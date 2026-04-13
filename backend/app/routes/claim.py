from fastapi import APIRouter, Depends

from ..config import get_settings
from ..dependencies import require_current_user
from ..schemas import ClaimsListResponse, ClaimResponse
from ..supabase_client import get_admin_client

router = APIRouter(prefix="/api", tags=["claim"])
@router.get("/claims/me", response_model=ClaimsListResponse)
def get_my_claims(current_user: dict = Depends(require_current_user)):
    settings = get_settings()
    admin = get_admin_client()

    claims_response = (
        admin.table(settings.supabase_claims_table)
        .select("*")
        .eq("user_id", current_user["id"])
        .order("created_at", desc=True)
        .execute()
    )

    claims = [ClaimResponse(**claim) for claim in (claims_response.data or [])]

    return ClaimsListResponse(claims=claims)