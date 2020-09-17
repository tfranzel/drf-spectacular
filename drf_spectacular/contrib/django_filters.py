from drf_spectacular.plumbing import build_parameter_type, get_view_model
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
            if '__' in field.field_name:
                fn = field.field_name.split('__')
                c = 0
                model_field = model
                while c < len(fn):
                    model_field = getattr(model_field, '_meta').get_field(fn[c])
                    if hasattr(model_field, 'related_model') and c+1 < len(fn):
                        if getattr(model_field, 'related_model')() is not None:
                            model_field = getattr(model_field, 'related_model')()
                    c += 1
            else:
                model_field = model._meta.get_field(field.field_name)

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
