import uuid
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

_FAKE_S3_KEY = "media/user-id/test.jpg"
_FAKE_URL = "https://s3.example.com/signed-url"


def _upload(client, auth_headers, content=b"hello", filename="test.jpg"):
    with (
        patch("app.api.v1.views.media.upload_file", return_value=_FAKE_S3_KEY),
        patch("app.api.v1.views.media.get_presigned_url", return_value=_FAKE_URL),
    ):
        return client.post(
            "/api/v1/media/upload",
            {"file": SimpleUploadedFile(filename, content, "image/jpeg")},
            format="multipart",
            **auth_headers,
        )


@pytest.mark.django_db
class TestUpload:
    def test_no_auth_returns_401(self, client):
        res = client.post("/api/v1/media/upload")
        assert res.status_code == 401

    def test_no_file_returns_400(self, client, auth_headers):
        res = client.post("/api/v1/media/upload", **auth_headers)
        assert res.status_code == 400

    def test_success_returns_201_with_media_id_and_url(self, client, auth_headers):
        res = _upload(client, auth_headers)
        assert res.status_code == 201
        data = res.json()["data"]
        assert "media_id" in data
        assert data["url"] == _FAKE_URL

    def test_media_record_persisted_in_db(self, client, auth_headers):
        from app.models import Media

        res = _upload(client, auth_headers)
        media_id = res.json()["data"]["media_id"]
        record = Media.objects.get(id=media_id)
        assert record.content_key == _FAKE_S3_KEY

    def test_s3_failure_returns_500(self, client, auth_headers):
        with patch(
            "app.api.v1.views.media.upload_file", side_effect=Exception("S3 down")
        ):
            res = client.post(
                "/api/v1/media/upload",
                {"file": SimpleUploadedFile("test.jpg", b"data", "image/jpeg")},
                format="multipart",
                **auth_headers,
            )
        assert res.status_code == 500


@pytest.mark.django_db
class TestGetUrl:
    def test_no_auth_returns_401(self, client):
        res = client.get(f"/api/v1/media/{uuid.uuid4()}/url")
        assert res.status_code == 401

    def test_nonexistent_media_returns_404(self, client, auth_headers):
        res = client.get(f"/api/v1/media/{uuid.uuid4()}/url", **auth_headers)
        assert res.status_code == 404

    def test_success_returns_presigned_url(self, client, auth_headers):
        media_id = _upload(client, auth_headers).json()["data"]["media_id"]

        with patch("app.api.v1.views.media.get_presigned_url", return_value=_FAKE_URL):
            res = client.get(f"/api/v1/media/{media_id}/url", **auth_headers)

        assert res.status_code == 200
        assert res.json()["data"]["url"] == _FAKE_URL

    def test_another_users_media_returns_404(self, client):
        client.post(
            "/api/v1/auth/register",
            {"email": "u1@x.com", "password": "Pass1!"},
            format="json",
        )
        client.post(
            "/api/v1/auth/register",
            {"email": "u2@x.com", "password": "Pass2!"},
            format="json",
        )

        token1 = client.post(
            "/api/v1/auth/login",
            {"email": "u1@x.com", "password": "Pass1!"},
            format="json",
        ).json()["data"]["access_token"]
        token2 = client.post(
            "/api/v1/auth/login",
            {"email": "u2@x.com", "password": "Pass2!"},
            format="json",
        ).json()["data"]["access_token"]

        media_id = _upload(client, {"HTTP_AUTHORIZATION": f"Bearer {token1}"}).json()[
            "data"
        ]["media_id"]

        res = client.get(
            f"/api/v1/media/{media_id}/url", HTTP_AUTHORIZATION=f"Bearer {token2}"
        )
        assert res.status_code == 404
