from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from app.schemas import PayoutDetailsCreateRequest
from app.services.payout_details_service import resolve_claim_payout_destination


class TestPayoutDetailsValidation:
    def test_invalid_input_rejected(self):
        with pytest.raises(ValidationError):
            PayoutDetailsCreateRequest(
                account_holder_name="Test User",
                bank_account_number="",
                ifsc_code="",
                upi_id="invalid-upi",
            )

    def test_valid_upi_accepted(self):
        payload = PayoutDetailsCreateRequest(
            account_holder_name="Test User",
            upi_id="tester@upi",
        )
        assert payload.upi_id == "tester@upi"

    def test_valid_bank_accepted(self):
        payload = PayoutDetailsCreateRequest(
            account_holder_name="Test User",
            bank_account_number="123456789012",
            ifsc_code="HDFC0001234",
        )
        assert payload.ifsc_code == "HDFC0001234"


class TestPayoutDestinationResolution:
    def test_no_payout_details_blocks_payout(self):
        assert resolve_claim_payout_destination(None) is None

    def test_upi_destination_selected(self):
        method, masked = resolve_claim_payout_destination(
            {
                "upi_id": "tester@upi",
                "bank_account_number": None,
            }
        )
        assert method == "upi"
        assert masked == "tester@upi"

    def test_bank_destination_masked(self):
        method, masked = resolve_claim_payout_destination(
            {
                "upi_id": None,
                "bank_account_number": "123456789012",
            }
        )
        assert method == "bank"
        assert masked.endswith("9012")
        assert masked.startswith("X")


class TestPayoutDetailsApi:
    def test_post_payout_details_valid_upi(self, client, mock_admin):
        with patch("app.routes.user.get_admin_client") as mock_get:
            mock_get.return_value = mock_admin
            mock_admin.execute.side_effect = [
                MagicMock(data=[]),
                MagicMock(
                    data=[
                        {
                            "account_holder_name": "Test User",
                            "bank_account_number": None,
                            "ifsc_code": None,
                            "upi_id": "tester@upi",
                            "created_at": "2026-01-01T00:00:00Z",
                        }
                    ]
                ),
            ]

            response = client.post(
                "/api/user/payout-details",
                json={
                    "account_holder_name": "Test User",
                    "upi_id": "tester@upi",
                },
            )

            assert response.status_code == 200
            body = response.json()
            assert body["upi_id"] == "tester@upi"
            assert body["bank_account_number_masked"] is None

    def test_post_payout_details_invalid_input_rejected(self, client):
        response = client.post(
            "/api/user/payout-details",
            json={
                "account_holder_name": "Test User",
                "ifsc_code": "BAD123",
            },
        )

        assert response.status_code == 422
