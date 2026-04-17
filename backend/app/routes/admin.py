"""
Admin endpoints for system metrics and risk oversight.
"""

import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status

from ..auth_utils import create_access_token, verify_password
from ..config import get_settings
from ..dependencies import require_admin_user
from ..metrics_utils import get_full_metrics
from ..schemas import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminMetricsResponse,
    AdminNextWeekRiskResponse,
    CityForecastDay,
    CityMLPrediction,
    CityRiskBreakdown,
    DayForecastSummary,
)
from ..supabase_client import get_admin_client
from ..trigger_utils import fetch_7day_forecast_async, compute_trigger_payouts
from ml.predict import get_next_week_risk_score

router = APIRouter(prefix="/api/admin", tags=["admin"])

logger = logging.getLogger(__name__)


def calculate_affected_ratio(max_payout_pct: int) -> float:
    """
    Calculate affected population ratio based on trigger severity.
    
    Higher severity triggers affect more workers (more cities affected, more infrastructure impacted).
    Lower severity triggers affect fewer (more localized impacts).
    """
    if max_payout_pct >= 100:
        return 0.7  # 70% affected - severe events hit widespread population
    elif max_payout_pct >= 60:
        return 0.5  # 50% affected - moderate severity
    elif max_payout_pct >= 30:
        return 0.3  # 30% affected - light severity
    else:
        return 0.1  # 10% affected - minimal impact


def determine_trigger_type(rain_pct: int, aqi_pct: int, heat_pct: int) -> str:
    if rain_pct == 0 and aqi_pct == 0 and heat_pct == 0:
        return "NONE"

    if rain_pct >= heat_pct and rain_pct >= aqi_pct and rain_pct > 0:
        return "RAIN"
    if heat_pct >= rain_pct and heat_pct >= aqi_pct and heat_pct > 0:
        return "HEAT"
    if aqi_pct > 0:
        return "AQI"
    return "NONE"


def risk_level_from_score(score: float) -> str:
    if score >= 0.6:
        return "HIGH"
    if score >= 0.3:
        return "MEDIUM"
    return "LOW"


def empty_next_week_risk_response() -> AdminNextWeekRiskResponse:
    now = datetime.now(timezone.utc).isoformat()
    return AdminNextWeekRiskResponse(
        risk_level="LOW",
        risk_score=0.0,
        ml_risk_score=0.0,
        ml_used=False,
        ml_explanation=[],
        trigger_risk=0,
        final_score=0.0,
        total_expected_claims=0,
        projected_payout=0.0,
        high_risk_cities=[],
        city_predictions=[],
        max_payout_tier=0,
        days_with_triggers=0,
        city_breakdown=[],
        forecast_summary=[],
        last_updated=now,
    )


def build_default_forecast() -> list[dict]:
    return [
        {
            "date": (datetime.now(timezone.utc) + timedelta(days=i)).isoformat().split("T")[0],
            "rain": 0.0,
            "temperature": 20.0,
        }
        for i in range(7)
    ]


def _normalize_ml_result(result) -> tuple[float, bool, list[str]]:
    if isinstance(result, dict):
        return (
            float(result.get("risk_score", 0.0) or 0.0),
            bool(result.get("ml_used", False)),
            list(result.get("explanation", []) or []),
        )

    if isinstance(result, tuple):
        score = float(result[0] if len(result) > 0 else 0.0)
        used_model = bool(result[1] if len(result) > 1 else False)
        return score, used_model, []

    return 0.0, False, []


@router.post("/login", response_model=AdminLoginResponse)
def login(payload: AdminLoginRequest):
    settings = get_settings()
    admin = get_admin_client()

    result = (
        admin.table(settings.supabase_users_table)
        .select("id,full_name,email,phone,password_hash,role")
        .eq("email", payload.email)
        .limit(1)
        .execute()
    )

    rows = result.data or []
    if not rows:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials")

    user = rows[0]
    if user.get("role", "user") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials")

    access_token = create_access_token(
        user_id=user["id"],
        phone=user.get("phone", ""),
        role="admin",
        email=user.get("email")
    )

    return AdminLoginResponse(access_token=access_token, role="admin")


@router.get("/metrics", response_model=AdminMetricsResponse)
def get_metrics(current_admin: dict = Depends(require_admin_user)):
    """
    Fetch system metrics: total premiums, payouts, and loss ratio.
    Used for admin dashboard and risk control oversight.
    """
    admin = get_admin_client()
    metrics = get_full_metrics(admin)
    print("Metrics API response:", metrics)
    
    return AdminMetricsResponse(
        total_premium=metrics["total_premium"],
        total_payout=metrics["total_payout"],
        loss_ratio=metrics["loss_ratio"],
        loss_ratio_percentage=round(metrics["loss_ratio"] * 100, 2),
        status=str(metrics.get("status") or "SAFE"),
        last_updated=metrics["last_updated"],
    )


