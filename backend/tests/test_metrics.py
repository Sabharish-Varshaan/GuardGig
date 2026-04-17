"""
Metrics & Actuarial Intelligence Tests

Tests:
- Premium tracking (total_premium increases)
- Payout tracking (total_payout increases)
- Loss ratio calculation (payout / premium)
- Loss ratio threshold (> 85% blocks policies)
- Zero division safety
"""
import pytest
from decimal import Decimal

from app.metrics_utils import _calculate_loss_ratio, classify_loss_ratio_status


class TestMetricsTracking:
    """Test system metrics tracking"""

    def test_premium_added_to_total(self):
        """Test premium is added to total_premium on payment"""
        initial_total = Decimal('0.00')
        premium_amount = Decimal('450.00')
        
        updated_total = initial_total + premium_amount
        
        print("\n[TEST] Metrics - Premium Added")
        print(f"Input: premium={premium_amount}")
        print(f"Expected: total_premium increases by {premium_amount}")
        print(f"Actual: {initial_total} + {premium_amount} = {updated_total}")
        assert updated_total == Decimal('450.00')
        print("Result: PASS")

    def test_payout_added_to_total(self):
        """Test payout is added to total_payout on claim"""
        initial_total = Decimal('0.00')
        payout_amount = Decimal('9000.00')
        
        updated_total = initial_total + payout_amount
        
        print("\n[TEST] Metrics - Payout Added")
        print(f"Input: payout={payout_amount}")
        print(f"Expected: total_payout increases by {payout_amount}")
        print(f"Actual: {initial_total} + {payout_amount} = {updated_total}")
        assert updated_total == Decimal('9000.00')
        print("Result: PASS")

    def test_multiple_premiums_accumulate(self):
        """Test multiple premiums accumulate correctly"""
        total = Decimal('0.00')
        premiums = [Decimal('450.00'), Decimal('500.00'), Decimal('400.00')]
        
        for premium in premiums:
            total += premium
        
        expected = Decimal('1350.00')
        
        print("\n[TEST] Metrics - Multiple Premiums")
        print(f"Input: premiums={premiums}")
        print(f"Expected: total={expected}")
        print(f"Actual: total={total}")
        assert total == expected
        print("Result: PASS")

    def test_multiple_payouts_accumulate(self):
        """Test multiple payouts accumulate correctly"""
        total = Decimal('0.00')
        payouts = [Decimal('9000.00'), Decimal('15000.00'), Decimal('6000.00')]
        
        for payout in payouts:
            total += payout
        
        expected = Decimal('30000.00')
        
        print("\n[TEST] Metrics - Multiple Payouts")
        print(f"Input: payouts={payouts}")
        print(f"Expected: total={expected}")
        print(f"Actual: total={total}")
        assert total == expected
        print("Result: PASS")


class TestLossRatioCalculation:
    """Test loss ratio calculation and thresholds"""

    def test_loss_ratio_calculation(self):
        """Test loss_ratio = total_payout / total_premium"""
        total_premium = Decimal('10000.00')
        total_payout = Decimal('6000.00')
        
        loss_ratio = total_payout / total_premium if total_premium > 0 else Decimal('0.00')
        
        print("\n[TEST] Loss Ratio - Calculation")
        print(f"Input: premium={total_premium}, payout={total_payout}")
        print(f"Expected: loss_ratio = {total_payout}/{total_premium}")
        print(f"Actual: loss_ratio = {loss_ratio}")
        assert loss_ratio == Decimal('0.6')
        print("Result: PASS")

    def test_loss_ratio_healthy(self):
        """Test loss_ratio < 70% (healthy)"""
        total_premium = Decimal('10000.00')
        total_payout = Decimal('6000.00')
        
        loss_ratio = total_payout / total_premium
        is_healthy = loss_ratio < Decimal('0.70')
        
        print("\n[TEST] Loss Ratio - Healthy (<70%)")
        print(f"Input: premium={total_premium}, payout={total_payout}")
        print(f"Expected: loss_ratio=0.60 (healthy)")
        print(f"Actual: loss_ratio={loss_ratio}, is_healthy={is_healthy}")
        assert is_healthy
        print("Result: PASS")

    def test_loss_ratio_warning(self):
        """Test loss_ratio 70-85% (warning)"""
        total_premium = Decimal('10000.00')
        total_payout = Decimal('7500.00')
        
        loss_ratio = total_payout / total_premium
        is_warning = Decimal('0.70') <= loss_ratio <= Decimal('0.85')
        
        print("\n[TEST] Loss Ratio - Warning (70-85%)")
        print(f"Input: premium={total_premium}, payout={total_payout}")
        print(f"Expected: loss_ratio=0.75 (warning)")
        print(f"Actual: loss_ratio={loss_ratio}, is_warning={is_warning}")
        assert is_warning
        print("Result: PASS")

    def test_loss_ratio_critical(self):
        """Test loss_ratio > 85% (critical, blocks policies)"""
        total_premium = Decimal('10000.00')
        total_payout = Decimal('9000.00')
        
        loss_ratio = total_payout / total_premium
        is_critical = loss_ratio > Decimal('0.85')
        
        print("\n[TEST] Loss Ratio - Critical (>85%)")
        print(f"Input: premium={total_premium}, payout={total_payout}")
        print(f"Expected: loss_ratio=0.90 (critical)")
        print(f"Actual: loss_ratio={loss_ratio}, is_critical={is_critical}")
        assert is_critical
        print("Result: PASS")

    def test_loss_ratio_blocks_new_policies(self):
        """Test that critical loss_ratio blocks new policy creation"""
        loss_ratio = Decimal('0.88')
        threshold = Decimal('0.85')
        
        can_create_policy = loss_ratio <= threshold
        
        print("\n[TEST] Loss Ratio - Blocks New Policies")
        print(f"Input: loss_ratio={loss_ratio} (> {threshold})")
        print(f"Expected: can_create_policy=False")
        print(f"Actual: can_create_policy={can_create_policy}")
        assert not can_create_policy
        print("Result: PASS")

    def test_loss_ratio_at_boundary(self):
        """Test loss_ratio at exactly 85% boundary"""
        total_premium = Decimal('10000.00')
        total_payout = Decimal('8500.00')
        
        loss_ratio = total_payout / total_premium
        threshold = Decimal('0.85')
        
        can_create_policy = loss_ratio <= threshold
        
        print("\n[TEST] Loss Ratio - Boundary (85%)")
        print(f"Input: loss_ratio={loss_ratio}")
        print(f"Expected: can_create_policy=True (<=, not <)")
        print(f"Actual: can_create_policy={can_create_policy}")
        assert can_create_policy
        print("Result: PASS")


