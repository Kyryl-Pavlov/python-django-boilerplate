import pytest


@pytest.mark.django_db
class TestRegister:
    def test_success_returns_201(self, client):
        res = client.post(
            "/api/v1/auth/register",
            {"email": "new@example.com", "password": "Pass123!"},
            format="json",
        )
        assert res.status_code == 201
        assert res.json()["success"] is True

    def test_missing_email_returns_422(self, client):
        res = client.post(
            "/api/v1/auth/register", {"password": "Pass123!"}, format="json"
        )
        assert res.status_code == 422

    def test_missing_password_returns_422(self, client):
        res = client.post("/api/v1/auth/register", {"email": "a@b.com"}, format="json")
        assert res.status_code == 422

    def test_empty_body_returns_422(self, client):
        res = client.post("/api/v1/auth/register", {}, format="json")
        assert res.status_code == 422

    def test_duplicate_email_returns_409(self, client):
        payload = {"email": "dup@example.com", "password": "Pass123!"}
        client.post("/api/v1/auth/register", payload, format="json")
        res = client.post("/api/v1/auth/register", payload, format="json")
        assert res.status_code == 409

    def test_email_is_normalized_to_lowercase(self, client):
        client.post(
            "/api/v1/auth/register",
            {"email": "Upper@Example.COM", "password": "Pass123!"},
            format="json",
        )
        res = client.post(
            "/api/v1/auth/login",
            {"email": "upper@example.com", "password": "Pass123!"},
            format="json",
        )
        assert res.status_code == 200


@pytest.mark.django_db
class TestLogin:
    def test_success_returns_both_tokens(self, client, registered_user):
        res = client.post("/api/v1/auth/login", registered_user, format="json")
        assert res.status_code == 200
        data = res.json()["data"]
        assert "access_token" in data
        assert "refresh_token" in data

    def test_wrong_password_returns_401(self, client, registered_user):
        res = client.post(
            "/api/v1/auth/login",
            {"email": registered_user["email"], "password": "wrong"},
            format="json",
        )
        assert res.status_code == 401

    def test_unknown_email_returns_401(self, client):
        res = client.post(
            "/api/v1/auth/login",
            {"email": "nobody@example.com", "password": "Pass123!"},
            format="json",
        )
        assert res.status_code == 401

    def test_missing_fields_returns_422(self, client):
        res = client.post("/api/v1/auth/login", {}, format="json")
        assert res.status_code == 422


@pytest.mark.django_db
class TestRefresh:
    def test_success_returns_new_access_token(self, client, refresh_token):
        res = client.post(
            "/api/v1/auth/refresh",
            HTTP_AUTHORIZATION=f"Bearer {refresh_token}",
        )
        assert res.status_code == 200
        assert "access_token" in res.json()["data"]

    def test_access_token_rejected_on_refresh_endpoint(self, client, access_token):
        res = client.post(
            "/api/v1/auth/refresh",
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        assert res.status_code == 401

    def test_no_token_returns_401(self, client):
        res = client.post("/api/v1/auth/refresh")
        assert res.status_code == 401