@router.get("/next-week-risk", response_model=AdminNextWeekRiskResponse)
async def get_next_week_risk(current_admin: dict = Depends(require_admin_user)):
    """
    Forecast next week's disruption risk across all worker cities.
    Aggregates active policies by city, fetches weather forecasts,
    simulates trigger payouts, and projects claims and payouts.
    """
    settings = get_settings()
    admin = get_admin_client()
    
    # 1. Fetch all active, paid policies with onboarding data
    policies_response = (
        admin.table(settings.supabase_policies_table)
        .select("id,user_id,status,payment_status,coverage_amount,created_at")
        .eq("status", "active")
        .eq("payment_status", "success")
        .execute()
    )
    
    policies = policies_response.data or []
    if not policies:
        return empty_next_week_risk_response()
    
    # 2. Fetch onboarding data for all users
    user_ids = list(set(p["user_id"] for p in policies))
    onboarding_response = (
        admin.table(settings.supabase_onboarding_table)
        .select("user_id,city,mean_income")
        .in_("user_id", user_ids)
        .execute()
    )
    
    onboarding_by_user = {o["user_id"]: o for o in (onboarding_response.data or [])}
    
    # 3. Group policies by city
    city_groups = {}
    for policy in policies:
        user_id = policy["user_id"]
        onboarding = onboarding_by_user.get(user_id)
        if not onboarding or not onboarding.get("city"):
            continue
        
        city = onboarding["city"]
        if city not in city_groups:
            city_groups[city] = []
        
        city_groups[city].append({
            "policy": policy,
            "onboarding": onboarding,
        })
    
    if not city_groups:
        return empty_next_week_risk_response()
    
    # 4. Fetch 7-day forecast for each city and compute risk
    city_results = {}
    all_days_results = {}  # Track all days across all cities
    any_city_used_model = False
    city_explanations = {}
    
    for city, policy_records in city_groups.items():
        forecast = await fetch_7day_forecast_async(city)
        if not forecast:
            forecast = build_default_forecast()
        
        # Compute max payout and triggers for this city
        max_payout_pct = 0
        expected_triggers_set = set()
        city_forecast_days = []
        temperatures = []
        rain_values = []
        payout_percentages = []
        
        for day_data in forecast[:7]:
            rain = day_data.get("rain", 0.0)
            temp = day_data.get("temperature", 20.0)
            aqi = 0.0  # AQI not available from 7-day forecast
            
            rain_pct, aqi_pct, heat_pct = compute_trigger_payouts(rain, aqi, temp)
            day_max_pct = max(rain_pct, aqi_pct, heat_pct)
            trigger_type = determine_trigger_type(rain_pct, aqi_pct, heat_pct)
            
            if day_max_pct > max_payout_pct:
                max_payout_pct = day_max_pct
            
            # Track triggers
            if rain_pct > 0:
                expected_triggers_set.add("RAIN")
            if heat_pct > 0:
                expected_triggers_set.add("HEAT")
            if aqi_pct > 0:
                expected_triggers_set.add("AQI")

            temperatures.append(float(temp))
            rain_values.append(float(rain))
            payout_percentages.append(float(day_max_pct))

            city_forecast_days.append(
                CityForecastDay(
                    date=day_data.get("date", ""),
                    temperature=float(temp),
                    rain=float(rain),
                    trigger_type=trigger_type,
                    payout_percentage=day_max_pct,
                )
            )
            
            # Store day result keyed by date
            date_str = day_data.get("date", "")
            if date_str not in all_days_results:
                all_days_results[date_str] = {
                    "rain": float(rain),
                    "temperature": float(temp),
                    "payout_pct": day_max_pct,
                    "triggers": set(),
                }
            
            # Update max across all cities for this date
            if day_max_pct > all_days_results[date_str]["payout_pct"]:
                all_days_results[date_str]["payout_pct"] = day_max_pct
            if float(rain) > all_days_results[date_str]["rain"]:
                all_days_results[date_str]["rain"] = float(rain)
            if float(temp) > all_days_results[date_str]["temperature"]:
                all_days_results[date_str]["temperature"] = float(temp)

            day_triggers = set()
            if rain_pct > 0:
                day_triggers.add("RAIN")
            if heat_pct > 0:
                day_triggers.add("HEAT")
            if aqi_pct > 0:
                day_triggers.add("AQI")
            all_days_results[date_str]["triggers"].update(day_triggers)
        
        # Compute city-level aggregates
        num_policies = len(policy_records)
        num_users = len(set(p["onboarding"]["user_id"] for p in policy_records))
        
        coverages = [float(p["policy"].get("coverage_amount", 700.0)) for p in policy_records]
        avg_coverage = sum(coverages) / len(coverages) if coverages else 700.0
        
        # Calculate affected_ratio based on trigger severity
        affected_ratio = calculate_affected_ratio(max_payout_pct)
        
        # Updated claim estimation: includes affected_ratio factor
        expected_claims = int(round(num_users * affected_ratio * (max_payout_pct / 100.0)))
        
        # Updated payout: accounts for payout_pct reduction
        projected_payout = expected_claims * avg_coverage * (max_payout_pct / 100.0)
        
        city_trigger_days = sum(1 for pct in payout_percentages if pct > 0)
        avg_temperature = sum(temperatures) / len(temperatures) if temperatures else 20.0
        max_temperature = max(temperatures) if temperatures else 20.0
        total_rainfall = sum(rain_values)
        max_rainfall = max(rain_values) if rain_values else 0.0
        avg_payout_pct = sum(payout_percentages) / len(payout_percentages) if payout_percentages else 0.0

        ml_input = {
            "avg_temperature": avg_temperature,
            "max_temperature": max_temperature,
            "total_rainfall": total_rainfall,
            "max_rainfall": max_rainfall,
            "trigger_days": city_trigger_days,
            "avg_payout_percentage": avg_payout_pct,
        }
        logger.info("[ML INPUT] city=%s features=%s", city, ml_input)

        ml_result = get_next_week_risk_score(forecast)
        ml_score, used_model, explanation = _normalize_ml_result(ml_result)
        trigger_risk_score = max_payout_pct / 100.0

        if not used_model:
            # Safety fallback to trigger-only risk when ML is unavailable.
            ml_score = trigger_risk_score
            city_final_score = trigger_risk_score
            logger.warning("[ML OUTPUT] city=%s model_unavailable=True fallback=trigger_based", city)
        else:
            any_city_used_model = True
            city_final_score = (0.85 * ml_score) + (0.15 * trigger_risk_score)

        city_final_score = min(max(city_final_score, 0.0), 1.0)
        ml_score = min(max(float(ml_score), 0.0), 1.0)
        city_risk_level = risk_level_from_score(city_final_score)
        city_explanations[city] = explanation

        logger.info(
            "[ML OUTPUT] city=%s ml_score=%.3f used_model=%s",
            city,
            ml_score,
            used_model,
        )
        logger.info(
            "[FINAL SCORE] city=%s trigger_risk=%.3f final_score=%.3f",
            city,
            trigger_risk_score,
            city_final_score,
        )
        
        # Detailed logging
        logger.info(
            f"City risk analysis: {city} | users={num_users} | affected_ratio={affected_ratio:.2f} | "
            f"max_payout={max_payout_pct}% | expected_claims={expected_claims} | "
            f"projected_payout={projected_payout:.2f} | trigger_days={city_trigger_days} | "
            f"avg_temp={avg_temperature:.1f}°C | ml_score={ml_score:.3f} | "
            f"final_score={city_final_score:.3f} | risk_level={city_risk_level}"
        )
        
        city_results[city] = {
            "num_policies": num_policies,
            "num_users": num_users,
            "max_payout_pct": max_payout_pct,
            "affected_ratio": affected_ratio,
            "expected_claims": expected_claims,
            "avg_coverage": avg_coverage,
            "projected_payout": projected_payout,
            "risk_level": city_risk_level,
            "risk_score": city_final_score,
            "ml_score": ml_score,
            "final_score": city_final_score,
            "trigger_days": city_trigger_days,
            "avg_temp": avg_temperature,
            "expected_triggers": sorted(list(expected_triggers_set)),
            "forecast_days": city_forecast_days,
        }
    
    # 5. Aggregate system-wide results
    total_expected_claims = sum(r["expected_claims"] for r in city_results.values())
    total_projected_payout = sum(r["projected_payout"] for r in city_results.values())
    max_payout_tier = max((r["max_payout_pct"] for r in city_results.values()), default=0)
    
    # Calculate system-wide aggregate values
    num_trigger_days = sum(1 for d in all_days_results.values() if d["payout_pct"] > 0)

    total_users_weight = sum(max(1, r["num_users"]) for r in city_results.values())
    weighted_ml_score = sum(r["ml_score"] * max(1, r["num_users"]) for r in city_results.values())
    ml_risk_score = (weighted_ml_score / total_users_weight) if total_users_weight else 0.0
    trigger_risk_score = max_payout_tier / 100.0
    if any_city_used_model:
        system_final_score = (0.85 * ml_risk_score) + (0.15 * trigger_risk_score)
    else:
        ml_risk_score = trigger_risk_score
        system_final_score = trigger_risk_score

    system_final_score = min(max(system_final_score, 0.0), 1.0)
    overall_risk_level = risk_level_from_score(system_final_score)
    
    # System-wide logging
    total_num_users = sum(r["num_users"] for r in city_results.values())
    logger.info(
        f"System-wide risk summary | total_users={total_num_users} | "
        f"trigger_days={num_trigger_days} | "
        f"max_payout={max_payout_tier}% | total_expected_claims={total_expected_claims} | "
        f"total_projected_payout={total_projected_payout:.2f} | "
        f"ml_risk_score={ml_risk_score:.3f} | final_score={system_final_score:.3f} | "
        f"risk_level={overall_risk_level}"
    )

    logger.info("[FINAL SCORE] system trigger_risk=%.3f final_score=%.3f", trigger_risk_score, system_final_score)
    
    # High risk cities
    ordered_cities = sorted(city_results.items(), key=lambda item: item[1]["final_score"], reverse=True)
    high_risk_cities = [c for c, r in ordered_cities if r["risk_level"] == "HIGH"]

    ml_explanation: list[str] = []
    for city, _ in ordered_cities[:3]:
        for reason in city_explanations.get(city, []):
            if reason not in ml_explanation:
                ml_explanation.append(reason)

    if not ml_explanation and ordered_cities:
        ml_explanation = city_explanations.get(ordered_cities[0][0], [])

    city_predictions = [
        CityMLPrediction(
            city=city,
            ml_score=round(r["ml_score"], 4),
            trigger_score=r["max_payout_pct"],
            trigger_pct=r["max_payout_pct"],
            final_score=round(r["final_score"], 4),
            risk_level=r["risk_level"],
        )
        for city, r in ordered_cities
    ]
    
    # Build city breakdown
    city_breakdown = [
        CityRiskBreakdown(
            city=city,
            num_policies=r["num_policies"],
            num_users=r["num_users"],
            max_payout_pct=r["max_payout_pct"],
            affected_ratio=r["affected_ratio"],
            expected_claims=r["expected_claims"],
            avg_coverage_amount=r["avg_coverage"],
            projected_payout=r["projected_payout"],
            risk_level=r["risk_level"],
            risk_score=r["risk_score"],
            expected_triggers=r["expected_triggers"],
            forecast_days=r["forecast_days"],
        )
        for city, r in city_results.items()
    ]
    
    # Build forecast summary
    forecast_summary = []
    for i, (date_str, day_result) in enumerate(sorted(all_days_results.items())):
        if date_str:
            day_of_week = datetime.fromisoformat(date_str).strftime("%a")
        else:
            day_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][i % 7]
        forecast_summary.append(
            DayForecastSummary(
                day=day_of_week,
                date=date_str,
                rain=day_result["rain"],
                temperature=day_result["temperature"],
                payout_pct=day_result["payout_pct"],
                triggers=sorted(day_result["triggers"]),
            )
        )
    
    return AdminNextWeekRiskResponse(
        risk_level=overall_risk_level,
        risk_score=round(system_final_score, 4),
        ml_risk_score=round(ml_risk_score, 4),
        ml_used=any_city_used_model,
        ml_explanation=ml_explanation,
        trigger_risk=max_payout_tier,
        final_score=round(system_final_score, 4),
        total_expected_claims=total_expected_claims,
        projected_payout=round(total_projected_payout, 2),
        high_risk_cities=high_risk_cities,
        city_predictions=city_predictions,
        max_payout_tier=max_payout_tier,
        days_with_triggers=num_trigger_days,
        city_breakdown=city_breakdown,
        forecast_summary=forecast_summary,
        last_updated=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/predictions")
def get_predictions(current_admin: dict = Depends(require_admin_user)):
    admin = get_admin_client()
    metrics = get_full_metrics(admin)

    total_premium = metrics["total_premium"]
    total_payout = metrics["total_payout"]
    loss_ratio = metrics["loss_ratio"]

    risk_score = (loss_ratio * 5) + (total_payout / (total_premium + 1))

    if risk_score > 5:
        risk = "HIGH"
    elif risk_score > 2:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    if loss_ratio > 0.85:
        disruption = "High claim payouts may affect system stability"
    elif loss_ratio > 0.7:
        disruption = "Moderate financial risk, monitor closely"
    else:
        disruption = "System stable, no major disruption expected"

    return {
        "next_week_risk": risk,
        "risk_score": round(risk_score, 2),
        "expected_disruption": disruption,
        "last_updated": metrics["last_updated"],
    }
