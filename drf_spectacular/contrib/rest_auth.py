from django.conf import settings
from rest_framework import serializers

from drf_spectacular.contrib.rest_framework_simplejwt import TokenRefreshSerializerExtension
from drf_spectacular.extensions import OpenApiSerializerExtension, OpenApiViewExtension
from drf_spectacular.utils import extend_schema


def get_token_serializer_class():
    from dj_rest_auth.app_settings import JWTSerializer, TokenSerializer

    if getattr(settings, 'REST_USE_JWT', False):
        return JWTSerializer
    else:
        return TokenSerializer


class RestAuthDetailSerializer(serializers.Serializer):
    detail = serializers.CharField(read_only=True, required=False)


class RestAuthDefaultResponseView(OpenApiViewExtension):
    def view_replacement(self):
        class Fixed(self.target_class):
            @extend_schema(responses=RestAuthDetailSerializer)
            def post(self, request, *args, **kwargs):
                pass  # pragma: no cover

        return Fixed


class RestAuthLoginView(OpenApiViewExtension):
    target_class = 'dj_rest_auth.views.LoginView'

    def view_replacement(self):
        class Fixed(self.target_class):
            @extend_schema(responses=get_token_serializer_class())
            def post(self, request, *args, **kwargs):
                pass  # pragma: no cover

        return Fixed


class RestAuthLogoutView(OpenApiViewExtension):
    target_class = 'dj_rest_auth.views.LogoutView'

    def view_replacement(self):
        if getattr(settings, 'ACCOUNT_LOGOUT_ON_GET', None):
            get_schema_params = {'responses': RestAuthDetailSerializer}
        else:
            get_schema_params = {'exclude': True}

        class Fixed(self.target_class):
            @extend_schema(**get_schema_params)
            def get(self, request, *args, **kwargs):
                pass  # pragma: no cover

            @extend_schema(request=None, responses=RestAuthDetailSerializer)
            def post(self, request, *args, **kwargs):
                pass  # pragma: no cover

        return Fixed


class RestAuthPasswordChangeView(RestAuthDefaultResponseView):
    target_class = 'dj_rest_auth.views.PasswordChangeView'


class RestAuthPasswordResetView(RestAuthDefaultResponseView):
    target_class = 'dj_rest_auth.views.PasswordResetView'


class RestAuthPasswordResetConfirmView(RestAuthDefaultResponseView):
    target_class = 'dj_rest_auth.views.PasswordResetConfirmView'


class RestAuthVerifyEmailView(RestAuthDefaultResponseView):
    target_class = 'dj_rest_auth.registration.views.VerifyEmailView'


class RestAuthResendEmailVerificationView(RestAuthDefaultResponseView):
    target_class = 'dj_rest_auth.registration.views.ResendEmailVerificationView'


class RestAuthJWTSerializer(OpenApiSerializerExtension):
    target_class = 'dj_rest_auth.serializers.JWTSerializer'

    def map_serializer(self, auto_schema, direction):
        from dj_rest_auth.app_settings import UserDetailsSerializer

        class Fixed(self.target_class):
            user = UserDetailsSerializer()

        return auto_schema._map_serializer(Fixed, direction)


class CookieTokenRefreshSerializerExtension(TokenRefreshSerializerExtension):
    target_class = 'dj_rest_auth.jwt_auth.CookieTokenRefreshSerializer'

    def get_name(self):
        return 'TokenRefresh'


class RestAuthRegisterView(OpenApiViewExtension):
    target_class = 'dj_rest_auth.registration.views.RegisterView'

    def view_replacement(self):
        from allauth.account.app_settings import EMAIL_VERIFICATION, EmailVerificationMethod

        if EMAIL_VERIFICATION == EmailVerificationMethod.MANDATORY:
            response_serializer = RestAuthDetailSerializer
        else:
            response_serializer = get_token_serializer_class()

        class Fixed(self.target_class):
            @extend_schema(responses=response_serializer)
            def post(self, request, *args, **kwargs):
                pass  # pragma: no cover

        return Fixed
