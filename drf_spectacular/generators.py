import os
import re

from django.urls import URLPattern, URLResolver
from rest_framework import views, viewsets
from rest_framework.schemas.generators import BaseSchemaGenerator  # type: ignore
from rest_framework.schemas.generators import EndpointEnumerator as BaseEndpointEnumerator
from rest_framework.settings import api_settings

from drf_spectacular.drainage import add_trace_message, reset_generator_stats
from drf_spectacular.extensions import OpenApiViewExtension
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import (
    ComponentRegistry, alpha_operation_sorter, build_root_object, camelize_operation, error,
    get_class, is_versioning_supported, modify_for_versioning, normalize_result_object,
    operation_matches_version, sanitize_result_object, warn,
)
from drf_spectacular.settings import spectacular_settings


class EndpointEnumerator(BaseEndpointEnumerator):
    def get_api_endpoints(self, patterns=None, prefix=''):
        api_endpoints = self._get_api_endpoints(patterns, prefix)

        for hook in spectacular_settings.PREPROCESSING_HOOKS:
            api_endpoints = hook(endpoints=api_endpoints)

        api_endpoints_deduplicated = {}
        for path, path_regex, method, callback in api_endpoints:
            if (path, method) not in api_endpoints_deduplicated:
                api_endpoints_deduplicated[path, method] = (path, path_regex, method, callback)

        api_endpoints = list(api_endpoints_deduplicated.values())

        if callable(spectacular_settings.SORT_OPERATIONS):
            return sorted(api_endpoints, key=spectacular_settings.SORT_OPERATIONS)
        elif spectacular_settings.SORT_OPERATIONS:
            return sorted(api_endpoints, key=alpha_operation_sorter)
        else:
            return api_endpoints

    def get_path_from_regex(self, path_regex):
        path = super().get_path_from_regex(path_regex)
        # bugfix oversight in DRF regex stripping
        path = path.replace('\\.', '.')
        return path

    def _get_api_endpoints(self, patterns, prefix):
        """
        Return a list of all available API endpoints by inspecting the URL conf.
        Only modification the the DRF version is passing through the path_regex.
        """
        if patterns is None:
            patterns = self.patterns

        api_endpoints = []

        for pattern in patterns:
            path_regex = prefix + str(pattern.pattern)
            if isinstance(pattern, URLPattern):
                path = self.get_path_from_regex(path_regex)
                callback = pattern.callback
                if self.should_include_endpoint(path, callback):
                    for method in self.get_allowed_methods(callback):
                        endpoint = (path, path_regex, method, callback)
                        api_endpoints.append(endpoint)

            elif isinstance(pattern, URLResolver):
                nested_endpoints = self._get_api_endpoints(
                    patterns=pattern.url_patterns,
                    prefix=path_regex
                )
                api_endpoints.extend(nested_endpoints)

        return api_endpoints

    def get_allowed_methods(self, callback):
        methods = super().get_allowed_methods(callback)
        return [
            method for method in methods
            if method not in ('OPTIONS', 'HEAD', 'TRACE', 'CONNECT')
        ]


