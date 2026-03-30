from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

PHONE_PATTERN = r"^[0-9]{10}$"


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=80)
    phone: str = Field(pattern=PHONE_PATTERN)
    password: str = Field(min_length=6, max_length=72)

    @field_validator("full_name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()


class LoginRequest(BaseModel):
    phone: str = Field(pattern=PHONE_PATTERN)
    password: str = Field(min_length=6, max_length=72)


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: str
    onboarding_completed: bool


class OnboardingRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(min_length=2, max_length=80)
    age: int = Field(ge=18, le=70)
    city: str = Field(min_length=2, max_length=80)
    platform: str = Field(min_length=2, max_length=80)
    vehicle_type: Literal["Bike", "Scooter", "Cycle"]
    work_hours: int = Field(gt=0, le=24)
    daily_income: int = Field(gt=0)
    weekly_income: int = Field(gt=0)
    risk_preference: Literal["Low", "Medium", "High"]


class OnboardingResponse(BaseModel):
    onboarding_completed: bool
    profile: dict
