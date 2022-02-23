from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from drf_spectacular.plumbing import get_relative_url, set_query_parameters
from drf_spectacular.settings import spectacular_settings
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import AUTHENTICATION_CLASSES


class SpectacularRapiDocView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = spectacular_settings.SERVE_PERMISSIONS
    authentication_classes = AUTHENTICATION_CLASSES
    url_name = 'schema'
    url = None
    template_name = 'rapidoc.html'
    title = spectacular_settings.TITLE

    @extend_schema(exclude=True)
    def get(self, request, *args, **kwargs):
        schema_url = self.url or get_relative_url(reverse(self.url_name, request=request))
        schema_url = set_query_parameters(schema_url, lang=request.GET.get('lang'))
        return Response(
            data={
                'title': self.title,
                'dist': 'https://cdn.jsdelivr.net/npm/rapidoc@latest',
                'schema_url': schema_url,
            },
            template_name=self.template_name,
        )
