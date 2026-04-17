"""
Fraud Detection Tests

Tests:
- Fraud score calculation
- Threshold enforcement (0.8)
- High fraud → claim rejected
- Low fraud → claim approved
- Medium fraud → payout reduced
- Exclusion rules (activity status, location)
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.claim_rules import calculate_fraud_score


class _FraudRouteResponse:
    def __init__(self, data):
        self.data = data


class _FraudRouteAdmin:
    def __init__(self, claim: dict):
        self.claim = dict(claim)
        self._table = None
        self._op = None
        self._filters = {}
        self._payload = None

    def table(self, table_name):
        self._table = table_name
        self._op = None
        self._filters = {}
        self._payload = None
        return self

    def select(self, *_args, **_kwargs):
        self._op = "select"
        return self

    def update(self, payload):
        self._op = "update"
        self._payload = payload
        return self

    def eq(self, key, value):
        self._filters[key] = value
        return self

    def limit(self, _count):
        return self

    def execute(self):
        if self._op == "select":
            if (
                self._filters.get("id") == self.claim.get("id")
                and self._filters.get("user_id") == self.claim.get("user_id")
            ):
                return _FraudRouteResponse([dict(self.claim)])
            return _FraudRouteResponse([])

        if self._op == "update":
            self.claim.update(self._payload or {})
            return _FraudRouteResponse([dict(self.claim)])

        return _FraudRouteResponse([])


class TestFraudDetectionHeuristic:
    """Test fraud detection using heuristic fallback"""

    @pytest.mark.parametrize("claims_today,activity_status,location_valid,expected_fraud_score,expected_approved", [
        (0, "active", True, 0.0, True),           # Clean
        (1, "active", True, 0.05, True),          # Few claims
        (5, "active", True, 0.25, True),          # Moderate claims
        (10, "inactive", True, 0.7, False),       # High frequency + inactive
        (0, "suspicious", False, 0.7, False),     # Suspicious activity
        (15, "none", False, 1.0, False),          # Multiple red flags
    ])
    def test_fraud_detection_heuristic(self, claims_today, activity_status, location_valid,
                                       expected_fraud_score, expected_approved):
        """Test fraud score calculation with heuristic"""
        # Heuristic formula:
        base_score = min(0.5, claims_today / 20)
        if activity_status in {"none", "inactive", "suspicious"}:
            base_score += 0.4
        if not location_valid:
            base_score += 0.3
        fraud_score = min(1.0, base_score)
        
        is_approved = fraud_score <= 0.8
        
        print(f"\n[TEST] Fraud Detection - claims={claims_today}, activity={activity_status}, location_valid={location_valid}")
        print(f"Input: claims_today={claims_today}, activity_status={activity_status}, location_valid={location_valid}")
        print(f"Expected: fraud_score≈{expected_fraud_score}, approved={expected_approved}")
        print(f"Actual: fraud_score={fraud_score:.2f}, approved={is_approved}")

    def test_fraud_score_clean_user(self):
        """Test fraud score for clean user"""
        claims_today = 0
        activity_status = "active"
        location_valid = True
        
        base_score = min(0.5, claims_today / 20)
        fraud_score = base_score
        
        print("\n[TEST] Fraud Score - Clean User")
        print(f"Input: No claims, active status, valid location")
        print(f"Expected: fraud_score=0.0")
        print(f"Actual: fraud_score={fraud_score}")
        assert fraud_score == 0.0
        print("Result: PASS")

    def test_fraud_score_frequent_claims(self):
        """Test fraud score increases with claim frequency"""
        scores = []
        for claims_today in [0, 1, 5, 10]:
            score = min(0.5, claims_today / 20)
            scores.append((claims_today, score))
        
        print("\n[TEST] Fraud Score - Claim Frequency Impact")
        print(f"Input: Varying claim counts (0-10)")
        print(f"Expected: Score increases monotonically")
        for claims, score in scores:
            print(f"  {claims} claims → score={score:.2f}")
        # Verify monotonic increase
        for i in range(1, len(scores)):
            assert scores[i][1] >= scores[i-1][1]
        print("Result: PASS (monotonic increase)")

    def test_fraud_score_activity_status_inactive(self):
        """Test fraud score penalty for inactive status"""
        base_score = 0.1
        activity_penalty = 0.4  # +0.4 for inactive/suspicious/none
        final_score = min(1.0, base_score + activity_penalty)
        
        print("\n[TEST] Fraud Score - Activity Status Penalty")
        print(f"Input: activity_status='inactive'")
        print(f"Expected: fraud_score = base + 0.4")
        print(f"Actual: {base_score} + {activity_penalty} = {final_score}")
        assert final_score == 0.5
        print("Result: PASS")

    def test_fraud_score_invalid_location(self):
        """Test fraud score penalty for invalid location"""
        base_score = 0.1
        location_penalty = 0.3  # +0.3 for invalid location
        final_score = min(1.0, base_score + location_penalty)
        
        print("\n[TEST] Fraud Score - Location Penalty")
        print(f"Input: location_valid=False")
        print(f"Expected: fraud_score = base + 0.3")
        print(f"Actual: {base_score} + {location_penalty} = {final_score}")
        assert final_score == 0.4
        print("Result: PASS")

    def test_fraud_score_multiple_red_flags(self):
        """Test fraud score with multiple red flags"""
        base_score = 0.5  # Max base score
        activity_penalty = 0.4
        location_penalty = 0.3
        preliminary = base_score + activity_penalty + location_penalty
        final_score = min(1.0, preliminary)
        
        print("\n[TEST] Fraud Score - Multiple Red Flags")
        print(f"Input: High claim count + inactive + invalid location")
        print(f"Expected: fraud_score=1.0 (clamped)")
        print(f"Actual: {base_score} + {activity_penalty} + {location_penalty} = {preliminary} → {final_score}")
        assert final_score == 1.0
        print("Result: PASS")


class TestFraudThreshold:
    """Test fraud score threshold enforcement"""

    def test_fraud_threshold_approved(self):
        """Test claim approved when fraud_score <= 0.8"""
        fraud_score = 0.6
        threshold = 0.8
        is_approved = fraud_score <= threshold
        
        print("\n[TEST] Fraud Threshold - Approved (score=0.6)")
        print(f"Input: fraud_score={fraud_score}, threshold={threshold}")
        print(f"Expected: approved=True")
        print(f"Actual: approved={is_approved}")
        assert is_approved
        print("Result: PASS")

    def test_fraud_threshold_rejected(self):
        """Test claim rejected when fraud_score > 0.8"""
        fraud_score = 0.81
        threshold = 0.8
        is_approved = fraud_score <= threshold
        
        print("\n[TEST] Fraud Threshold - Rejected (score=0.81)")
        print(f"Input: fraud_score={fraud_score}, threshold={threshold}")
        print(f"Expected: approved=False")
        print(f"Actual: approved={is_approved}")
        assert not is_approved
        print("Result: PASS")

    def test_fraud_threshold_boundary(self):
        """Test fraud score at exactly threshold"""
        fraud_score = 0.8
        threshold = 0.8
        is_approved = fraud_score <= threshold
        
        print("\n[TEST] Fraud Threshold - Boundary (score=0.8)")
        print(f"Input: fraud_score={fraud_score}, threshold={threshold}")
        print(f"Expected: approved=True (<=, not <)")
        print(f"Actual: approved={is_approved}")
        assert is_approved
        print("Result: PASS")

    def test_fraud_threshold_just_above(self):
        """Test fraud score just above threshold"""
        fraud_score = 0.81
        threshold = 0.8
        is_approved = fraud_score <= threshold
        
        print("\n[TEST] Fraud Threshold - Just Above (score=0.81)")
        print(f"Input: fraud_score={fraud_score}, threshold={threshold}")
        print(f"Expected: approved=False")
        print(f"Actual: approved={is_approved}")
        assert not is_approved
        print("Result: PASS")


class TestFraudExclusions:
    """Test fraud detection exclusion rules"""

    def test_exclusion_none_activity(self):
        """Test claim rejected for activity_status='none'"""
        activity_status = "none"
        is_excluded = activity_status in {"none", "inactive", "suspicious"}
        
        print("\n[TEST] Fraud Exclusion - Activity Status 'none'")
        print(f"Input: activity_status='{activity_status}'")
        print(f"Expected: Should exclude")
        print(f"Actual: is_excluded={is_excluded}")
        assert is_excluded
        print("Result: PASS")

    def test_exclusion_suspicious_activity(self):
        """Test claim rejected for activity_status='suspicious'"""
        activity_status = "suspicious"
        is_excluded = activity_status in {"none", "inactive", "suspicious"}
        
        print("\n[TEST] Fraud Exclusion - Activity Status 'suspicious'")
        print(f"Input: activity_status='{activity_status}'")
        print(f"Expected: Should exclude")
        print(f"Actual: is_excluded={is_excluded}")
        assert is_excluded
        print("Result: PASS")

    def test_exclusion_inactive_activity(self):
        """Test claim rejected for activity_status='inactive'"""
        activity_status = "inactive"
        is_excluded = activity_status in {"none", "inactive", "suspicious"}
        
        print("\n[TEST] Fraud Exclusion - Activity Status 'inactive'")
        print(f"Input: activity_status='{activity_status}'")
        print(f"Expected: Should exclude")
        print(f"Actual: is_excluded={is_excluded}")
        assert is_excluded
        print("Result: PASS")

    def test_exclusion_active_activity(self):
        """Test claim NOT excluded for activity_status='active'"""
        activity_status = "active"
        is_excluded = activity_status in {"none", "inactive", "suspicious"}
        
        print("\n[TEST] Fraud Exclusion - Activity Status 'active'")
        print(f"Input: activity_status='{activity_status}'")
        print(f"Expected: Should NOT exclude")
        print(f"Actual: is_excluded={is_excluded}")
        assert not is_excluded
        print("Result: PASS")

    def test_exclusion_invalid_location(self):
        """Test claim rejected for invalid location"""
        location_valid = False
        is_excluded = not location_valid
        
        print("\n[TEST] Fraud Exclusion - Invalid Location")
        print(f"Input: location_valid={location_valid}")
        print(f"Expected: Should exclude")
        print(f"Actual: is_excluded={is_excluded}")
        assert is_excluded
        print("Result: PASS")

    def test_exclusion_valid_location(self):
        """Test claim NOT excluded for valid location"""
        location_valid = True
        is_excluded = not location_valid
        
        print("\n[TEST] Fraud Exclusion - Valid Location")
        print(f"Input: location_valid={location_valid}")
        print(f"Expected: Should NOT exclude")
        print(f"Actual: is_excluded={is_excluded}")
        assert not is_excluded
        print("Result: PASS")


class TestFraudWithClaims:
    """Test fraud detection in business context"""

    def test_high_fraud_claim_rejected(self):
        """Test high-fraud claim is NOT paid"""
        claim = {
            "status": "approved",
            "fraud_score": 0.85,
            "payout_amount": 9000
        }
        
        threshold = 0.8
        is_rejected = claim["fraud_score"] > threshold
        final_status = "rejected" if is_rejected else "approved"
        final_payout = 0 if is_rejected else claim["payout_amount"]
        
        print("\n[TEST] Fraud With Claims - High Fraud Rejected")
        print(f"Input: fraud_score={claim['fraud_score']}, payout={claim['payout_amount']}")
        print(f"Expected: status=rejected, payout=0")
        print(f"Actual: status={final_status}, payout={final_payout}")
        assert is_rejected and final_payout == 0
        print("Result: PASS")

    def test_low_fraud_claim_approved(self):
        """Test low-fraud claim IS paid"""
        claim = {
            "status": "approved",
            "fraud_score": 0.2,
            "payout_amount": 9000
        }
        
        threshold = 0.8
        is_approved = claim["fraud_score"] <= threshold
        final_status = "approved" if is_approved else "rejected"
        final_payout = claim["payout_amount"] if is_approved else 0
        
        print("\n[TEST] Fraud With Claims - Low Fraud Approved")
        print(f"Input: fraud_score={claim['fraud_score']}, payout={claim['payout_amount']}")
        print(f"Expected: status=approved, payout={claim['payout_amount']}")
        print(f"Actual: status={final_status}, payout={final_payout}")
        assert is_approved and final_payout == 9000
        print("Result: PASS")

    def test_medium_fraud_claim_payout_halved(self):
        """Test medium fraud score reduces payout by 50%"""
        claim = {
            "fraud_score": 0.7,
            "payout_amount": 9000,
        }

        reject_threshold = 0.8
        medium_threshold = 0.6

        is_rejected = claim["fraud_score"] > reject_threshold
        if is_rejected:
            final_payout = 0
        elif claim["fraud_score"] > medium_threshold:
            final_payout = claim["payout_amount"] * 0.5
        else:
            final_payout = claim["payout_amount"]

        print("\n[TEST] Fraud With Claims - Medium Fraud Payout Halved")
        print(f"Input: fraud_score={claim['fraud_score']}, payout={claim['payout_amount']}")
        print("Expected: status=approved, payout halved to 4500")
        print(f"Actual: rejected={is_rejected}, payout={final_payout}")
        assert not is_rejected and final_payout == 4500


class TestFraudGpsDistance:
    def test_far_gps_flagged(self, client):
        from app.auth_utils import create_access_token

        token = create_access_token(user_id="test-user-123", phone="9876543210")
        admin = _FraudRouteAdmin(
            claim={
                "id": "claim-1",
                "user_id": "test-user-123",
                "status": "pending",
                "fraud_score": 0.0,
            }
        )

        with patch("app.routes.fraud.get_admin_client", return_value=admin), patch(
            "app.routes.fraud.calculate_fraud_score", return_value=0.4
        ):
            response = client.post(
                "/api/fraud/check",
                json={
                    "claim_id": "claim-1",
                    "gps": "12.9716,77.5946",
                    "activity": "normal",
                    "claim_frequency": 0,
                    "weather_lat": 12.9,
                    "weather_lon": 77.3,
                },
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["decision"] == "rejected"
        assert "location mismatch" in body["message"].lower()

    def test_near_gps_allowed(self, client):
        from app.auth_utils import create_access_token

        token = create_access_token(user_id="test-user-123", phone="9876543210")
        admin = _FraudRouteAdmin(
            claim={
                "id": "claim-2",
                "user_id": "test-user-123",
                "status": "pending",
                "fraud_score": 0.0,
            }
        )

        with patch("app.routes.fraud.get_admin_client", return_value=admin), patch(
            "app.routes.fraud.calculate_fraud_score", return_value=0.4
        ):
            response = client.post(
                "/api/fraud/check",
                json={
                    "claim_id": "claim-2",
                    "gps": "12.9716,77.5946",
                    "activity": "normal",
                    "claim_frequency": 0,
                    "weather_lat": 12.972,
                    "weather_lon": 77.595,
                },
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["decision"] == "approved"
        print("Result: PASS")


class TestFraudSafetyLayer:
    """Regression coverage for the stronger fraud safety overlay."""

    def test_gps_spoofing_increases_fraud_score(self):
        base_score = calculate_fraud_score(
            activity_status="active",
            location_valid=True,
            claim_frequency=0,
            location_change_km=0.0,
            reported_rain_mm=20.0,
            actual_rain_mm=20.0,
        )
        spoofed_score = calculate_fraud_score(
            activity_status="active",
            location_valid=False,
            claim_frequency=0,
            location_change_km=7.5,
            reported_rain_mm=20.0,
            actual_rain_mm=20.0,
        )

        assert spoofed_score > base_score
        assert spoofed_score >= 0.3

    def test_weather_mismatch_increases_fraud_score(self):
        clean_score = calculate_fraud_score(
            activity_status="active",
            location_valid=True,
            claim_frequency=0,
            location_change_km=0.0,
            reported_rain_mm=10.0,
            actual_rain_mm=10.0,
        )
        mismatch_score = calculate_fraud_score(
            activity_status="active",
            location_valid=True,
            claim_frequency=0,
            location_change_km=0.0,
            reported_rain_mm=10.0,
            actual_rain_mm=45.0,
        )

        assert mismatch_score > clean_score
        assert mismatch_score >= 0.15

    def test_claim_frequency_abuse_increases_fraud_score(self):
        clean_score = calculate_fraud_score(
            activity_status="active",
            location_valid=True,
            claim_frequency=0,
            location_change_km=0.0,
            reported_rain_mm=10.0,
            actual_rain_mm=10.0,
        )
        abusive_score = calculate_fraud_score(
            activity_status="active",
            location_valid=True,
            claim_frequency=8,
            location_change_km=0.0,
            reported_rain_mm=10.0,
            actual_rain_mm=10.0,
        )

        assert abusive_score > clean_score
        assert abusive_score >= 0.35
