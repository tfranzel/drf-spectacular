from drf_spectacular.extensions import OpenApiFilterExtension
from drf_spectacular.plumbing import build_parameter_type, follow_field_source, get_view_model, warn
from drf_spectacular.utils import OpenApiParameter

try:
    from django_filters.rest_framework import DjangoFilterBackend as OriginalDjangoFilterBackend
except ImportError:
    class OriginalDjangoFilterBackend:  # type: ignore
        pass


class DjangoFilterExtension(OpenApiFilterExtension):
    target_class = 'django_filters.rest_framework.DjangoFilterBackend'
    match_subclasses = True

    def get_schema_operation_parameters(self, auto_schema, *args, **kwargs):
        if isinstance(self.target_class, SpectacularDjangoFilterBackendMixin):
            warn(
                'DEPRECATED - Spectacular\'s DjangoFilterBackend is superseded by extension. you '
                'can simply restore this to the original class, extensions will take care of the '
                'rest.'
            )

        model = get_view_model(auto_schema.view)
        if not model:
            return []

        filterset_class = self.target.get_filterset_class(auto_schema.view, model.objects.none())
        if not filterset_class:
            return []

        parameters = []
        for field_name, field in filterset_class.base_filters.items():
            path = field.field_name.split('__')
            model_field = follow_field_source(model, path)

            parameters.append(build_parameter_type(
                name=field_name,
                required=field.extra['required'],
                location=OpenApiParameter.QUERY,
                description=field.label if field.label is not None else field_name,
                schema=auto_schema._map_model_field(model_field, direction=None),
                enum=[c for c, _ in field.extra.get('choices', [])],
            ))

        return parameters


class SpectacularDjangoFilterBackendMixin:
    """ DEPRECATED - superseded by FilterExtensions """
    def get_schema_operation_parameters(self, view):
        return super().get_schema_operation_parameters(view)


class DjangoFilterBackend(SpectacularDjangoFilterBackendMixin, OriginalDjangoFilterBackend):
    """ DEPRECATED - superseded by FilterExtensions """
    pass
