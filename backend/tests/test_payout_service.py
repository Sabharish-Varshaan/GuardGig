from unittest.mock import MagicMock, patch

import pytest

from app.services.payout_service import process_payout


@pytest.fixture
def mock_admin():
    admin = MagicMock()
    admin.table = MagicMock(return_value=admin)
    admin.select = MagicMock(return_value=admin)
    admin.eq = MagicMock(return_value=admin)
    admin.update = MagicMock(return_value=admin)
    admin.limit = MagicMock(return_value=admin)
    admin.execute = MagicMock(return_value=MagicMock(data=[{"id": "claim-1"}]))
    return admin


def test_process_payout_upi_credited(mock_admin):
    claim = {"id": "claim-1", "user_id": "user-1", "payout_amount": 120.0}

    with patch("app.services.payout_service.fetch_user_payout_details", return_value={"upi_id": "worker@upi"}):
        with patch("app.services.payout_service.resolve_claim_payout_destination", return_value=("upi", "worker@upi")):
            result = process_payout(
                claim,
                admin=mock_admin,
                claims_table="claims",
                payout_details_table="user_payout_details",
                trigger_snapshot={},
                delay_range=(0.0, 0.0),
            )

    assert result["success"] is True
    assert result["payment_status"] == "credited"
    assert result["payout_status"] == "credited"
    assert result["payout_method"] == "upi"
    assert result["order_id"].startswith("order_")
    assert result["payment_id"].startswith("pay_")
    assert result["payment_signature"].startswith("sig_")
    assert result["transaction_id"].startswith("RZP_")
    assert len(result["transaction_id"]) == 14


def test_process_payout_bank_credited(mock_admin):
    claim = {"id": "claim-2", "user_id": "user-2", "payout_amount": 220.0}

    with patch("app.services.payout_service.fetch_user_payout_details", return_value={"bank_account_number": "1234567890"}):
        with patch("app.services.payout_service.resolve_claim_payout_destination", return_value=("bank", "******7890")):
            result = process_payout(
                claim,
                admin=mock_admin,
                claims_table="claims",
                payout_details_table="user_payout_details",
                trigger_snapshot={},
                delay_range=(0.0, 0.0),
            )

    assert result["success"] is True
    assert result["payment_status"] == "credited"
    assert result["payout_status"] == "credited"
    assert result["payout_method"] == "bank"
    assert result["transaction_id"].startswith("RZP_")


def test_process_payout_no_details_failed(mock_admin):
    claim = {"id": "claim-3", "user_id": "user-3", "payout_amount": 180.0}

    with patch("app.services.payout_service.fetch_user_payout_details", return_value=None):
        with patch("app.services.payout_service.resolve_claim_payout_destination", return_value=None):
            result = process_payout(
                claim,
                admin=mock_admin,
                claims_table="claims",
                payout_details_table="user_payout_details",
                trigger_snapshot={},
                delay_range=(0.0, 0.0),
            )

    assert result["success"] is False
    assert result["payment_status"] == "pending_payout_details"
    assert result["payout_status"] == "failed"
    assert result["transaction_id"] is None


def test_claim_created_auto_triggers_payout_processing(mock_admin):
    claim = {"id": "claim-4", "user_id": "user-4", "payout_amount": 150.0, "status": "approved"}

    with patch("app.services.payout_service.fetch_user_payout_details", return_value={"upi_id": "worker@upi"}):
        with patch("app.services.payout_service.resolve_claim_payout_destination", return_value=("upi", "worker@upi")):
            with patch("app.services.payout_service.update_claim_payout_status") as mock_update_status:
                result = process_payout(
                    claim,
                    admin=mock_admin,
                    claims_table="claims",
                    payout_details_table="user_payout_details",
                    trigger_snapshot={},
                    delay_range=(0.0, 0.0),
                )

    assert result["success"] is True
    mock_update_status.assert_called_once_with(mock_admin, "claims", "claim-4", "processing")
