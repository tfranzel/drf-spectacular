from django.conf import settings as global_settings
from rest_framework import serializers

try:
    from allauth.account.app_settings import EMAIL_VERIFICATION, EmailVerificationMethod
except ImportError:
    EMAIL_VERIFICATION, EmailVerificationMethod = None, None

try:
    from rest_auth.app_settings import JWTSerializer, TokenSerializer, UserDetailsSerializer
    from rest_auth.registration.app_settings import RegisterSerializer
except ImportError:
    JWTSerializer, UserDetailsSerializer, TokenSerializer, RegisterSerializer = (None, ) * 4

from drf_spectacular.extensions import OpenApiViewExtension
from drf_spectacular.utils import extend_schema

if getattr(global_settings, 'REST_USE_JWT', False):
    AuthTokenSerializer = JWTSerializer
else:
    AuthTokenSerializer = TokenSerializer


class DRFDefaultDetailResponseSerializer(serializers.Serializer):
    detail = serializers.CharField(read_only=True, required=False)


if EmailVerificationMethod and EMAIL_VERIFICATION == EmailVerificationMethod.MANDATORY:
    class RegisterResponseSerializer(DRFDefaultDetailResponseSerializer):  # type: ignore
        pass

elif AuthTokenSerializer:
    class RegisterResponseSerializer(serializers.Serializer):  # type: ignore
        user = UserDetailsSerializer(read_only=True)
        token = AuthTokenSerializer(read_only=True)
else:
    class RegisterResponseSerializer:  # type: ignore
        pass


class RestAuthDefaultResponseView(OpenApiViewExtension):

    def view_replacement(self):

        class Fixed(self.target_class):

            @extend_schema(responses=DRFDefaultDetailResponseSerializer)
            def post(self, request, *args, **kwargs):
                pass

        return Fixed


class RestAuthLoginView(OpenApiViewExtension):
    target_class = 'rest_auth.views.LoginView'

    def view_replacement(self):

        class Fixed(self.target_class):

            @extend_schema(responses=AuthTokenSerializer)
            def post(self, request, *args, **kwargs):
                pass

        return Fixed


class RestAuthLogoutView(OpenApiViewExtension):
    target_class = 'rest_auth.views.LogoutView'

    def view_replacement(self):

        class Fixed(self.target_class):

            if getattr(global_settings, 'ACCOUNT_LOGOUT_ON_GET', None):
                @extend_schema(request=None, responses=DRFDefaultDetailResponseSerializer)
                def get(self, request, *args, **kwargs):
                    pass
            else:
                @extend_schema(exclude=True)
                def get(self, request, *args, **kwargs):
                    pass

            @extend_schema(request=None, responses=DRFDefaultDetailResponseSerializer)
            def post(self, request, *args, **kwargs):
                pass

        return Fixed


class RestAuthPasswordChangeView(RestAuthDefaultResponseView):
    target_class = 'rest_auth.views.PasswordChangeView'


class RestAuthPasswordResetView(RestAuthDefaultResponseView):
    target_class = 'rest_auth.views.PasswordResetView'


class RestAuthPasswordResetConfirmView(RestAuthDefaultResponseView):
    target_class = 'rest_auth.views.PasswordResetConfirmView'


class RestAuthRegisterView(OpenApiViewExtension):
    target_class = 'rest_auth.registration.views.RegisterView'

    def view_replacement(self):

        class Fixed(self.target_class):

            @extend_schema(
                request=RegisterSerializer,
                responses=RegisterResponseSerializer,
            )
            def post(self, request, *args, **kwargs):
                pass

        return Fixed


class RestAuthVerifyEmailView(RestAuthDefaultResponseView):
    target_class = 'rest_auth.registration.views.VerifyEmailView'
