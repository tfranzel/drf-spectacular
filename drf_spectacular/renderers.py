import yaml
from django.conf import settings
from rest_framework.renderers import OpenAPIRenderer

enable_schema_key_sorting = settings.SPECTACULAR_SETTINGS['ENABLE_SCHEMA_KEY_SORTING']


class NoAliasOpenAPIRenderer(OpenAPIRenderer):
    """ Remove this temp fix once DRF 3.11 is no longer supported """

    def render(self, data, media_type=None, renderer_context=None):
        # disable yaml advanced feature 'alias' for clean, portable, and readable output
        class Dumper(yaml.Dumper):
            def ignore_aliases(self, data):
                return True

        return yaml.dump(data, default_flow_style=False, sort_keys=enable_schema_key_sorting, Dumper=Dumper).encode('utf-8')
