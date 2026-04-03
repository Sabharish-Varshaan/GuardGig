from typing import Literal, Optional

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


class PolicyResponse(BaseModel):
    id: str
    user_id: str
    weekly_income: int
    premium: float
    coverage_amount: float
    policy_start_date: str
    status: Literal["active", "inactive"]
    eligibility_status: str = "eligible"
    worker_tier: str = "medium"
    created_at: str
    updated_at: str


class PolicyCreateResponse(BaseModel):
    status: Literal["created", "ineligible"]
    policy: PolicyResponse | None = None
    message: str


class PremiumCalculateRequest(BaseModel):
    income: float = Field(gt=0)
    risk_preference: Literal["Low", "Medium", "High"] = "Medium"


class PremiumCalculateResponse(BaseModel):
    premium: float


class ClaimCreateRequest(BaseModel):
    location: str | None = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    activity_status: Literal["active", "inactive", "none"] = "active"
    location_valid: bool = True
    trigger_type: Optional[str] = None
    severity: Optional[str] = None


class ClaimResponse(BaseModel):
    id: str
    user_id: str
    policy_id: str
    trigger_type: str
    trigger_value: float
    payout_amount: float
    status: Literal["pending", "approved", "rejected"]
    fraud_score: Optional[float]
    created_at: str
    updated_at: str


class ClaimCreateResponse(BaseModel):
    claim: ClaimResponse
    message: str


class ClaimsListResponse(BaseModel):
    claims: list[ClaimResponse]


class FraudCheckRequest(BaseModel):
    claim_id: str
    gps: str  # e.g., "latitude,longitude" or location string
    activity: str  # e.g., "normal", "suspicious"
    claim_frequency: int = Field(ge=0)  # number of claims in period


class FraudCheckResponse(BaseModel):
    fraud_score: float
    decision: str  # "approved" or "rejected"
    message: str
