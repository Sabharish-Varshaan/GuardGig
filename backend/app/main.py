from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
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

        # Skip all downstream work for users who already have today's claim.
        try:
            enforce_max_one_claim_per_day(admin, settings.supabase_claims_table, user_id)
        except ValueError:
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

        try:
            rain = await fetch_rain_mm(city)
            aqi = await fetch_aqi(city)
        except Exception:
            continue

        trigger_data = check_trigger(rain, aqi)

        if not trigger_data.get("trigger"):
            continue

        if str(policy.get("payment_status") or "pending").lower() != "success":
            continue

        trigger_type = trigger_data["type"]
        severity = trigger_data["severity"]

        try:
            enforce_waiting_period(policy, waiting_hours=24)
        except ValueError:
            continue

        coverage_amount = float(policy.get("coverage_amount", 700.0))
        mean_income = float(onboarding.get("mean_income") or 0)
        payout_base = min(mean_income, coverage_amount)
        if severity == "full":
            payout = payout_base
        elif severity == "severe":
            payout = payout_base * 0.70
        elif severity == "partial":
            payout = payout_base * 0.30
        else:
            payout = 0.0
        payout = round(min(payout, coverage_amount), 2)
        rule_decision_reason = f"approved_after_{trigger_type}_{severity}_checks"
        trigger_snapshot = {
            "trigger_type": trigger_type,
            "severity": severity,
            "rain": rain,
            "aqi": aqi,
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
        trigger=IntervalTrigger(hours=1),
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
