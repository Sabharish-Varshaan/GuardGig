from datetime import datetime, timezone
from math import radians, sin, cos, sqrt, atan2

from fastapi import APIRouter, Depends, HTTPException, status

from ..claim_rules import calculate_fraud_score
from ..config import get_settings
from ..dependencies import require_current_user
from ..schemas import FraudCheckRequest, FraudCheckResponse
from ..supabase_client import get_admin_client

router = APIRouter(prefix="/api/fraud", tags=["fraud"])


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return r * c


def _parse_gps_pair(raw_value: str | None) -> tuple[float, float] | None:
    value = str(raw_value or "").strip()
    if not value or "," not in value:
        return None

    lat_text, lon_text = value.split(",", 1)
    try:
        return float(lat_text.strip()), float(lon_text.strip())
    except (TypeError, ValueError):
        return None

@router.post("/check", response_model=FraudCheckResponse)
def check_fraud(request: FraudCheckRequest, current_user: dict = Depends(require_current_user)):
    settings = get_settings()
    admin = get_admin_client()

    # Verify claim belongs to user
    claim_response = (
        admin.table(settings.supabase_claims_table)
        .select("*")
        .eq("id", request.claim_id)
        .eq("user_id", current_user["id"])
        .limit(1)
        .execute()
    )

    if not claim_response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    claim = claim_response.data[0]

    # Calculate fraud score from location distance where coordinates are available.
    reasons: list[str] = []
    parsed_gps = _parse_gps_pair(request.gps)
    user_lat = request.user_lat if request.user_lat is not None else (parsed_gps[0] if parsed_gps else None)
    user_lon = request.user_lon if request.user_lon is not None else (parsed_gps[1] if parsed_gps else None)
    weather_lat = request.weather_lat
    weather_lon = request.weather_lon

    distance_km = request.location_change_km
    if (
        distance_km is None
        and user_lat is not None
        and user_lon is not None
        and weather_lat is not None
        and weather_lon is not None
    ):
        distance_km = haversine(float(user_lat), float(user_lon), float(weather_lat), float(weather_lon))

    gps_spoofing_suspected = bool(distance_km is not None and distance_km > 5.0)
    location_valid = not gps_spoofing_suspected
    if gps_spoofing_suspected:
        reasons.append("location mismatch")

    activity_status = "active" if request.activity.lower() != "suspicious" else "none"
    fraud_score = calculate_fraud_score(
        activity_status,
        location_valid,
        request.claim_frequency,
        location_change_km=distance_km,
        reported_rain_mm=request.reported_rain_mm,
        actual_rain_mm=request.actual_rain_mm,
        time_since_last_claim_hours=request.time_since_last_claim_hours,
        weather_mismatch=request.weather_mismatch,
    )

    if gps_spoofing_suspected:
        fraud_score = min(1.0, round(fraud_score + 0.5, 2))

    # Determine decision
    if fraud_score > settings.claim_fraud_threshold:
        decision = "rejected"
        suffix = f" ({', '.join(reasons)})" if reasons else ""
        message = f"Claim rejected due to high fraud score: {fraud_score:.2f}{suffix}"
        new_status = "rejected"
    else:
        decision = "approved"
        suffix = f" ({', '.join(reasons)})" if reasons else ""
        message = f"Claim approved with fraud score: {fraud_score:.2f}{suffix}"
        new_status = "approved"

    # Update claim
    update_data = {
        "fraud_score": fraud_score,
        "status": new_status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    admin.table(settings.supabase_claims_table).update(update_data).eq("id", request.claim_id).execute()

    return FraudCheckResponse(
        fraud_score=fraud_score,
        decision=decision,
        message=message
    )