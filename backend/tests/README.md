# GuardGig Backend Test Suite

## Overview

This is a comprehensive test suite for the GuardGig backend system. It covers:

- **Authentication & User Management**: Registration, login, token validation
- **Policy Management**: Creation, validation, expiration handling
- **Payment Processing**: Razorpay integration, signature verification, replay attack prevention
- **Trigger Logic**: Weather-based parametric insurance (AQI, rainfall)
- **Claim Generation**: Automated claims, payout calculation, rule enforcement
- **Fraud Detection**: Fraud scoring, threshold enforcement, exclusions
- **Metrics & Actuarial**: Loss ratio tracking, policy blocking, zero-division safety
- **Scheduler**: Automated job execution, idempotency, metrics updates
- **Edge Cases**: Expired/inactive policies, missing data, invalid inputs, extreme values
- **Adversarial**: Fake payments, duplicate claims, rapid runs, replay attacks

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                 # Pytest fixtures and test configuration
├── test_auth.py               # Authentication tests
├── test_policy.py             # Policy management tests
├── test_payment.py            # Razorpay payment tests
├── test_trigger.py            # Weather trigger logic tests
├── test_claims.py             # Claim generation and payout tests
├── test_fraud.py              # Fraud detection tests
├── test_metrics.py            # Metrics and actuarial tests
├── test_scheduler.py          # Scheduler and background job tests
├── test_edge_cases.py         # Edge case and adversarial tests
└── run_all_tests.py           # Comprehensive test runner
```

## Installation

### Prerequisites

- Python 3.8+
- FastAPI/Starlette (already in backend)
- pytest
- pytest-asyncio (for async tests)

### Setup

```bash
# Navigate to backend directory
cd backend

# Install test dependencies
pip install pytest pytest-asyncio

# Optional: Install for HTML reports
pip install pytest-html
```

## Running Tests

### Run All Tests

```bash
# Standard output
python -m pytest tests/ -v

# Or use the test runner
python tests/run_all_tests.py

# Verbose output
python tests/run_all_tests.py -v

# Generate HTML report
python tests/run_all_tests.py --html
```

### Run Specific Test Module

```bash
# Authentication tests only
python -m pytest tests/test_auth.py -v

# Policy tests only
python -m pytest tests/test_policy.py -v

# Payment tests only
python -m pytest tests/test_payment.py -v
```

### Run Specific Test Class

```bash
# Test class
python -m pytest tests/test_auth.py::TestAuthenticationFlow -v

# Specific test method
python -m pytest tests/test_auth.py::TestAuthenticationFlow::test_register_user_success -v
```

### Run with Coverage

```bash
# Install coverage
pip install pytest-cov

# Run with coverage report
python -m pytest tests/ --cov=app --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html
```

## Test Coverage

### Layer 1: API-Level Tests

- **test_auth.py**: HTTP endpoint testing
  - `POST /api/auth/register` - Valid/invalid inputs
  - `POST /api/auth/login` - Correct/incorrect credentials
  - Protected endpoint authentication

- **test_policy.py**: Policy API tests
  - `POST /api/policy/create` - Valid creation, blocked by loss_ratio
  - Policy status transitions
  - Expiration handling

- **test_payment.py**: Razorpay API tests
  - `POST /api/payment/create-order` - Order creation
  - `POST /api/payment/verify` - Signature verification
  - Replay attack prevention

- **test_trigger.py**: Trigger check API tests
  - `POST /api/check` - Weather trigger evaluation
  - Multi-trigger logic

### Layer 2: Service-Level Tests

- **test_claims.py**: Claim generation logic
  - Payout calculation accuracy
  - Rule enforcement (daily limit, waiting period)
  - Status transitions

- **test_fraud.py**: Fraud detection service
  - Fraud score heuristics
  - Threshold enforcement
  - Exclusion rules

- **test_metrics.py**: Metrics calculation
  - Premium/payout accumulation
  - Loss ratio recalculation
  - Zero-division safety

- **test_scheduler.py**: Scheduler logic
  - Automated claim generation
  - Idempotency checks
  - Metrics updates

### Layer 3: Edge Cases & Adversarial

- **test_edge_cases.py**: Comprehensive edge case coverage
  - Expired/inactive policies
  - Missing/invalid data
  - Extreme values
  - Concurrent requests
  - Replay attacks
  - Rapid scheduler runs

## Test Data & Fixtures

All fixtures defined in `conftest.py`:

```python
# User fixtures
- test_user_data           # Registration data
- test_user_with_id        # User in database
- test_onboarding_data     # Onboarding profile
- test_onboarding_complete # Complete onboarding

