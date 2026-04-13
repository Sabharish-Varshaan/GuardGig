from __future__ import annotations

from ..payout_utils import mask_bank_account


def fetch_user_payout_details(admin, payout_details_table: str, user_id: str) -> dict | None:
    response = (
        admin.table(payout_details_table)
        .select("user_id,account_holder_name,bank_account_number,ifsc_code,upi_id,created_at")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    rows = response.data or []
    return rows[0] if rows else None


def resolve_claim_payout_destination(payout_details: dict | None) -> tuple[str, str] | None:
    if not payout_details:
        return None

    upi_id = payout_details.get("upi_id")
    if upi_id:
        return "upi", str(upi_id)

    masked_bank = mask_bank_account(payout_details.get("bank_account_number"))
    if masked_bank:
        return "bank", masked_bank

    return None
