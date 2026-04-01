from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timezone

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
from .routes.trigger import router as trigger_router
from .routes.claim import router as claim_router
from .routes.fraud import router as fraud_router
from .supabase_client import get_admin_client
from .trigger_utils import evaluate_rain_trigger, fetch_aqi, fetch_rain_mm

settings = get_settings()

app = FastAPI(
    title="GuardGig API",
    version="0.1.0",
    description="Registration, login, and onboarding APIs for GuardGig"
)

scheduler = AsyncIOScheduler()

async def automated_claim_check():
    """Automated task to check triggers and create claims for all active policies."""
    settings = get_settings()
    admin = get_admin_client()

    # Get all active policies with user onboarding info
    policies_response = (
        admin.table(settings.supabase_policies_table)
        .select("*, onboarding_profiles(city)")
        .eq("status", "active")
        .execute()
    )

    for policy in policies_response.data:
        user_id = policy["user_id"]
        city = policy.get("onboarding_profiles", {}).get("city")

        if not city:
            continue

        try:
            rain = await fetch_rain_mm(city)
            _aqi = await fetch_aqi(city)
        except Exception:
            continue

        trigger = evaluate_rain_trigger(rain)

        if trigger == "none":
            continue

        try:
            enforce_waiting_period(policy, waiting_hours=24)
            enforce_max_one_claim_per_day(admin, settings.supabase_claims_table, user_id)
        except ValueError:
            continue

        coverage_amount = float(policy.get("coverage_amount", 700.0))
        payout = coverage_amount if trigger == "full" else round(coverage_amount * 0.30, 2)

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
            "trigger_type": "rain",
            "trigger_value": rain,
            "payout_amount": payout,
            "status": "approved",
            "fraud_score": fraud_score,
            "activity_status": "active",
            "location_valid": True,
            "rule_decision_reason": "approved_after_rule_checks",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        admin.table(settings.supabase_claims_table).insert(claim_data).execute()

@app.on_event("startup")
async def startup_event():
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
app.include_router(trigger_router)
app.include_router(claim_router)
app.include_router(fraud_router)
