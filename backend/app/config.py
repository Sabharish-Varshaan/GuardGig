import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

# Risk control thresholds
LOSS_RATIO_THRESHOLD = 0.85  # 85% - system stops accepting new policies above this
LOSS_RATIO_MIN_PREMIUM_FOR_ENFORCEMENT = 500.0  # Avoid blocking at tiny sample sizes in early-stage/dev data


class Settings(BaseModel):
    app_env: str = Field(default="development")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    demo_mode: bool = Field(default=False)
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:8081"])
    supabase_url: str = Field(default="")
    supabase_anon_key: str = Field(default="")
    supabase_service_role_key: str = Field(default="")
    supabase_onboarding_table: str = Field(default="onboarding_profiles")
    supabase_users_table: str = Field(default="app_users")
    supabase_policies_table: str = Field(default="policies")
    supabase_claims_table: str = Field(default="claims")
    supabase_notifications_table: str = Field(default="notifications")
    supabase_payout_details_table: str = Field(default="user_payout_details")
    jwt_secret: str = Field(default="change-me")
    jwt_algorithm: str = Field(default="HS256")
    access_token_exp_minutes: int = Field(default=60)
    refresh_token_exp_days: int = Field(default=7)
    claim_fraud_threshold: float = Field(default=0.7)
    razorpay_key_id: str = Field(default="")
    razorpay_key_secret: str = Field(default="")
    razorpay_currency: str = Field(default="INR")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    origins_value = os.getenv("CORS_ORIGINS", "http://localhost:8081")
    origins = [item.strip() for item in origins_value.split(",") if item.strip()]
    demo_mode_value = os.getenv("APP_DEMO_MODE", os.getenv("DEMO_MODE", "false"))

    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        demo_mode=demo_mode_value.lower() == "true",
        cors_origins=origins,
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_anon_key=os.getenv("SUPABASE_ANON_KEY", ""),
        supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
        supabase_onboarding_table=os.getenv("SUPABASE_ONBOARDING_TABLE", "onboarding_profiles"),
        supabase_users_table=os.getenv("SUPABASE_USERS_TABLE", "app_users"),
        supabase_policies_table=os.getenv("SUPABASE_POLICIES_TABLE", "policies"),
        supabase_claims_table=os.getenv("SUPABASE_CLAIMS_TABLE", "claims"),
        supabase_notifications_table=os.getenv("SUPABASE_NOTIFICATIONS_TABLE", "notifications"),
        supabase_payout_details_table=os.getenv("SUPABASE_PAYOUT_DETAILS_TABLE", "user_payout_details"),
        jwt_secret=os.getenv("JWT_SECRET", "change-me"),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        access_token_exp_minutes=int(os.getenv("ACCESS_TOKEN_EXP_MINUTES", "60")),
        refresh_token_exp_days=int(os.getenv("REFRESH_TOKEN_EXP_DAYS", "7")),
        claim_fraud_threshold=float(os.getenv("CLAIM_FRAUD_THRESHOLD", "0.7")),
        razorpay_key_id=os.getenv("RAZORPAY_KEY_ID", ""),
        razorpay_key_secret=os.getenv("RAZORPAY_KEY_SECRET", ""),
        razorpay_currency=os.getenv("RAZORPAY_CURRENCY", "INR"),
    )
