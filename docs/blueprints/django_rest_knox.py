from http import HTTPStatus

from drf_spectacular.utils import extend_schema, extend_schema_view
from knox.views import LoginView, LogoutAllView, LogoutView
from rest_framework import serializers


class TokenLoginSerializer(serializers.Serializer):
    token = serializers.CharField()
    expiry = serializers.DateTimeField()


@extend_schema_view(
    post=extend_schema(request=None, responses=TokenLoginSerializer),
)
class KnoxLoginView(LoginView):
    """"""


@extend_schema_view(
    post=extend_schema(request=None, responses={HTTPStatus.NO_CONTENT: None}),
)
class KnoxLogoutView(LogoutView):
    """"""


@extend_schema_view(
    post=extend_schema(request=None, responses={HTTPStatus.NO_CONTENT: None}),
)
class KnoxLogoutAllView(LogoutAllView):
    """"""
