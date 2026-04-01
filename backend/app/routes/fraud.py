from fastapi import APIRouter, Depends, HTTPException, status

from ..config import get_settings
from ..dependencies import require_current_user
from ..schemas import FraudCheckRequest, FraudCheckResponse
from ..supabase_client import get_admin_client

router = APIRouter(prefix="/api/fraud", tags=["fraud"])

def calculate_fraud_score(gps: str, activity: str, claim_frequency: int) -> float:
    """Calculate fraud score based on inputs."""
    score = 0.0

    # Claim frequency factor (more claims = higher risk)
    score += min(0.5, claim_frequency / 20.0)

    # Activity factor
    if activity.lower() == "suspicious":
        score += 0.4

    # GPS factor (simplified: if not "expected", add risk)
    if gps.lower() != "expected":
        score += 0.3

    # Cap at 1.0
    return min(1.0, score)

@router.post("/check", response_model=FraudCheckResponse)
def check_fraud(request: FraudCheckRequest, current_user: dict = Depends(require_current_user)):
    settings = get_settings()
    admin = get_admin_client()

    # Verify claim belongs to user
    claim_response = (
        admin.table("claims")
        .select("*")
        .eq("id", request.claim_id)
        .eq("user_id", current_user["id"])
        .limit(1)
        .execute()
    )

    if not claim_response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    claim = claim_response.data[0]

    # Calculate fraud score
    fraud_score = calculate_fraud_score(request.gps, request.activity, request.claim_frequency)

    # Determine decision
    if fraud_score > 0.7:
        decision = "rejected"
        message = f"Claim rejected due to high fraud score: {fraud_score:.2f}"
        new_status = "rejected"
    else:
        decision = "approved"
        message = f"Claim approved with fraud score: {fraud_score:.2f}"
        new_status = "approved"

    # Update claim
    update_data = {
        "fraud_score": fraud_score,
        "status": new_status,
        "updated_at": "now()"
    }

    admin.table("claims").update(update_data).eq("id", request.claim_id).execute()

    return FraudCheckResponse(
        fraud_score=fraud_score,
        decision=decision,
        message=message
    )