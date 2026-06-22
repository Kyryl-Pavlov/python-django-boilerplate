from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


def get_token_from_bearer(auth_header: str) -> str:
    if not auth_header or not auth_header.startswith("Bearer "):
        raise ValueError("Missing or malformed Authorization header")
    return auth_header.split(" ", 1)[1]


def verify_access_token(raw_token: str) -> str:
    try:
        token = AccessToken(raw_token)
        return str(token["user_id"])
    except TokenError as e:
        raise ValueError(str(e)) from e


def verify_refresh_token(raw_token: str) -> str:
    try:
        token = RefreshToken(raw_token)
        if token.get("token_type") != "refresh":
            raise ValueError("Not a refresh token")
        return str(token["user_id"])
    except TokenError as e:
        raise ValueError(str(e)) from e
