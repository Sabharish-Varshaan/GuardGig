"""
Authentication API tests
"""

from unittest.mock import MagicMock, patch


class TestAuthRoutes:
    def test_register_success(self, client, mock_admin):
        with patch("app.routes.auth.get_admin_client") as mock_get:
            mock_get.return_value = mock_admin
            # Existing user check -> no user
            mock_admin.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(data=[])

            payload = {
                "full_name": "Test User",
                "phone": "9876543210",
                "password": "SecurePass123!",
            }
            response = client.post("/api/auth/register", json=payload)

            assert response.status_code in (200, 201)
            body = response.json()
            assert "access_token" in body
            assert "refresh_token" in body
            assert "user_id" in body

    def test_register_duplicate_phone(self, client, mock_admin):
        with patch("app.routes.auth.get_admin_client") as mock_get:
            mock_get.return_value = mock_admin
            # Existing user check -> already exists
            mock_admin.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[{"id": "u1"}]
            )

            payload = {
                "full_name": "Test User",
                "phone": "9876543210",
                "password": "SecurePass123!",
            }
            response = client.post("/api/auth/register", json=payload)

            assert response.status_code == 409

    def test_login_success(self, client, mock_admin):
        from app.auth_utils import hash_password

        with patch("app.routes.auth.get_admin_client") as mock_get:
            mock_get.return_value = mock_admin

            # First execute: login user lookup
            # Second execute: onboarding status lookup
            mock_admin.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.side_effect = [
                MagicMock(data=[{"id": "test-user-123", "phone": "9876543210", "password_hash": hash_password("SecurePass123!")}]),
                MagicMock(data=[{"onboarding_completed": True}]),
            ]

            payload = {"phone": "9876543210", "password": "SecurePass123!"}
            response = client.post("/api/auth/login", json=payload)

            assert response.status_code == 200
            body = response.json()
            assert "access_token" in body
            assert "refresh_token" in body
            assert body.get("onboarding_completed") is True

    def test_login_invalid_password(self, client, mock_admin):
        from app.auth_utils import hash_password

        with patch("app.routes.auth.get_admin_client") as mock_get:
            mock_get.return_value = mock_admin
            mock_admin.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[{"id": "test-user-123", "phone": "9876543210", "password_hash": hash_password("AnotherPass123!")}]
            )

            payload = {"phone": "9876543210", "password": "SecurePass123!"}
            response = client.post("/api/auth/login", json=payload)

            assert response.status_code == 401

    def test_login_user_not_found(self, client, mock_admin):
        with patch("app.routes.auth.get_admin_client") as mock_get:
            mock_get.return_value = mock_admin
            mock_admin.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(data=[])

            payload = {"phone": "9876543210", "password": "SecurePass123!"}
            response = client.post("/api/auth/login", json=payload)

            assert response.status_code == 401
