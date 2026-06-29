from django.db import IntegrityError
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from app.api.utils import api_response
from app.api.v1.serializers.auth import LoginSerializer, RegisterSerializer
from app.models import User


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(False, "Invalid input", status_code=422)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        try:
            User.objects.create_user(email=email, password=password)
        except IntegrityError:
            return api_response(False, "Email already registered", status_code=409)

        return api_response(True, "User registered successfully", status_code=201)


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(False, "Invalid input", status_code=422)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return api_response(False, "Invalid credentials", status_code=401)

        if not user.check_password(password):
            return api_response(False, "Invalid credentials", status_code=401)

        refresh = RefreshToken.for_user(user)
        return api_response(
            True,
            "Login successful",
            data={
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
            },
        )


class RefreshView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return api_response(False, "Missing refresh token", status_code=401)

        raw_token = auth_header.split(" ", 1)[1]
        try:
            refresh = RefreshToken(raw_token)
            if refresh.get("token_type") != "refresh":
                raise TokenError("Not a refresh token")
            new_access = str(refresh.access_token)
        except TokenError:
            return api_response(
                False, "Invalid or expired refresh token", status_code=401
            )

        return api_response(True, "Token refreshed", data={"access_token": new_access})
