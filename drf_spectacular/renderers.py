import yaml
from rest_framework.renderers import OpenAPIRenderer


class NoAliasOpenAPIRenderer(OpenAPIRenderer):
    """ Remove this temp fix once DRF 3.11 is no longer supported """

    def render(self, data, media_type=None, renderer_context=None):
        # disable yaml advanced feature 'alias' for clean, portable, and readable output
        class Dumper(yaml.SafeDumper):
            def ignore_aliases(self, data):
                return True

        return yaml.dump(data, default_flow_style=False, sort_keys=False, Dumper=Dumper).encode('utf-8')
