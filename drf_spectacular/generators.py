import inspect
from urllib.parse import urljoin

from rest_framework import viewsets, views
from rest_framework.schemas.generators import BaseSchemaGenerator

from drf_spectacular.plumbing import (
    ComponentRegistry, warn, alpha_operation_sorter, reset_generator_stats, build_root_object
)
from drf_spectacular.settings import spectacular_settings


class SchemaGenerator(BaseSchemaGenerator):
    def __init__(self, *args, **kwargs):
        self.registry = ComponentRegistry()
        super().__init__(*args, **kwargs)

    def create_view(self, callback, method, request=None):
        """
        customized create_view which is called when all routes are traversed. part of this
        is instantiating views with default params. in case of custom routes (@action) the
        custom AutoSchema is injected properly through 'initkwargs' on view. However, when
        decorating plain views like retrieve, this initialization logic is not running.
        Therefore forcefully set the schema if @extend_schema decorator was used.
        """
        view = super().create_view(callback, method, request)

        if isinstance(view, viewsets.GenericViewSet) or isinstance(view, viewsets.ViewSet):
            action = getattr(view, view.action)
        elif isinstance(view, views.APIView):
            action = getattr(view, method.lower())
        else:
            warn(
                'Using not supported View class. Class must be derived from APIView '
                'or any of its subclasses like GenericApiView, GenericViewSet.'
            )
            return view

        # in case of @extend_schema, manually init custom schema class here due to
        # weakref reverse schema.view bug for multi annotations.
        schema = getattr(action, 'kwargs', {}).get('schema', None)
        if schema and inspect.isclass(schema):
            view.schema = schema()

        return view

    def get_endpoints(self, request):
        """ sorted endpoints by operation """
        self._initialise_endpoints()
        _, endpoints = self._get_paths_and_endpoints(request)

        if spectacular_settings.OPERATION_SORTER == 'alpha':
            return sorted(endpoints, key=alpha_operation_sorter)
        else:
            # default to DRF method sorting
            return endpoints

    def parse(self, request=None):
        """ Iterate endpoints generating per method path operations. """
        result = {}

        for path, method, view in self.get_endpoints(request):
            if not self.has_view_permissions(path, method, view):
                continue

            # beware that every access to schema yields a fresh object (descriptor pattern)
            operation = view.schema.get_operation(path, method, self.registry)

            # operation was manually removed via @extend_schema
            if not operation:
                continue

            # Normalise path for any provided mount url.
            if path.startswith('/'):
                path = path[1:]
            path = urljoin(self.url or '/', path)

            result.setdefault(path, {})
            result[path][method.lower()] = operation

        return result

    def get_schema(self, request=None, public=False):
        """ Generate a OpenAPI schema. """
        reset_generator_stats()
        return build_root_object(
            paths=self.parse(None if public else request),
            components=self.registry.build(spectacular_settings.APPEND_COMPONENTS),
        )
