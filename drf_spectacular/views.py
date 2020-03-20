from rest_framework.renderers import JSONOpenAPIRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.app_settings import spectacular_settings
from drf_spectacular.renderers import NoAliasOpenAPIRenderer
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema


class SpectacularAPIView(APIView):
    renderer_classes = [NoAliasOpenAPIRenderer, JSONOpenAPIRenderer]

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        generator_class = spectacular_settings.DEFAULT_GENERATOR_CLASS
        generator = generator_class(
            urlconf=spectacular_settings.SERVE_URLCONF,
        )
        return Response(generator.get_schema(
            request=request,
            public=spectacular_settings.SERVE_PUBLIC
        ))
