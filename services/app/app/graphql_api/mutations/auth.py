import graphene
from django.db import IntegrityError
from rest_framework_simplejwt.tokens import RefreshToken

from app.graphql_api.types import AuthPayloadType, AuthResponse, StringResponse
from app.graphql_api.utils import get_token_from_bearer, verify_refresh_token
from app.models import User


class Register(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    Output = StringResponse

    def mutate(self, info, email, password):
        email = email.lower().strip()
        if not password:
            return StringResponse(success=False, message="Password is required")
        try:
            User.objects.create_user(email=email, password=password)
        except IntegrityError:
            return StringResponse(success=False, message="Email already registered")
        except Exception as e:
            return StringResponse(success=False, message=str(e))
        return StringResponse(success=True, message="User registered successfully")


class Login(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    Output = AuthResponse

    def mutate(self, info, email, password):
        email = email.lower().strip()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return AuthResponse(success=False, message="Invalid credentials")

        if not user.check_password(password):
            return AuthResponse(success=False, message="Invalid credentials")

        refresh = RefreshToken.for_user(user)
        return AuthResponse(
            success=True,
            message="Login successful",
            data=AuthPayloadType(
                access_token=str(refresh.access_token),
                refresh_token=str(refresh),
            ),
        )


class RefreshTokenMutation(graphene.Mutation):
    class Arguments:
        pass

    Output = AuthResponse

    def mutate(self, info):
        auth_header = info.context["request"].META.get("HTTP_AUTHORIZATION", "")
        try:
            raw_token = get_token_from_bearer(auth_header)
            verify_refresh_token(raw_token)
            from rest_framework_simplejwt.tokens import RefreshToken as RT

            refresh = RT(raw_token)
            new_access = str(refresh.access_token)
        except ValueError as e:
            return AuthResponse(success=False, message=str(e))

        return AuthResponse(
            success=True,
            message="Token refreshed",
            data=AuthPayloadType(access_token=new_access),
        )


class AuthMutations(graphene.ObjectType):
    register = Register.Field()
    login = Login.Field()
    refresh_token = RefreshTokenMutation.Field()
