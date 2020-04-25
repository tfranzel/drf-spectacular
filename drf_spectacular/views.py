from collections import namedtuple

from rest_framework.renderers import JSONOpenAPIRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.renderers import NoAliasOpenAPIRenderer
from drf_spectacular.settings import spectacular_settings
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

    generator_class = spectacular_settings.DEFAULT_GENERATOR_CLASS
    serve_public = spectacular_settings.SERVE_PUBLIC
    urlconf = spectacular_settings.SERVE_URLCONF

    @extend_schema(**SCHEMA_KWARGS)
    def get(self, request):
        if isinstance(self.urlconf, list):
            ModuleWrapper = namedtuple('ModuleWrapper', ['urlpatterns'])
            self.urlconf = ModuleWrapper(self.urlconf)

        generator = self.generator_class(urlconf=self.urlconf)
        schema = generator.get_schema(request=request, public=self.serve_public)
        return Response(schema)


class SpectacularYAMLAPIView(SpectacularAPIView):
    renderer_classes = [NoAliasOpenAPIRenderer]


class SpectacularJSONAPIView(SpectacularAPIView):
    renderer_classes = [JSONOpenAPIRenderer]
