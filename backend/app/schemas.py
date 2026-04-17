from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

from .payout_utils import is_valid_ifsc, is_valid_upi

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


class AdminLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=6, max_length=72)


class AdminLoginResponse(BaseModel):
    access_token: str
    role: Literal["admin"]


class OnboardingRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(min_length=2, max_length=80)
    age: int = Field(ge=18, le=70)
    city: str = Field(min_length=2, max_length=80)
    platform: str = Field(min_length=2, max_length=80)
    vehicle_type: Literal["Bike", "Scooter", "Cycle"]
    work_hours: int = Field(gt=0, le=24)
    min_income: float = Field(gt=0)
    max_income: float = Field(gt=0)
    risk_preference: Literal["Low", "Medium", "High"]

    @field_validator("max_income")
    @classmethod
    def validate_income_range(cls, value: float, info: ValidationInfo) -> float:
        min_income = info.data.get("min_income")
        if min_income is not None and value <= min_income:
            raise ValueError("max_income must be greater than min_income")
        return value


class OnboardingResponse(BaseModel):
    onboarding_completed: bool
    profile: dict


class PolicyResponse(BaseModel):
    id: str
    user_id: str
    weekly_income: int
    min_income: Optional[float] = None
    max_income: Optional[float] = None
    mean_income: Optional[float] = None
    income_variance: Optional[float] = None
    risk_score: Optional[float] = Field(None, ge=0, le=1)
    premium: float
    coverage_amount: float
    payment_status: Optional[str] = "pending"
    payment_id: Optional[str] = None
    activated_at: Optional[str] = None
    expires_at: Optional[str] = None
    end_date: Optional[str] = None
    policy_start_date: str
    status: Literal["active", "inactive"]
    is_active: Optional[bool] = None
    eligibility_status: str = "eligible"
    worker_tier: str = "medium"
    created_at: str
    updated_at: str


class PolicyCreateResponse(BaseModel):
    status: Literal["created", "ineligible"]
    policy: PolicyResponse | None = None
    message: str


class DemoModeToggleRequest(BaseModel):
    enabled: bool


class DemoModeToggleResponse(BaseModel):
    demo_mode_enabled: bool
    updated_at: str | None = None
    message: str


