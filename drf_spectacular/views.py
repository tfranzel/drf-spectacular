import json
from collections import namedtuple
from typing import Any, Dict

from django.conf import settings
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from drf_spectacular.plumbing import get_relative_url, set_query_parameters
from drf_spectacular.renderers import (
    OpenApiJsonRenderer, OpenApiJsonRenderer2, OpenApiYamlRenderer, OpenApiYamlRenderer2,
)
from drf_spectacular.settings import spectacular_settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

if spectacular_settings.SERVE_INCLUDE_SCHEMA:
    SCHEMA_KWARGS: Dict[str, Any] = {'responses': {200: OpenApiTypes.OBJECT}}

    if settings.USE_I18N:
        SCHEMA_KWARGS['parameters'] = [
            OpenApiParameter(
                'lang', str, OpenApiParameter.QUERY, enum=list(dict(settings.LANGUAGES).keys())
            )
        ]
else:
    SCHEMA_KWARGS = {'exclude': True}

if spectacular_settings.SERVE_AUTHENTICATION is not None:
    AUTHENTICATION_CLASSES = spectacular_settings.SERVE_AUTHENTICATION
else:
    AUTHENTICATION_CLASSES = api_settings.DEFAULT_AUTHENTICATION_CLASSES


class SpectacularAPIView(APIView):
    __doc__ = _("""
    OpenApi3 schema for this API. Format can be selected via content negotiation.

    - YAML: application/vnd.oai.openapi
    - JSON: application/vnd.oai.openapi+json
    """)
    renderer_classes = [
        OpenApiYamlRenderer, OpenApiYamlRenderer2, OpenApiJsonRenderer, OpenApiJsonRenderer2
    ]
    permission_classes = spectacular_settings.SERVE_PERMISSIONS
    authentication_classes = AUTHENTICATION_CLASSES
    generator_class = spectacular_settings.DEFAULT_GENERATOR_CLASS
    serve_public = spectacular_settings.SERVE_PUBLIC
    urlconf = spectacular_settings.SERVE_URLCONF
    api_version = None

    @extend_schema(**SCHEMA_KWARGS)
    def get(self, request, *args, **kwargs):
        if isinstance(self.urlconf, list) or isinstance(self.urlconf, tuple):
            ModuleWrapper = namedtuple('ModuleWrapper', ['urlpatterns'])
            self.urlconf = ModuleWrapper(tuple(self.urlconf))

        if settings.USE_I18N and request.GET.get('lang'):
            with translation.override(request.GET.get('lang')):
                return self._get_schema_response(request)
        else:
            return self._get_schema_response(request)

    def _get_schema_response(self, request):
        generator = self.generator_class(urlconf=self.urlconf, api_version=self.api_version)
        return Response(generator.get_schema(request=request, public=self.serve_public))


class SpectacularYAMLAPIView(SpectacularAPIView):
    renderer_classes = [OpenApiYamlRenderer, OpenApiYamlRenderer2]


class SpectacularJSONAPIView(SpectacularAPIView):
    renderer_classes = [OpenApiJsonRenderer, OpenApiJsonRenderer2]


class SpectacularSwaggerView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = spectacular_settings.SERVE_PERMISSIONS
    authentication_classes = AUTHENTICATION_CLASSES
    url_name = 'schema'
    url = None
    template_name = 'drf_spectacular/swagger_ui.html'
    template_name_js = 'drf_spectacular/swagger_ui.js'

    @extend_schema(exclude=True)
    def get(self, request, *args, **kwargs):
        schema_url = self.url or get_relative_url(reverse(self.url_name, request=request))
        return Response(
            data={
                'dist': spectacular_settings.SWAGGER_UI_DIST,
                'favicon_href': spectacular_settings.SWAGGER_UI_FAVICON_HREF,
                'schema_url': set_query_parameters(
                    url=schema_url,
                    lang=request.GET.get('lang')
                ),
                'settings': json.dumps(spectacular_settings.SWAGGER_UI_SETTINGS),
                'template_name_js': self.template_name_js
            },
            template_name=self.template_name,
        )


class SpectacularSwaggerSplitView(SpectacularSwaggerView):
    """
    Alternate Swagger UI implementation that separates the html request from the
    javascript request to cater to web servers with stricter CSP policies.
    """
    url_self = None

    @extend_schema(exclude=True)
    def get(self, request, *args, **kwargs):
        if request.GET.get('script') is not None:
            schema_url = self.url or get_relative_url(reverse(self.url_name, request=request))
            return Response(
                data={
                    'schema_url': set_query_parameters(
                        url=schema_url,
                        lang=request.GET.get('lang')
                    ),
                    'settings': json.dumps(spectacular_settings.SWAGGER_UI_SETTINGS),
                },
                template_name=self.template_name_js,
                content_type='application/javascript',
            )
        else:
            script_url = self.url_self or request.get_full_path()
            return Response(
                data={
                    'dist': spectacular_settings.SWAGGER_UI_DIST,
                    'favicon_href': spectacular_settings.SWAGGER_UI_FAVICON_HREF,
                    'script_url': set_query_parameters(
                        url=script_url,
                        lang=request.GET.get('lang'),
                        script=''  # signal to deliver init script
                    )
                },
                template_name=self.template_name,
            )


class SpectacularRedocView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = spectacular_settings.SERVE_PERMISSIONS
    authentication_classes = AUTHENTICATION_CLASSES
    url_name = 'schema'
    url = None
    template_name = 'drf_spectacular/redoc.html'

    @extend_schema(exclude=True)
    def get(self, request, *args, **kwargs):
        schema_url = self.url or get_relative_url(reverse(self.url_name, request=request))
        schema_url = set_query_parameters(schema_url, lang=request.GET.get('lang'))
        return Response(
            {'schema_url': schema_url},
            template_name=self.template_name
        )
