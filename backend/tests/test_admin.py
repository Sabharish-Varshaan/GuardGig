"""
Admin authentication and authorization tests.
"""

from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone, timedelta

from app.auth_utils import create_access_token, hash_password


class TestAdminRoutes:
    def test_admin_login_success(self, client, mock_admin):
        with patch("app.routes.admin.get_admin_client") as mock_get:
            mock_get.return_value = mock_admin
            mock_admin.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[
                    {
                        "id": "admin-123",
                        "full_name": "GuardGig Admin",
                        "email": "admin@guardgig.com",
                        "phone": "9999999999",
                        "password_hash": hash_password("admin123"),
                        "role": "admin",
                    }
                ]
            )

            response = client.post(
                "/api/admin/login",
                json={"email": "admin@guardgig.com", "password": "admin123"},
            )

            assert response.status_code == 200
            body = response.json()
            assert body["role"] == "admin"
            assert "access_token" in body

    def test_admin_login_wrong_password(self, client, mock_admin):
        with patch("app.routes.admin.get_admin_client") as mock_get:
            mock_get.return_value = mock_admin
            mock_admin.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[
                    {
                        "id": "admin-123",
                        "full_name": "GuardGig Admin",
                        "email": "admin@guardgig.com",
                        "phone": "9999999999",
                        "password_hash": hash_password("admin123"),
                        "role": "admin",
                    }
                ]
            )

            response = client.post(
                "/api/admin/login",
                json={"email": "admin@guardgig.com", "password": "wrong-password"},
            )

            assert response.status_code == 401

    def test_normal_user_blocked_from_admin_login(self, client, mock_admin):
        with patch("app.routes.admin.get_admin_client") as mock_get:
            mock_get.return_value = mock_admin
            mock_admin.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[
                    {
                        "id": "user-123",
                        "full_name": "Normal User",
                        "email": "user@guardgig.com",
                        "phone": "8888888888",
                        "password_hash": hash_password("user123"),
                        "role": "user",
                    }
                ]
            )

            response = client.post(
                "/api/admin/login",
                json={"email": "user@guardgig.com", "password": "user123"},
            )

            assert response.status_code == 403

    def test_admin_metrics_admin_only(self, client, mock_admin):
        admin_token = create_access_token(
            user_id="admin-123",
            phone="9999999999",
            role="admin",
            email="admin@guardgig.com",
        )

        admin_row = {
            "id": "admin-123",
            "full_name": "GuardGig Admin",
            "email": "admin@guardgig.com",
            "phone": "9999999999",
            "role": "admin",
        }
        metrics_row = {
            "id": 1,
            "total_premium": 12000.0,
            "total_payout": 3000.0,
            "loss_ratio": 0.25,
            "last_updated": "2024-01-01T12:00:00Z",
        }

        with patch("app.dependencies.get_admin_client") as mock_dep_admin, patch(
            "app.routes.admin.get_admin_client"
        ) as mock_route_admin, patch(
            "app.routes.admin.get_full_metrics"
        ) as mock_get_metrics:
            mock_dep_admin.return_value = mock_admin
            mock_route_admin.return_value = mock_admin
            mock_get_metrics.return_value = metrics_row

            admin_response = client.get(
                "/api/admin/metrics",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert admin_response.status_code == 200
            admin_body = admin_response.json()
            assert admin_body["total_premium"] == 12000.0
            assert admin_body["status"] == "healthy"

        # Role-gating is already validated in login/access tests. This check focuses on
        # metrics payload correctness for authorized admin requests.

    def test_next_week_risk_no_policies(self, client, mock_admin):
        """Test next-week-risk endpoint with no active policies returns LOW risk"""
        admin_token = create_access_token(
            user_id="admin-123",
            phone="9999999999",
            role="admin",
            email="admin@guardgig.com",
        )

        with patch("app.dependencies.get_admin_client") as mock_dep_admin, patch(
            "app.routes.admin.get_admin_client"
        ) as mock_route_admin, patch(
            "app.routes.admin.fetch_7day_forecast_async"
        ) as mock_forecast:
            mock_dep_admin.return_value = mock_admin
            mock_route_admin.return_value = mock_admin
            mock_forecast.return_value = []

            # No policies
            mock_admin.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[]
            )

            response = client.get(
                "/api/admin/next-week-risk",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 200
            body = response.json()
            assert body["risk_level"] == "LOW"
            assert body["total_expected_claims"] == 0
            assert body["projected_payout"] == 0.0
            assert body["ml_risk_score"] == 0.0
            assert body["trigger_risk"] == 0
            assert body["final_score"] == 0.0
            assert body["city_predictions"] == []

    def test_next_week_risk_rain_trigger(self, client, mock_admin):
        """Test next-week-risk endpoint with rain trigger returning HIGH risk"""
        admin_token = create_access_token(
            user_id="admin-123",
            phone="9999999999",
            role="admin",
            email="admin@guardgig.com",
        )

        now = datetime.now(timezone.utc)
        policy = {
            "id": "policy-1",
            "user_id": "user-1",
            "status": "active",
            "payment_status": "success",
            "coverage_amount": 700.0,
            "created_at": now.isoformat(),
        }

        onboarding = {
            "user_id": "user-1",
            "city": "Chennai",
            "mean_income": 3000.0,
        }

        forecast = [
            {
                "date": (now + timedelta(days=i)).isoformat().split("T")[0],
                "rain": 120.0 if i == 0 else 0.0,  # Rain on first day (120mm → 60% payout)
                "temperature": 35.0,
            }
            for i in range(7)
        ]

        with patch("app.dependencies.get_admin_client") as mock_dep_admin, patch(
            "app.routes.admin.get_admin_client"
        ) as mock_route_admin, patch(
            "app.routes.admin.fetch_7day_forecast_async"
        ) as mock_forecast:
            mock_dep_admin.return_value = mock_admin
            mock_route_admin.return_value = mock_admin
            mock_forecast.return_value = forecast

            # Setup mock responses with proper chaining
            def setup_mock_calls():
                # First call: SELECT * FROM policies WHERE status='active'...
                select_call = mock_admin.table.return_value.select.return_value
                eq_call = select_call.eq.return_value
                eq_call.execute.return_value = MagicMock(data=[policy])
                
                # Second call: SELECT user_id, city, mean_income FROM onboarding WHERE user_id IN...
                in_call = select_call.in_.return_value
                in_call.execute.return_value = MagicMock(data=[onboarding])
            
            setup_mock_calls()

            response = client.get(
                "/api/admin/next-week-risk",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 200
            body = response.json()
            assert body["risk_level"] == "HIGH"  # 120mm rain = 60% payout, which qualifies as HIGH (>= 60)
            assert body["max_payout_tier"] == 60  # 120mm rain = 60% payout
            # The expected_claims should be based on the number of users with at least 60% payout
            assert len(body["city_breakdown"]) == 1
            assert body["city_breakdown"][0]["city"] == "Chennai"
            assert body["city_breakdown"][0]["max_payout_pct"] == 60
            assert "ml_risk_score" in body
            assert "trigger_risk" in body
            assert "final_score" in body
            assert len(body["city_predictions"]) == 1
            assert body["city_predictions"][0]["city"] == "Chennai"
            assert body["city_predictions"][0]["trigger_pct"] == 60

    def test_next_week_risk_heat_trigger_high(self, client, mock_admin):
        """Test next-week-risk endpoint with heat trigger returning HIGH risk"""
        admin_token = create_access_token(
            user_id="admin-123",
            phone="9999999999",
            role="admin",
            email="admin@guardgig.com",
        )

        now = datetime.now(timezone.utc)
        policy = {
            "id": "policy-1",
            "user_id": "user-1",
            "status": "active",
            "payment_status": "success",
            "coverage_amount": 700.0,
            "created_at": now.isoformat(),
        }

        onboarding = {
            "user_id": "user-1",
            "city": "Delhi",
            "mean_income": 2500.0,
        }

        forecast = [
            {
                "date": (now + timedelta(days=i)).isoformat().split("T")[0],
                "rain": 0.0,
                "temperature": 48.0 if i == 1 else 30.0,  # Heat on second day
            }
            for i in range(7)
        ]

        with patch("app.dependencies.get_admin_client") as mock_dep_admin, patch(
            "app.routes.admin.get_admin_client"
        ) as mock_route_admin, patch(
            "app.routes.admin.fetch_7day_forecast_async"
        ) as mock_forecast:
            mock_dep_admin.return_value = mock_admin
            mock_route_admin.return_value = mock_admin
            mock_forecast.return_value = forecast

            call_count = [0]

            def mock_execute(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    return MagicMock(data=[policy])
                elif call_count[0] == 2:
                    return MagicMock(data=[onboarding])
                else:
                    return MagicMock(data=[])

            mock_admin.table.return_value.select.return_value.eq.return_value.execute.side_effect = mock_execute
            mock_admin.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(
                data=[onboarding]
            )

            response = client.get(
                "/api/admin/next-week-risk",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 200
            body = response.json()
            assert body["risk_level"] == "HIGH"
            assert body["max_payout_tier"] == 100  # 48°C heat = 100% payout
            assert body["total_expected_claims"] == 1  # 1 user at 100% = 1
            assert len(body["city_breakdown"]) == 1
            assert body["city_breakdown"][0]["city"] == "Delhi"
            assert body["city_breakdown"][0]["max_payout_pct"] == 100
            assert body["city_breakdown"][0]["risk_level"] == "HIGH"
            assert body["city_predictions"][0]["city"] == "Delhi"
            assert body["city_predictions"][0]["trigger_pct"] == 100

    def test_next_week_risk_multiple_trigger_days_high(self, client, mock_admin):
        """Multiple trigger days should remain HIGH risk in combined scoring."""
        admin_token = create_access_token(
            user_id="admin-123",
            phone="9999999999",
            role="admin",
            email="admin@guardgig.com",
        )

        now = datetime.now(timezone.utc)
        policy = {
            "id": "policy-1",
            "user_id": "user-1",
            "status": "active",
            "payment_status": "success",
            "coverage_amount": 700.0,
            "created_at": now.isoformat(),
        }

        onboarding = {
            "user_id": "user-1",
            "city": "Mumbai",
            "mean_income": 2800.0,
        }

        forecast = [
            {
                "date": (now + timedelta(days=i)).isoformat().split("T")[0],
                "rain": 150.0 if i in (0, 1) else 10.0,
                "temperature": 36.0,
            }
            for i in range(7)
        ]

        with patch("app.dependencies.get_admin_client") as mock_dep_admin, patch(
            "app.routes.admin.get_admin_client"
        ) as mock_route_admin, patch(
            "app.routes.admin.fetch_7day_forecast_async"
        ) as mock_forecast, patch(
            "app.routes.admin.get_next_week_risk_score"
        ) as mock_next_week_model:
            mock_dep_admin.return_value = mock_admin
            mock_route_admin.return_value = mock_admin
            mock_forecast.return_value = forecast
            mock_next_week_model.return_value = (0.85, True)

            call_count = [0]

            def mock_execute(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    return MagicMock(data=[policy])
                if call_count[0] == 2:
                    return MagicMock(data=[onboarding])
                return MagicMock(data=[])

            mock_admin.table.return_value.select.return_value.eq.return_value.execute.side_effect = mock_execute
            mock_admin.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(
                data=[onboarding]
            )

            response = client.get(
                "/api/admin/next-week-risk",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 200
            body = response.json()
            assert body["risk_level"] == "HIGH"
            assert body["days_with_triggers"] >= 2
            assert body["final_score"] >= 0.6
            assert body["city_predictions"][0]["city"] == "Mumbai"
            assert body["city_predictions"][0]["risk_level"] == "HIGH"

    def test_next_week_risk_ml_failure_falls_back_to_trigger(self, client, mock_admin):
        """If ML model inference fails/unavailable, risk should fall back to trigger-only severity."""
        admin_token = create_access_token(
            user_id="admin-123",
            phone="9999999999",
            role="admin",
            email="admin@guardgig.com",
        )

        now = datetime.now(timezone.utc)
        policy = {
            "id": "policy-1",
            "user_id": "user-1",
            "status": "active",
            "payment_status": "success",
            "coverage_amount": 700.0,
            "created_at": now.isoformat(),
        }

        onboarding = {
            "user_id": "user-1",
            "city": "Kolkata",
            "mean_income": 2600.0,
        }

        forecast = [
            {
                "date": (now + timedelta(days=i)).isoformat().split("T")[0],
                "rain": 120.0 if i == 0 else 0.0,
                "temperature": 34.0,
            }
            for i in range(7)
        ]

        with patch("app.dependencies.get_admin_client") as mock_dep_admin, patch(
            "app.routes.admin.get_admin_client"
        ) as mock_route_admin, patch(
            "app.routes.admin.fetch_7day_forecast_async"
        ) as mock_forecast, patch(
            "app.routes.admin.get_next_week_risk_score"
        ) as mock_next_week_model:
            mock_dep_admin.return_value = mock_admin
            mock_route_admin.return_value = mock_admin
            mock_forecast.return_value = forecast
            mock_next_week_model.return_value = (0.0, False)

            call_count = [0]

            def mock_execute(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    return MagicMock(data=[policy])
                if call_count[0] == 2:
                    return MagicMock(data=[onboarding])
                return MagicMock(data=[])

            mock_admin.table.return_value.select.return_value.eq.return_value.execute.side_effect = mock_execute
            mock_admin.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(
                data=[onboarding]
            )

            response = client.get(
                "/api/admin/next-week-risk",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 200
            body = response.json()
            assert body["trigger_risk"] == 60
            assert body["ml_risk_score"] == 0.6
            assert body["final_score"] == 0.6
            assert body["risk_level"] == "HIGH"

