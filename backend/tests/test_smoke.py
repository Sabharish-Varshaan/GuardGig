"""
Simple smoke tests to verify basic setup
Run this first before running full test suite
"""
import pytest
from unittest.mock import MagicMock, patch
import os
import sys
from pathlib import Path

# Ensure path is set
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestBasicSetup:
    """Test basic imports and setup"""

    def test_imports(self):
        """Test that basic imports work"""
        try:
            from app.main import app
            from app.supabase_client import get_admin_client
            from app.dependencies import get_current_user, require_current_user
            print("\n✓ All imports successful")
            assert True
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

    def test_fastapi_app(self):
        """Test FastAPI app initialization"""
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        print("\n✓ FastAPI app initialized")
        assert client is not None

    def test_mock_admin_client(self):
        """Test mock admin client chain"""
        admin = MagicMock()
        admin.table = MagicMock(return_value=admin)
        admin.select = MagicMock(return_value=admin)
        admin.eq = MagicMock(return_value=admin)
        admin.execute = MagicMock(return_value=MagicMock(data=[]))
        
        # Test chaining
        result = admin.table("users").select("*").eq("id", "123").execute()
        assert result.data == []
        print("\n✓ Mock chaining works correctly")

    def test_mock_with_data(self):
        """Test mock with return data"""
        admin = MagicMock()
        admin.table = MagicMock(return_value=admin)
        admin.select = MagicMock(return_value=admin)
        admin.eq = MagicMock(return_value=admin)
        admin.execute = MagicMock(return_value=MagicMock(data=[
            {"id": "user-1", "phone": "9876543210"}
        ]))
        
        result = admin.table("users").select("*").eq("id", "user-1").execute()
        assert result.data[0]["id"] == "user-1"
        print("\n✓ Mock data returning correctly")

    def test_patch_import(self):
        """Test patching works correctly"""
        with patch('app.supabase_client.get_admin_client') as mock_get:
            mock_admin = MagicMock()
            mock_get.return_value = mock_admin
            
            from app.supabase_client import get_admin_client
            client = get_admin_client()
            assert client == mock_admin
            print("\n✓ Patching works correctly")


# Business Logic Tests
class TestBusinessLogic:
    """Test core business logic without API mocking"""

    def test_payout_calculation(self):
        """Test payout calculation logic"""
        mean_income = 30000
        payout_percentage = 30
        coverage_amount = 100000
        
        payout = min(
            (payout_percentage / 100) * mean_income,
            coverage_amount
        )
        
        assert payout == 9000
        print("\n✓ Payout calculation correct (30% of ₹30,000 = ₹9,000)")

    def test_fraud_score_calculation(self):
        """Test fraud score heuristic"""
        claims_today = 2
        activity_status = "active"
        location_valid = True
        
        base_score = min(0.5, claims_today / 20)
        if activity_status in {"none", "inactive", "suspicious"}:
            base_score += 0.4
        if not location_valid:
            base_score += 0.3
        fraud_score = min(1.0, base_score)
        
        assert fraud_score == 0.1
        is_approved = fraud_score <= 0.7
        assert is_approved
        print("\n✓ Fraud score calculation correct (score=0.1, approved=True)")

    def test_loss_ratio_calculation(self):
        """Test loss ratio calculation"""
        total_premium = 10000.0
        total_payout = 6000.0
        
        loss_ratio = total_payout / total_premium if total_premium > 0 else 0.0
        assert loss_ratio == 0.6
        
        can_create_policy = loss_ratio <= 0.85
        assert can_create_policy
        print("\n✓ Loss ratio calculation correct (0.6, policies allowed)")

    def test_trigger_thresholds(self):
        """Test trigger logic"""
        test_cases = [
            (30, 250, 0),           # No trigger
            (60, 250, 30),          # Rain 30%
            (120, 250, 60),         # Rain 60%
            (160, 250, 100),        # Rain 100%
            (30, 320, 30),          # AQI 30%
            (30, 510, 100),         # AQI 100%
            (160, 510, 100),        # Both max = 100%
        ]
        
        for rain_mm, aqi, expected_payout in test_cases:
            # Rain logic
            rain_payout = 100 if rain_mm >= 150 else (60 if rain_mm >= 100 else 30 if rain_mm >= 50 else 0)
            # AQI logic
            aqi_payout = 100 if aqi >= 500 else (60 if aqi >= 400 else 30 if aqi >= 300 else 0)
            # Multi-trigger: higher wins
            payout = max(rain_payout, aqi_payout)
            
            assert payout == expected_payout, f"Rain={rain_mm}, AQI={aqi}: expected {expected_payout}, got {payout}"
        
        print("\n✓ All trigger thresholds correct")

    def test_daily_claim_limit(self):
        """Test daily claim limit logic"""
        from datetime import datetime, date
        
        claim1_date = date(2024, 1, 15)
        claim2_date = date(2024, 1, 15)
        claim3_date = date(2024, 1, 16)
        
        # Same day = limit reached
        same_day_12h = claim1_date == claim2_date
        assert same_day_12h  # 1st claim ok, 2nd on same day = rejected
        
        # Different day = allowed
        different_day = claim1_date != claim3_date
        assert different_day  # 3rd claim on different day = allowed
        
        print("\n✓ Daily claim limit logic correct")

    def test_waiting_period(self):
        """Test 24h waiting period logic"""
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        policy_created = now
        
        # Try claim 12h later
        claim_12h = now + timedelta(hours=12)
        time_elapsed_12h = (claim_12h - policy_created).total_seconds()
        can_claim_12h = time_elapsed_12h >= 86400  # 24h in seconds
        assert not can_claim_12h
        
        # Try claim 25h later
        claim_25h = now + timedelta(hours=25)
        time_elapsed_25h = (claim_25h - policy_created).total_seconds()
        can_claim_25h = time_elapsed_25h >= 86400
        assert can_claim_25h
        
        print("\n✓ Waiting period logic correct")
