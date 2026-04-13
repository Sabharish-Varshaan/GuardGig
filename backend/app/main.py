from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .claim_rules import (
    calculate_fraud_score,
    enforce_exclusions,
    enforce_max_one_claim_per_day,
    enforce_waiting_period,
    fetch_recent_claim_count,
)
from .config import get_settings
from .routes.auth import router as auth_router
from .routes.onboarding import router as onboarding_router
from .routes.policy import router as policy_router
from .routes.premium import router as premium_router
from .routes.payment import router as payment_router
from .routes.trigger import router as trigger_router
from .routes.claim import router as claim_router
from .routes.fraud import router as fraud_router
from .routes.ml_demo import router as ml_demo_router
from .services.payment_service import persist_claim_payment, simulate_razorpay_payout
from .supabase_client import get_admin_client
from .trigger_utils import check_trigger, fetch_aqi, fetch_rain_mm

settings = get_settings()
IST = ZoneInfo("Asia/Kolkata")

app = FastAPI(
    title="GuardGig API",
    version="0.1.0",
    description="Registration, login, and onboarding APIs for GuardGig"
)

payment_pages_dir = Path(__file__).resolve().parent / "payment_pages"
app.mount("/payment-pages", StaticFiles(directory=str(payment_pages_dir), html=True), name="payment-pages")

scheduler = AsyncIOScheduler()


def _verify_migration_007_applied() -> None:
    admin = get_admin_client()

    try:
        response = admin.rpc("guardgig_migration_007_applied").execute()
    except Exception as exc:
        raise RuntimeError("Migration 007 not applied. System cannot start.") from exc

    result = response.data
    if isinstance(result, list):
        is_applied = bool(result[0]) if result else False
    else:
        is_applied = bool(result)

    if not is_applied:
        raise RuntimeError("Migration 007 not applied. System cannot start.")


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)

async def automated_claim_check():
    """Automated task to check triggers and create claims for all active policies."""
    settings = get_settings()
    admin = get_admin_client()

    # Fetch active policies first, then explicitly fetch onboarding by user_id.
    policies_response = (
        admin.table(settings.supabase_policies_table)
        .select("*")
        .eq("status", "active")
        .execute()
    )

    for policy in (policies_response.data or []):
        user_id = policy["user_id"]

        # 1) Policy validity checks
        if str(policy.get("payment_status") or "pending").lower() != "success":
            continue

        expires_at = _parse_iso_datetime(policy.get("expires_at"))
        now_utc = datetime.now(timezone.utc)
        if expires_at is None or now_utc > expires_at:
            continue

        onboarding_response = (
            admin.table(settings.supabase_onboarding_table)
            .select("city,mean_income")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        onboarding_rows = onboarding_response.data or []
        onboarding = onboarding_rows[0] if onboarding_rows else {}
        city = onboarding.get("city")

        if not city:
            continue

        # 2) Fetch trigger data
        try:
            rain = await fetch_rain_mm(city)
            aqi = await fetch_aqi(city)
        except Exception:
            continue

        # 3) Trigger gate
        trigger_data = check_trigger(rain, aqi)

        if not trigger_data.get("triggered"):
            continue

        # 4) Daily claim limit
        try:
            enforce_max_one_claim_per_day(admin, settings.supabase_claims_table, user_id)
        except ValueError:
            continue

        trigger_type = trigger_data["trigger_type"]
        severity = trigger_data["severity"]
        payout_percentage_raw = trigger_data["payout_percentage"]

        try:
            enforce_waiting_period(policy, waiting_hours=24)
        except ValueError:
            continue

        coverage_amount = float(policy.get("coverage_amount", 700.0))
        mean_income = float(onboarding.get("mean_income") or 0)
        if mean_income <= 0:
            continue

        # Standardized payout formula: (payout_percentage / 100) * min(mean_income, coverage_amount)
        payout_base = min(mean_income, coverage_amount)
        payout = round((payout_percentage_raw / 100.0) * payout_base, 2)
        payout_percentage = payout_percentage_raw / 100.0
        
        rule_decision_reason = f"approved_after_{trigger_type}_{severity}_checks"
        trigger_snapshot = {
            "trigger_type": trigger_type,
            "severity": severity,
            "rain": rain,
            "aqi": aqi,
            "payout_percentage": payout_percentage,
            "payout_amount": payout,
            "fraud_score": None,
            "activity_status": "active",
            "location_valid": True,
            "rule_decision_reason": rule_decision_reason,
            "city": city,
        }

        claim_count = fetch_recent_claim_count(
            admin,
            settings.supabase_claims_table,
            user_id,
        )

        # 5) Fraud check
        fraud_score = calculate_fraud_score(
            activity_status="active",
            location_valid=True,
            claim_frequency=claim_count,
        )

        try:
            enforce_exclusions(
                activity_status="active",
                location_valid=True,
                fraud_score=fraud_score,
                fraud_threshold=settings.claim_fraud_threshold,
            )
        except ValueError:
            continue

        # 6) Payout is already computed above based on trigger severity and income.

        # 7) Create approved claim
        claim_data = {
            "user_id": user_id,
            "policy_id": policy["id"],
            "trigger_type": trigger_type,
            "trigger_value": rain if trigger_type == "rain" else aqi,
            "payout_amount": payout,
            "status": "approved",
            "fraud_score": fraud_score,
            "activity_status": "active",
            "location_valid": True,
            "rule_decision_reason": rule_decision_reason,
            "updated_at": datetime.now(IST).isoformat(),
        }

        try:
            claim_response = admin.table(settings.supabase_claims_table).insert(claim_data).execute()
        except Exception as exc:
            if "daily claim limit reached" in str(exc).lower():
                continue
            raise

        claim_rows = claim_response.data or []
        if not claim_rows:
            continue

        claim = claim_rows[0]

        # 8) Execute payout and persist payout fields
        try:
            payout_result = simulate_razorpay_payout(payout, user_id)
            payment_status = payout_result["status"]
            transaction_id = payout_result["transaction_id"]
            paid_at = payout_result["paid_at"]
        except Exception:
            payment_status = "failed"
            transaction_id = None
            paid_at = None

        persist_claim_payment(
            admin,
            settings.supabase_claims_table,
            claim["id"],
            payment_status,
            transaction_id,
            paid_at,
            "Razorpay",
            trigger_snapshot,
        )

@app.on_event("startup")
async def startup_event():
    _verify_migration_007_applied()

    # Add automated job to run every hour
    scheduler.add_job(
        automated_claim_check,
        trigger=IntervalTrigger(minutes=5),
        id="automated_claim_check",
        name="Automated Claim Check"
    )
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "environment": settings.app_env
    }


app.include_router(auth_router)
app.include_router(onboarding_router)
app.include_router(policy_router)
app.include_router(premium_router)
app.include_router(payment_router)
app.include_router(trigger_router)
app.include_router(claim_router)
app.include_router(fraud_router)
app.include_router(ml_demo_router)
