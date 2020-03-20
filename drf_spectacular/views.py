from rest_framework.renderers import JSONOpenAPIRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.app_settings import spectacular_settings
from drf_spectacular.renderers import NoAliasOpenAPIRenderer
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema

if spectacular_settings.SERVE_INCLUDE_SCHEMA:
    SCHEMA_KWARGS = {'responses': {200: OpenApiTypes.OBJECT}}
else:
    SCHEMA_KWARGS = {'exclude': True}


class SpectacularAPIView(APIView):
    """
    OpenApi3 schema for this API. Format can be selected via content negotiation.

    - YAML: application/vnd.oai.openapi
    - JSON: application/vnd.oai.openapi+json
    """
    renderer_classes = [NoAliasOpenAPIRenderer, JSONOpenAPIRenderer]
    permission_classes = spectacular_settings.SERVE_PERMISSIONS

    @extend_schema(**SCHEMA_KWARGS)
    def get(self, request):
        generator_class = spectacular_settings.DEFAULT_GENERATOR_CLASS
        generator = generator_class(
            urlconf=spectacular_settings.SERVE_URLCONF,
        )
        return Response(generator.get_schema(
            request=request,
            public=spectacular_settings.SERVE_PUBLIC
        ))


class SpectacularYAMLAPIView(SpectacularAPIView):
    renderer_classes = [NoAliasOpenAPIRenderer]


class SpectacularJSONAPIView(SpectacularAPIView):
    renderer_classes = [JSONOpenAPIRenderer]
