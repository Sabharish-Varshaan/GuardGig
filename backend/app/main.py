from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import asyncio
import httpx
from datetime import datetime, timedelta

from .config import get_settings
from .routes.auth import router as auth_router
from .routes.onboarding import router as onboarding_router
from .routes.policy import router as policy_router
from .routes.premium import router as premium_router
from .routes.trigger import router as trigger_router
from .routes.claim import router as claim_router
from .routes.fraud import router as fraud_router
from .supabase_client import get_admin_client

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

        # Check weather
        try:
            rain = await get_weather_rain(city)
        except:
            continue

        # Determine trigger
        trigger = "none"
        if rain >= 100:
            trigger = "full"
        elif rain >= 60:
            trigger = "partial"

        if trigger == "none":
            continue

        # Check if claim already exists for today
        today = datetime.now().date()
        existing_claims = (
            admin.table("claims")
            .select("id")
            .eq("user_id", user_id)
            .gte("created_at", today.isoformat())
            .execute()
        )

        if existing_claims.data:
            continue  # Already has claim today

        # Calculate payout
        payout = 700.0 if trigger == "full" else 210.0

        # Get claim frequency (claims in last 30 days)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        claim_count = len(
            admin.table("claims")
            .select("id")
            .eq("user_id", user_id)
            .gte("created_at", thirty_days_ago)
            .execute()
            .data
        )

        # Create claim
        claim_data = {
            "user_id": user_id,
            "policy_id": policy["id"],
            "trigger_type": "rain",
            "trigger_value": rain,
            "payout_amount": payout,
            "status": "pending",
            "fraud_score": None
        }

        claim_response = admin.table("claims").insert(claim_data).execute()
        claim_id = claim_response.data[0]["id"]

        # Run fraud check
        fraud_score = calculate_fraud_score(city, "normal", claim_count)

        if fraud_score > 0.7:
            status = "rejected"
        else:
            status = "approved"

        # Update claim
        admin.table("claims").update({
            "fraud_score": fraud_score,
            "status": status
        }).eq("id", claim_id).execute()

async def get_weather_rain(location: str) -> float:
    """Fetch current rain amount from weather API."""
    url = f"https://wttr.in/{location}?format=j1"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        rain = float(data['current_condition'][0]['precipMM'])
        return rain

def calculate_fraud_score(gps: str, activity: str, claim_frequency: int) -> float:
    """Calculate fraud score."""
    score = 0.0
    score += min(0.5, claim_frequency / 20.0)
    if activity.lower() == "suspicious":
        score += 0.4
    if gps.lower() != "expected":
        score += 0.3
    return min(1.0, score)

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