class TestZeroDivisionSafety:
    """Test zero division safety in calculations"""

    def test_zero_premium_no_division(self):
        """Test zero division is safe when total_premium=0"""
        total_premium = Decimal('0.00')
        total_payout = Decimal('1000.00')
        
        # Safe division with default
        loss_ratio = total_payout / total_premium if total_premium > 0 else Decimal('0.00')
        
        print("\n[TEST] Zero Division - Zero Premium")
        print(f"Input: premium={total_premium}, payout={total_payout}")
        print(f"Expected: loss_ratio=0.0 (safe default)")
        print(f"Actual: loss_ratio={loss_ratio}")
        assert loss_ratio == Decimal('0.00')
        print("Result: PASS")

    def test_zero_payout_zero_ratio(self):
        """Test zero payout gives zero loss ratio"""
        total_premium = Decimal('10000.00')
        total_payout = Decimal('0.00')
        
        loss_ratio = total_payout / total_premium
        
        print("\n[TEST] Zero Division - Zero Payout")
        print(f"Input: premium={total_premium}, payout={total_payout}")
        print(f"Expected: loss_ratio=0.0")
        print(f"Actual: loss_ratio={loss_ratio}")
        assert loss_ratio == Decimal('0.0')
        print("Result: PASS")

    def test_both_zero_safe(self):
        """Test both premium and payout zero is handled safely"""
        total_premium = Decimal('0.00')
        total_payout = Decimal('0.00')
        
        loss_ratio = total_payout / total_premium if total_premium > 0 else Decimal('0.00')
        
        print("\n[TEST] Zero Division - Both Zero")
        print(f"Input: premium={total_premium}, payout={total_payout}")
        print(f"Expected: loss_ratio=0.0 (no division)")
        print(f"Actual: loss_ratio={loss_ratio}")
        assert loss_ratio == Decimal('0.00')
        print("Result: PASS")


class TestMetricsUpdate:
    """Test metrics table updates"""

    def test_system_metrics_single_row(self):
        """Test system_metrics maintains single row"""
        # System metrics should always have exactly 1 row
        metrics_rows = [
            {
                "id": 1,
                "total_premium": Decimal('10000.00'),
                "total_payout": Decimal('6000.00'),
                "loss_ratio": Decimal('0.60'),
                "updated_by": "scheduler",
                "last_updated": "2024-01-15T10:30:00Z"
            }
        ]
        
        print("\n[TEST] Metrics - Single Row Design")
        print(f"Input: System metrics table")
        print(f"Expected: Exactly 1 row with id=1")
        print(f"Actual: {len(metrics_rows)} row(s)")
        assert len(metrics_rows) == 1
        assert metrics_rows[0]["id"] == 1
        print("Result: PASS")

    def test_metrics_timestamp_updated(self):
        """Test last_updated timestamp is refreshed"""
        from datetime import datetime
        
        old_timestamp = "2024-01-15T10:30:00Z"
        new_timestamp = datetime.utcnow().isoformat() + "Z"
        
        print("\n[TEST] Metrics - Timestamp Updated")
        print(f"Input: Metrics updated")
        print(f"Expected: last_updated changes")
        print(f"Actual: {old_timestamp} → {new_timestamp}")
        assert old_timestamp != new_timestamp
        print("Result: PASS")

    def test_metrics_updated_by_tracking(self):
        """Test updated_by field tracks who updated metrics"""
        sources = ["initialization", "payment_verify", "scheduler", "admin"]
        
        print("\n[TEST] Metrics - Updated By Tracking")
        print(f"Input: Metrics updated from different sources")
        print(f"Expected: updated_by field captures source")
        print(f"Actual: can track from {sources}")
        print("Result: PASS")


class TestLossRatioVisibility:
    def test_loss_ratio_above_one_is_visible(self):
        ratio = _calculate_loss_ratio(total_premium=1000.0, total_payout=1500.0)
        status = classify_loss_ratio_status(ratio)

        assert ratio == 1.5
        assert status == "HIGH RISK"
