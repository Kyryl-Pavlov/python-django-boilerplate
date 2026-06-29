import json
import uuid
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

_SIGNED_URL = """
query($mediaId: String!) {
    signedUrl(mediaId: $mediaId) {
        success
        message
        data
    }
}
"""

_UPLOAD = """
mutation($file: Upload!) {
    uploadFile(file: $file) {
        success
        message
        data { mediaId url expiresIn }
    }
}
"""

_FAKE_KEY = "media/user/test.jpg"
_FAKE_URL = "https://s3.example.com/signed"


def _upload_file(client, auth_header=None):
    operations = json.dumps({"query": _UPLOAD, "variables": {"file": None}})
    data = {
        "operations": operations,
        "map": json.dumps({"0": ["variables.file"]}),
        "0": SimpleUploadedFile("test.jpg", b"test content", "image/jpeg"),
    }
    kwargs = {}
    if auth_header:
        kwargs["HTTP_AUTHORIZATION"] = auth_header
    return client.post("/graphql", data, **kwargs)


@pytest.mark.django_db
class TestSignedUrl:
    def test_no_auth_returns_error(self, gql):
        payload = gql(_SIGNED_URL, {"mediaId": str(uuid.uuid4())}).json()["data"][
            "signedUrl"
        ]
        assert payload["success"] is False

    def test_nonexistent_media_returns_not_found(self, gql, gql_auth_headers):
        payload = gql(
            _SIGNED_URL,
            {"mediaId": str(uuid.uuid4())},
            headers=gql_auth_headers["access"],
        ).json()["data"]["signedUrl"]
        assert payload["success"] is False
        assert "not found" in payload["message"].lower()

    def test_success_returns_url(self, client, gql, gql_auth_headers):
        access_header = gql_auth_headers["access"]["HTTP_AUTHORIZATION"]
        with (
            patch(
                "app.graphql_api.mutations.media.upload_file", return_value=_FAKE_KEY
            ),
            patch(
                "app.graphql_api.mutations.media.get_presigned_url",
                return_value=_FAKE_URL,
            ),
        ):
            upload_res = _upload_file(client, access_header)
        media_id = upload_res.json()["data"]["uploadFile"]["data"]["mediaId"]

        with patch(
            "app.graphql_api.queries.media.get_presigned_url", return_value=_FAKE_URL
        ):
            payload = gql(
                _SIGNED_URL,
                {"mediaId": media_id},
                headers=gql_auth_headers["access"],
            ).json()["data"]["signedUrl"]

        assert payload["success"] is True
        assert payload["data"] == _FAKE_URL


@pytest.mark.django_db
class TestUploadFile:
    def test_no_auth_returns_error(self, client):
        res = _upload_file(client)
        payload = res.json()["data"]["uploadFile"]
        assert payload["success"] is False

    def test_success_returns_media_payload(self, client, gql_auth_headers):
        access_header = gql_auth_headers["access"]["HTTP_AUTHORIZATION"]
        with (
            patch(
                "app.graphql_api.mutations.media.upload_file", return_value=_FAKE_KEY
            ),
            patch(
                "app.graphql_api.mutations.media.get_presigned_url",
                return_value=_FAKE_URL,
            ),
        ):
            payload = _upload_file(client, access_header).json()["data"]["uploadFile"]

        assert payload["success"] is True
        assert payload["data"]["mediaId"]
        assert payload["data"]["url"] == _FAKE_URL

    def test_s3_failure_returns_error(self, client, gql_auth_headers):
        access_header = gql_auth_headers["access"]["HTTP_AUTHORIZATION"]
        with patch(
            "app.graphql_api.mutations.media.upload_file",
            side_effect=Exception("S3 down"),
        ):
            payload = _upload_file(client, access_header).json()["data"]["uploadFile"]
        assert payload["success"] is False