class SchemaGenerator(BaseSchemaGenerator):
    endpoint_inspector_cls = EndpointEnumerator

    def __init__(self, *args, **kwargs):
        self.registry = ComponentRegistry()
        self.api_version = kwargs.pop('api_version', None)
        self.inspector = None
        super().__init__(*args, **kwargs)

    def coerce_path(self, path, method, view):
        """
        Customized coerce_path which also considers the `_pk` suffix in URL paths
        of nested routers.
        """
        path = super().coerce_path(path, method, view)  # take care of {pk}
        if spectacular_settings.SCHEMA_COERCE_PATH_PK_SUFFIX:
            path = re.sub(pattern=r'{(\w+)_pk}', repl=r'{\1_id}', string=path)
        return path

    def create_view(self, callback, method, request=None):
        """
        customized create_view which is called when all routes are traversed. part of this
        is instantiating views with default params. in case of custom routes (@action) the
        custom AutoSchema is injected properly through 'initkwargs' on view. However, when
        decorating plain views like retrieve, this initialization logic is not running.
        Therefore forcefully set the schema if @extend_schema decorator was used.
        """
        override_view = OpenApiViewExtension.get_match(callback.cls)
        if override_view:
            original_cls = callback.cls
            callback.cls = override_view.view_replacement()

        # we refrain from passing request and deal with it ourselves in parse()
        view = super().create_view(callback, method, None)

        # drf-yasg compatibility feature. makes the view aware that we are running
        # schema generation and not a real request.
        view.swagger_fake_view = True

        # callback.cls is hosted in urlpatterns and is therefore not an ephemeral modification.
        # restore after view creation so potential revisits have a clean state as basis.
        if override_view:
            callback.cls = original_cls

        if isinstance(view, viewsets.ViewSetMixin):
            action = getattr(view, view.action)
        elif isinstance(view, views.APIView):
            action = getattr(view, method.lower())
        else:
            error(
                'Using not supported View class. Class must be derived from APIView '
                'or any of its subclasses like GenericApiView, GenericViewSet.'
            )
            return view

        action_schema = getattr(action, 'kwargs', {}).get('schema', None)
        if not action_schema:
            # there is no method/action customized schema so we are done here.
            return view

        # action_schema is either a class or instance. when @extend_schema is used, it
        # is always a class to prevent the weakref reverse "schema.view" bug for multi
        # annotations. The bug is prevented by delaying the instantiation of the schema
        # class until create_view (here) and not doing it immediately in @extend_schema.
        action_schema_class = get_class(action_schema)
        view_schema_class = get_class(callback.cls.schema)

        if not issubclass(action_schema_class, view_schema_class):
            # this handles the case of having a manually set custom AutoSchema on the
            # view together with extend_schema. In most cases, the decorator mechanics
            # prevent extend_schema from having access to the view's schema class. So
            # extend_schema is forced to use DEFAULT_SCHEMA_CLASS as fallback base class
            # instead of the correct base class set in view. We remedy this chicken-egg
            # problem here by rearranging the class hierarchy.
            mro = tuple(
                cls for cls in action_schema_class.__mro__
                if cls not in api_settings.DEFAULT_SCHEMA_CLASS.__mro__
            ) + view_schema_class.__mro__
            action_schema_class = type('ExtendedRearrangedSchema', mro, {})

        view.schema = action_schema_class()
        return view

    def _initialise_endpoints(self):
        if self.endpoints is None:
            self.inspector = self.endpoint_inspector_cls(self.patterns, self.urlconf)
            self.endpoints = self.inspector.get_api_endpoints()

    def _get_paths_and_endpoints(self):
        """
        Generate (path, method, view) given (path, method, callback) for paths.
        """
        view_endpoints = []
        for path, path_regex, method, callback in self.endpoints:
            view = self.create_view(callback, method)
            path = self.coerce_path(path, method, view)
            view_endpoints.append((path, path_regex, method, view))

        return view_endpoints

    def parse(self, input_request, public):
        """ Iterate endpoints generating per method path operations. """
        result = {}
        self._initialise_endpoints()
        endpoints = self._get_paths_and_endpoints()

        if spectacular_settings.SCHEMA_PATH_PREFIX is None:
            # estimate common path prefix if none was given. only use it if we encountered more
            # than one view to prevent emission of erroneous and unnecessary fallback names.
            non_trivial_prefix = len(set([view.__class__ for _, _, _, view in endpoints])) > 1
            if non_trivial_prefix:
                path_prefix = os.path.commonpath([path for path, _, _, _ in endpoints])
                path_prefix = re.escape(path_prefix)  # guard for RE special chars in path
            else:
                path_prefix = '/'
        else:
            path_prefix = spectacular_settings.SCHEMA_PATH_PREFIX
        if not path_prefix.startswith('^'):
            path_prefix = '^' + path_prefix  # make sure regex only matches from the start

        for path, path_regex, method, view in endpoints:
            view.request = spectacular_settings.GET_MOCK_REQUEST(method, path, view, input_request)

            if not (public or self.has_view_permissions(path, method, view)):
                continue

            if view.versioning_class and not is_versioning_supported(view.versioning_class):
                warn(
                    f'using unsupported versioning class "{view.versioning_class}". view will be '
                    f'processed as unversioned view.'
                )
            elif view.versioning_class:
                version = (
                    self.api_version  # explicit version from CLI, SpecView or SpecView request
                    or view.versioning_class.default_version  # fallback
                )
                if not version:
                    continue
                path = modify_for_versioning(self.inspector.patterns, method, path, view, version)
                if not operation_matches_version(view, version):
                    continue

            assert isinstance(view.schema, AutoSchema), (
                f'Incompatible AutoSchema used on View {view.__class__}. Is DRF\'s '
                f'DEFAULT_SCHEMA_CLASS pointing to "drf_spectacular.openapi.AutoSchema" '
                f'or any other drf-spectacular compatible AutoSchema?'
            )
            with add_trace_message(getattr(view, '__class__', view).__name__):
                operation = view.schema.get_operation(
                    path, path_regex, path_prefix, method, self.registry
                )

            # operation was manually removed via @extend_schema
            if not operation:
                continue

            if spectacular_settings.SCHEMA_PATH_PREFIX_TRIM:
                path = re.sub(pattern=path_prefix, repl='', string=path, flags=re.IGNORECASE)

            if not path.startswith('/'):
                path = '/' + path

            if spectacular_settings.CAMELIZE_NAMES:
                path, operation = camelize_operation(path, operation)

            result.setdefault(path, {})
            result[path][method.lower()] = operation

        return result

    def get_schema(self, request=None, public=False):
        """ Generate a OpenAPI schema. """
        reset_generator_stats()
        result = build_root_object(
            paths=self.parse(request, public),
            components=self.registry.build(spectacular_settings.APPEND_COMPONENTS),
            version=self.api_version or getattr(request, 'version', None),
        )
        for hook in spectacular_settings.POSTPROCESSING_HOOKS:
            result = hook(result=result, generator=self, request=request, public=public)

        return sanitize_result_object(normalize_result_object(result))
