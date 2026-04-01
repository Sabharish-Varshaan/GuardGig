from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from ..claim_rules import calculate_fraud_score
from ..config import get_settings
from ..dependencies import require_current_user
from ..schemas import FraudCheckRequest, FraudCheckResponse
from ..supabase_client import get_admin_client

router = APIRouter(prefix="/api/fraud", tags=["fraud"])

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

    # Calculate fraud score
    location_valid = request.gps.lower() == "expected"
    activity_status = "active" if request.activity.lower() != "suspicious" else "none"
    fraud_score = calculate_fraud_score(activity_status, location_valid, request.claim_frequency)

    # Determine decision
    if fraud_score > settings.claim_fraud_threshold:
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
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    admin.table(settings.supabase_claims_table).update(update_data).eq("id", request.claim_id).execute()

    return FraudCheckResponse(
        fraud_score=fraud_score,
        decision=decision,
        message=message
    )