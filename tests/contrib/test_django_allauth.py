import pytest
from rest_framework import permissions
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema
from tests import generate_schema

try:
    from allauth import __version__ as allauth_version
    from allauth.headless.contrib.rest_framework.authentication import XSessionTokenAuthentication
except ImportError:
    XSessionTokenAuthentication = object
    allauth_version = "0.0.0"


@pytest.mark.contrib('django_allauth')
@pytest.mark.skipif(allauth_version < "0.65.4", reason='')
def test_allauth_token_auth(no_warnings):

    class XAPIView(APIView):
        authentication_classes = [XSessionTokenAuthentication]
        permission_classes = [permissions.IsAuthenticated]

        @extend_schema(responses=int)
        def get(self, request):
            pass  # pragma: no cover

    schema = generate_schema('x', view=XAPIView)
    assert schema['components']['securitySchemes'] == {
        'XSessionTokenAuth': {
            "type": "apiKey",
            "in": "header",
            "name": "X-Session-Token",
            "description": "X-Session-Token authentication",
        }
    }