# Policy fixtures
- test_policy_data         # Policy creation request
- test_policy_active       # Active policy in database

# Payment fixtures
- razorpay_mock_keys       # Test keys
- razorpay_payment_valid   # Valid signature
- razorpay_payment_invalid # Invalid signature

# Data fixtures
- test_location_data       # City coordinates
- trigger_test_cases       # Parametrized trigger tests
- fraud_test_cases         # Parametrized fraud tests
- claim_test_cases         # Parametrized claim tests
```

## Sample Output

```
================================================================================
                    GUARDGIG BACKEND TEST SUITE
================================================================================
Start Time: 2024-01-15 10:30:45
Test Directory: tests
================================================================================

────────────────────────────────────────────────────────────────────────────────
Running: test_auth.py
────────────────────────────────────────────────────────────────────────────────
✓ test_auth.py - PASSED

────────────────────────────────────────────────────────────────────────────────
Running: test_policy.py
────────────────────────────────────────────────────────────────────────────────
✓ test_policy.py - PASSED

...

================================================================================
                           TEST SUMMARY REPORT
================================================================================
Execution Time: 2024-01-15 10:35:22

  Total Tests Run:        127
  ✓ Passed:              125
  ✗ Failed:              2
  ⚠ Errors:              0
  ⊘ Skipped:             0

  Success Rate:          98.4%

MODULE RESULTS:
────────────────────────────────────────────────────────────────────────────────
  ✓ PASS      test_auth.py
  ✓ PASS      test_policy.py
  ✓ PASS      test_payment.py
  ✓ PASS      test_trigger.py
  ✓ PASS      test_claims.py
  ✓ PASS      test_fraud.py
  ✓ PASS      test_metrics.py
  ✓ PASS      test_scheduler.py
  ✓ PASS      test_edge_cases.py
================================================================================

Exit Code: 0
```

## Key Testing Patterns

### 1. Parametrized Tests

```python
@pytest.mark.parametrize("rain,aqi,triggered,payout", [
    (160, 250, True, 100),
    (30, 320, True, 30),
    (30, 250, False, 0),
])
def test_trigger_thresholds(self, rain, aqi, triggered, payout):
    # Test multiple scenarios with single function
```

### 2. Mock Database

```python
with patch('app.routes.auth.get_db') as mock_db:
    mock_db.return_value = mock_admin
    mock_admin.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[test_user_data]
    )
    # Now test API call
```

### 3. Async Testing

```python
@pytest.mark.asyncio
async def test_concurrent_requests(self):
    results = await asyncio.gather(*[
        async_function_1(),
        async_function_2(),
    ])
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - run: pip install -r backend/requirements.txt pytest pytest-asyncio
      - run: cd backend && python -m pytest tests/ -v --cov=app
```

## Troubleshooting

### Import Errors

If you get import errors, ensure:
1. You're in the `backend/` directory
2. Backend dependencies are installed: `pip install -r requirements.txt`
3. Python path includes backend: `export PYTHONPATH=.`

### AsyncIO Errors

For async test issues:
```bash
pip install pytest-asyncio
```

### Supabase Mock Issues

The suite mocks Supabase calls. If you need real database testing:
1. Create test database
2. Set environment variables
3. Use `@pytest.mark.integration` marker for real DB tests

## Extending Tests

### Add New Test Module

1. Create `tests/test_feature.py`
2. Import fixtures from `conftest.py`
3. Write test classes and methods
4. Run: `python -m pytest tests/test_feature.py -v`

### Add New Fixture

Edit `conftest.py`:

```python
@pytest.fixture
def my_fixture():
    """Description of fixture"""
    return {"key": "value"}

# Use in test:
def test_something(self, my_fixture):
    assert my_fixture["key"] == "value"
```

## Performance Testing (Bonus)

For load testing, use `locust`:

```bash
pip install locust
```

Create `tests/locustfile.py` for traffic simulation.

## Best Practices

1. ✅ Keep tests isolated and independent
2. ✅ Use fixtures for common setup
3. ✅ Mock external services (Razorpay, weather APIs)
4. ✅ Test both happy path and error cases
5. ✅ Use parametrized tests for threshold testing
6. ✅ Document complex test logic
7. ✅ Keep tests fast (<5s each)
8. ✅ Use clear assertion messages
9. ✅ Version control test data
10. ✅ Review coverage regularly

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/advanced/testing-events/)
- [Mock Library](https://docs.python.org/3/library/unittest.mock.html)
- [Parametrize Tests](https://docs.pytest.org/en/latest/example/parametrize.html)

---

**Last Updated**: January 2024
**Test Suite Version**: 1.0
**Coverage**: 127+ test cases across 9 modules
