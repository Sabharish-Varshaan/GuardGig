import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class Settings(BaseModel):
    app_env: str = Field(default="development")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:8081"])
    supabase_url: str = Field(default="")
    supabase_anon_key: str = Field(default="")
    supabase_service_role_key: str = Field(default="")
    supabase_onboarding_table: str = Field(default="onboarding_profiles")
    supabase_users_table: str = Field(default="app_users")
    jwt_secret: str = Field(default="change-me")
    jwt_algorithm: str = Field(default="HS256")
    access_token_exp_minutes: int = Field(default=60)
    refresh_token_exp_days: int = Field(default=7)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    origins_value = os.getenv("CORS_ORIGINS", "http://localhost:8081")
    origins = [item.strip() for item in origins_value.split(",") if item.strip()]

    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        cors_origins=origins,
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_anon_key=os.getenv("SUPABASE_ANON_KEY", ""),
        supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
        supabase_onboarding_table=os.getenv("SUPABASE_ONBOARDING_TABLE", "onboarding_profiles"),
        supabase_users_table=os.getenv("SUPABASE_USERS_TABLE", "app_users"),
        jwt_secret=os.getenv("JWT_SECRET", "change-me"),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        access_token_exp_minutes=int(os.getenv("ACCESS_TOKEN_EXP_MINUTES", "60")),
        refresh_token_exp_days=int(os.getenv("REFRESH_TOKEN_EXP_DAYS", "7"))
    )
