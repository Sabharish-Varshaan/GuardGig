"""
Pytest configuration and shared fixtures for GuardGig test suite
"""
import os
import sys
import pytest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
# **CRITICAL**: Set dummy environment variables before importing app
if not os.getenv('SUPABASE_URL'):
    os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
    os.environ['SUPABASE_ANON_KEY'] = 'test-anon-key'
    os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'test-service-role-key'
    os.environ['JWT_SECRET'] = 'test-jwt-secret-key'


from app.main import app
from app.dependencies import require_current_user, require_admin_user
from app.supabase_client import get_admin_client
from fastapi.testclient import TestClient
import asyncio
import json
from datetime import datetime, timedelta
import hashlib
import hmac
from unittest.mock import MagicMock, patch

# Test Client
@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def override_authenticated_user():
    """Avoid real Supabase calls for auth dependency in protected routes."""
    app.dependency_overrides[require_current_user] = lambda: {
        "id": "test-user-123",
        "phone": "9876543210",
    }
    app.dependency_overrides[require_admin_user] = lambda: {
        "id": "test-admin-123",
        "phone": "9999999999",
        "role": "admin",
        "email": "admin@guardgig.com",
        "full_name": "Test Admin",
    }
    yield
    app.dependency_overrides.pop(require_current_user, None)
    app.dependency_overrides.pop(require_admin_user, None)


# Mock Database
@pytest.fixture
def mock_admin():
    """Mock Supabase admin client"""
    admin = MagicMock()
    # Setup mock to chain method calls properly (fluent API)
    admin.table = MagicMock(return_value=admin)
    admin.select = MagicMock(return_value=admin)
    admin.eq = MagicMock(return_value=admin)
    admin.insert = MagicMock(return_value=admin)
    admin.update = MagicMock(return_value=admin)
    admin.delete = MagicMock(return_value=admin)
    admin.limit = MagicMock(return_value=admin)
    admin.execute = MagicMock(return_value=MagicMock(data=[]))
    return admin


# Test Data
@pytest.fixture
def test_user_data():
    """Sample user registration data"""
    return {
        "phone": "9876543210",
        "password": "SecurePass123!"
    }


@pytest.fixture
def test_user_with_id(test_user_data):
    """User with generated ID"""
    return {
        **test_user_data,
        "id": "test-user-123",
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def test_onboarding_data():
    """Sample onboarding profile"""
    return {
        "min_income": 10000,
        "max_income": 50000,
        "risk_preference": "moderate"
    }


@pytest.fixture
def test_onboarding_complete(test_user_with_id):
    """Complete onboarding profile in database"""
    return {
        "id": "onboarding-123",
        "user_id": test_user_with_id["id"],
        "min_income": 10000,
        "max_income": 50000,
        "mean_income": 30000,
        "income_variance": 100000,
        "risk_preference": "moderate",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def test_policy_data():
    """Create policy request data"""
    return {
        "coverage_amount": 100000
    }


@pytest.fixture
def test_policy_active(test_user_with_id, test_onboarding_complete):
    """Active policy in database"""
    now = datetime.utcnow()
    return {
        "id": "policy-123",
        "user_id": test_user_with_id["id"],
        "premium": 450,
        "coverage_amount": 100000,
        "status": "active",
        "payment_status": "success",
        "activated_at": now.isoformat(),
        "expires_at": (now + timedelta(days=7)).isoformat(),
        "onboarding_profile_id": test_onboarding_complete["id"],
        "created_at": now.isoformat()
    }


@pytest.fixture
def test_location_data():
    """Sample location for trigger testing"""
    return {
        "city": "Delhi",
        "lat": 28.7041,
        "lon": 77.1025
    }


@pytest.fixture
def razorpay_mock_keys():
    """Razorpay key for signature verification"""
    return {
        "key_id": "rzp_test_123456",
        "key_secret": "test_secret_key_12345"
    }


def create_razorpay_signature(data: dict, secret: str) -> str:
    """Create valid Razorpay signature for testing"""
    message = f"{data.get('order_id')}|{data.get('payment_id')}"
    signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature


@pytest.fixture
def razorpay_payment_valid(razorpay_mock_keys):
    """Valid Razorpay payment verification data"""
    order_id = "order_123"
    payment_id = "pay_456"
    signature = create_razorpay_signature(
        {"order_id": order_id, "payment_id": payment_id},
        razorpay_mock_keys["key_secret"]
    )
    return {
        "order_id": order_id,
        "payment_id": payment_id,
        "signature": signature
    }


@pytest.fixture
def razorpay_payment_invalid(razorpay_mock_keys):
    """Invalid Razorpay payment signature"""
    return {
        "order_id": "order_123",
        "payment_id": "pay_456",
        "signature": "invalid_signature_xyz"
    }


# Event loop for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Trigger test data
@pytest.fixture
def trigger_test_cases():
    """Test cases for trigger logic"""
    return [
        # (rain_mm, aqi, expected_triggered, expected_payout_pct)
        (30, 250, False, 0),          # No trigger
        (60, 250, True, 30),           # Rain trigger 30%
        (120, 250, True, 60),          # Rain trigger 60%
        (160, 250, True, 100),         # Rain trigger 100%
        (30, 320, True, 30),           # AQI trigger 30%
        (30, 420, True, 60),           # AQI trigger 60%
        (30, 510, True, 100),          # AQI trigger 100%
        (160, 510, True, 100),         # Both trigger, choose max (100%)
        (30, 0, False, 0),             # Neither
    ]


# Fraud test data
@pytest.fixture
def fraud_test_cases():
    """Test cases for fraud detection"""
    return [
        # (claims_today, activity_status, location_valid, expected_fraud_score, expected_approved)
        (0, "active", True, 0.0, True),
        (1, "active", True, 0.1, True),
        (5, "active", True, 0.25, True),
        (10, "inactive", True, 0.7, False),  # High frequency + inactive
        (0, "suspicious", False, 0.7, False),  # Suspicious activity
        (15, "none", False, 1.0, False),        # Multiple red flags
    ]


# Claim test data
@pytest.fixture
def claim_test_cases():
    """Test cases for claim generation and payout"""
    return [
        # (mean_income, payout_pct, expected_payout)
        (30000, 30, 9000),
        (50000, 60, 30000),
        (100000, 100, 100000),
        (10000, 30, 3000),
        (0, 30, 0),  # Zero income
    ]
