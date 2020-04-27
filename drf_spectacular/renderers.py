import yaml
import logging
from rest_framework.renderers import JSONOpenAPIRenderer, OpenAPIRenderer
#from drf_spectacular.plumbing import warn

from rest_framework.exceptions import ErrorDetail

logger = logging.getLogger(__name__)


class NoAliasOpenAPIRenderer(OpenAPIRenderer):
    """ Remove this temp fix once DRF 3.11 is no longer supported """

    def render(self, data, media_type=None, renderer_context=None):
        detail = data.get('detail')
        if detail and isinstance(detail, ErrorDetail):
            if not media_type:
                media_type = 'Unknown'
            logger.error(f'media type {media_type}: Failure {detail}')
            return False

        # disable yaml advanced feature 'alias' for clean, portable, and readable output
        class Dumper(yaml.SafeDumper):
            def ignore_aliases(self, data):
                return True

        return yaml.dump(data, default_flow_style=False, sort_keys=False, Dumper=Dumper).encode('utf-8')


class ApplicationYamlOpenAPIRenderer(NoAliasOpenAPIRenderer):
    media_type = 'application/yaml'
    format = 'yaml'


class ApplicationJsonOpenAPIRenderer(JSONOpenAPIRenderer):
    media_type = 'application/json'
    format = 'json'
