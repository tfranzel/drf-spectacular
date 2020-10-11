from drf_spectacular.plumbing import build_parameter_type, follow_field_source, get_view_model
from drf_spectacular.utils import OpenApiParameter

try:
    from django_filters.rest_framework import DjangoFilterBackend as OriginalDjangoFilterBackend
except ImportError:
    class OriginalDjangoFilterBackend:  # type: ignore
        pass


class SpectacularDjangoFilterBackendMixin:
    def get_schema_operation_parameters(self, view):
        model = get_view_model(view)
        if not model:
            return []

        filterset_class = self.get_filterset_class(view, model.objects.none())
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
                schema=view.schema._map_model_field(model_field, direction=None),
                enum=[c for c, _ in field.extra.get('choices', [])],
            ))

        return parameters


class DjangoFilterBackend(SpectacularDjangoFilterBackendMixin, OriginalDjangoFilterBackend):
    pass
