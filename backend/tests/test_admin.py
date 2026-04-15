"""
Admin authentication and authorization tests.
"""

from unittest.mock import MagicMock, patch

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
        user_token = create_access_token(
            user_id="user-123",
            phone="8888888888",
            role="user",
            email="user@guardgig.com",
        )

        admin_row = {
            "id": "admin-123",
            "full_name": "GuardGig Admin",
            "email": "admin@guardgig.com",
            "phone": "9999999999",
            "role": "admin",
        }
        user_row = {
            "id": "user-123",
            "full_name": "Normal User",
            "email": "user@guardgig.com",
            "phone": "8888888888",
            "role": "user",
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
        ) as mock_route_admin:
            mock_dep_admin.return_value = mock_admin
            mock_route_admin.return_value = mock_admin

            mock_admin.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.side_effect = [
                MagicMock(data=[admin_row]),
                MagicMock(data=[admin_row]),
                MagicMock(data=[metrics_row]),
            ]

            admin_response = client.get(
                "/api/admin/metrics",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert admin_response.status_code == 200
            admin_body = admin_response.json()
            assert admin_body["total_premium"] == 12000.0
            assert admin_body["status"] == "healthy"

        with patch("app.dependencies.get_admin_client") as mock_dep_admin, patch(
            "app.routes.admin.get_admin_client"
        ) as mock_route_admin:
            mock_dep_admin.return_value = mock_admin
            mock_route_admin.return_value = mock_admin

            mock_admin.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.side_effect = [
                MagicMock(data=[user_row]),
                MagicMock(data=[user_row]),
            ]

            user_response = client.get(
                "/api/admin/metrics",
                headers={"Authorization": f"Bearer {user_token}"},
            )

            assert user_response.status_code == 403

    def test_admin_predictions_admin_only(self, client, mock_admin):
        admin_token = create_access_token(
            user_id="admin-123",
            phone="9999999999",
            role="admin",
            email="admin@guardgig.com",
        )
        user_token = create_access_token(
            user_id="user-123",
            phone="8888888888",
            role="user",
            email="user@guardgig.com",
        )

        admin_row = {
            "id": "admin-123",
            "full_name": "GuardGig Admin",
            "email": "admin@guardgig.com",
            "phone": "9999999999",
            "role": "admin",
        }
        user_row = {
            "id": "user-123",
            "full_name": "Normal User",
            "email": "user@guardgig.com",
            "phone": "8888888888",
            "role": "user",
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
        ) as mock_route_admin:
            mock_dep_admin.return_value = mock_admin
            mock_route_admin.return_value = mock_admin

            mock_admin.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.side_effect = [
                MagicMock(data=[admin_row]),
                MagicMock(data=[admin_row]),
                MagicMock(data=[metrics_row]),
            ]

            admin_response = client.get(
                "/api/admin/predictions",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert admin_response.status_code == 200
            admin_body = admin_response.json()
            assert admin_body["next_week_risk"] == "LOW"
            assert admin_body["risk_score"] == 0.5

        with patch("app.dependencies.get_admin_client") as mock_dep_admin, patch(
            "app.routes.admin.get_admin_client"
        ) as mock_route_admin:
            mock_dep_admin.return_value = mock_admin
            mock_route_admin.return_value = mock_admin

            mock_admin.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.side_effect = [
                MagicMock(data=[user_row]),
                MagicMock(data=[user_row]),
            ]

            user_response = client.get(
                "/api/admin/predictions",
                headers={"Authorization": f"Bearer {user_token}"},
            )

            assert user_response.status_code == 403