class PayoutDetailsCreateRequest(BaseModel):
    account_holder_name: str = Field(min_length=2, max_length=120)
    bank_account_number: str | None = Field(default=None, min_length=6, max_length=30)
    ifsc_code: str | None = Field(default=None, min_length=11, max_length=11)
    upi_id: str | None = Field(default=None, min_length=3, max_length=100)

    @field_validator("account_holder_name")
    @classmethod
    def normalize_holder_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("bank_account_number")
    @classmethod
    def normalize_bank_account(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().replace(" ", "")
        return normalized or None

    @field_validator("ifsc_code")
    @classmethod
    def normalize_ifsc(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        return normalized or None

    @field_validator("upi_id")
    @classmethod
    def normalize_upi(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        return normalized or None

    @model_validator(mode="after")
    def validate_payout_inputs(self):
        has_bank = bool(self.bank_account_number)
        has_ifsc = bool(self.ifsc_code)
        has_upi = bool(self.upi_id)

        if not has_upi and not (has_bank and has_ifsc):
            raise ValueError("Provide either bank account + IFSC or UPI ID")

        if has_bank != has_ifsc:
            raise ValueError("Bank account number and IFSC must be provided together")

        if has_ifsc and not is_valid_ifsc(self.ifsc_code):
            raise ValueError("Invalid IFSC code format")

        if has_upi and not is_valid_upi(self.upi_id):
            raise ValueError("Invalid UPI ID format")

        return self


class PayoutDetailsResponse(BaseModel):
    account_holder_name: str
    bank_account_number_masked: str | None = None
    ifsc_code: str | None = None
    upi_id: str | None = None
    created_at: str | None = None
    message: str


class PremiumCalculateRequest(BaseModel):
    income: float = Field(gt=0)
    income_variance: Optional[float] = 0
    risk_preference: Literal["Low", "Medium", "High"] = "Medium"
    city: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    forecast_data: Optional[list[dict]] = None


class PremiumCalculateResponse(BaseModel):
    premium: float
    coverage: float
    coverage_percentage: float
    mode: str
    target: str
    reason: str


class PaymentOrderCreateRequest(BaseModel):
    token: Optional[str] = None


class PaymentOrderResponse(BaseModel):
    order_id: str
    amount: int
    currency: str
    premium: float
    key_id: str


class PaymentVerifyRequest(BaseModel):
    order_id: str
    payment_id: str
    signature: str


class PaymentVerifyResponse(BaseModel):
    payment_status: Literal["success"]
    payment_id: str
    activated_at: str
    expires_at: str
    order_id: str


class ClaimCreateRequest(BaseModel):
    lat: Optional[float] = None
    lon: Optional[float] = None
    activity_status: Literal["active", "inactive", "none", "unknown", "suspicious"] = "unknown"


class ClaimResponse(BaseModel):
    id: str
    user_id: str
    policy_id: str
    trigger_type: str
    trigger_value: float
    trigger_reason: Optional[str] = None
    payout_percentage: Optional[int] = None
    payout_amount: float
    status: Literal["pending", "approved", "rejected"]
    fraud_score: Optional[float] = Field(None, ge=0, le=1)
    risk_score: Optional[float] = Field(None, ge=0, le=1)
    payout_status: Optional[str] = None
    payment_status: Optional[str] = None
    order_id: Optional[str] = None
    payment_id: Optional[str] = None
    payment_signature: Optional[str] = None
    transaction_id: Optional[str] = None
    paid_at: Optional[str] = None
    payout_method: Optional[str] = None
    masked_account: Optional[str] = None
    trigger_snapshot: Optional[dict] = None
    rule_decision_reason: Optional[str] = None
    created_at: str
    updated_at: str

    @field_validator("trigger_type")
    @classmethod
    def normalize_trigger_type_value(cls, value: str) -> str:
        normalized = str(value or "").strip().upper()
        if normalized in {"RAIN", "AQI", "HEAT"}:
            return normalized
        return normalized


class ClaimCreateResponse(BaseModel):
    claim: ClaimResponse
    message: str
    notification: Optional["NotificationResponse"] = None


class ClaimRejectedResponse(BaseModel):
    status: Literal["rejected"]
    reason: str


class ClaimsListResponse(BaseModel):
    claims: list[ClaimResponse]


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    notification_type: str
    claim_id: Optional[str] = None
    metadata: Optional[dict] = None
    read_status: bool = False
    created_at: str


class NotificationsListResponse(BaseModel):
    notifications: list[NotificationResponse]


class NotificationMarkReadResponse(BaseModel):
    notification: NotificationResponse
    message: str


class FraudCheckRequest(BaseModel):
    claim_id: str
    gps: str  # e.g., "latitude,longitude" or location string
    activity: str  # e.g., "normal", "suspicious"
    claim_frequency: int = Field(ge=0)  # number of claims in period
    location_change_km: Optional[float] = Field(default=None, ge=0)
    reported_rain_mm: Optional[float] = Field(default=None, ge=0)
    actual_rain_mm: Optional[float] = Field(default=None, ge=0)
    time_since_last_claim_hours: Optional[float] = Field(default=None, ge=0)
    weather_mismatch: Optional[bool] = False


class FraudCheckResponse(BaseModel):
    fraud_score: float
    decision: str  # "approved" or "rejected"
    message: str


class AdminMetricsResponse(BaseModel):
    total_premium: float
    total_payout: float
    loss_ratio: float
    loss_ratio_percentage: float  # For UI: loss_ratio * 100
    status: str  # "healthy", "warning", "critical"
    last_updated: str


class DayForecastSummary(BaseModel):
    day: str  # e.g., "Mon", "Tue"
    date: str  # e.g., "2026-04-20"
    rain: float  # mm
    temperature: float  # °C
    payout_pct: int  # 0, 30, 60, or 100
    triggers: list[str]  # ["RAIN"], ["HEAT"], ["RAIN", "HEAT"], etc.


class CityForecastDay(BaseModel):
    date: str
    temperature: float
    rain: float
    trigger_type: Literal["RAIN", "HEAT", "AQI", "NONE"]
    payout_percentage: int  # 0, 30, 60, or 100


class CityRiskBreakdown(BaseModel):
    city: str
    num_policies: int
    num_users: int
    max_payout_pct: int  # highest payout percentage across 7 days
    affected_ratio: float  # dynamic based on max_payout_pct: 0.7 (>=100%), 0.5 (>=60%), 0.3 (>=30%), 0.1 (<30%)
    expected_claims: int  # num_users * affected_ratio * (max_payout_pct / 100)
    avg_coverage_amount: float
    projected_payout: float  # expected_claims * avg_coverage_amount * (max_payout_pct / 100)
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    risk_score: float  # 0.0 to 1.0, multi-factor: 0.5*severity + 0.3*frequency + 0.2*temperature
    expected_triggers: list[str]
    forecast_days: list[CityForecastDay]


class CityMLPrediction(BaseModel):
    city: str
    ml_score: float  # raw ML score in [0, 1]
    trigger_score: int  # trigger-derived max payout percentage (0-100)
    trigger_pct: int  # legacy alias kept for backward compatibility
    final_score: float  # blended score in [0, 1]
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]


class AdminNextWeekRiskResponse(BaseModel):
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    risk_score: float  # 0.0 to 1.0, lightweight ML-style aggregate
    ml_risk_score: float  # system-wide ML score in [0, 1]
    ml_used: bool
    ml_explanation: list[str]
    trigger_risk: int  # trigger-derived system risk as percentage (0-100)
    final_score: float  # blended system score in [0, 1]
    total_expected_claims: int
    projected_payout: float
    high_risk_cities: list[str]  # list of city names with HIGH risk
    city_predictions: list[CityMLPrediction]
    max_payout_tier: int  # highest payout_pct across all cities and days
    days_with_triggers: int  # count of days with at least one trigger
    city_breakdown: list[CityRiskBreakdown]
    forecast_summary: list[DayForecastSummary]
    last_updated: str
