import typing

from django.db import models

from drf_spectacular.extensions import OpenApiFilterExtension
from drf_spectacular.plumbing import (
    build_basic_type, build_parameter_type, follow_field_source, get_view_model, is_basic_type,
    warn,
)
from drf_spectacular.types import OpenApiTypes
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
        if issubclass(self.target_class, SpectacularDjangoFilterBackendMixin):
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
            schema, description, enum = (
                self.resolve_filter_field(auto_schema, model, filterset_class, field)
            )
            parameters.append(build_parameter_type(
                name=field_name,
                required=field.extra['required'],
                location=OpenApiParameter.QUERY,
                description=description,
                schema=schema,
                enum=enum,
            ))

        return parameters

    def resolve_filter_field(self, auto_schema, model, filterset_class, filter_field):
        if filter_field.method:
            filter_method = getattr(filterset_class, filter_field.method)
            filter_method_hints = typing.get_type_hints(filter_method)

            if 'value' in filter_method_hints and is_basic_type(filter_method_hints['value']):
                schema = build_basic_type(filter_method_hints['value'])
            else:
                schema = self.map_filter_field(filter_field)
        else:
            path = filter_field.field_name.split('__')
            model_field = follow_field_source(model, path)

            if isinstance(model_field, models.Field):
                schema = auto_schema._map_model_field(model_field, direction=None)
            else:
                schema = self.map_filter_field(filter_field)

        enum = schema.pop('enum', None)

        if 'choices' in filter_field.extra:
            enum = [c for c, _ in filter_field.extra['choices']]

        description = schema.pop('description', None)

        if filter_field.extra.get('help_text', None):
            description = filter_field.extra['help_text']
        elif filter_field.label is not None:
            description = filter_field.label

        return schema, description, enum

    def map_filter_field(self, filter_field):
        from django_filters.rest_framework import filters
        mapping = {
            filters.CharFilter: OpenApiTypes.STR,
            filters.BooleanFilter: OpenApiTypes.BOOL,
            filters.DateFilter: OpenApiTypes.DATE,
            filters.DateTimeFilter: OpenApiTypes.DATETIME,
            filters.TimeFilter: OpenApiTypes.TIME,
            filters.UUIDFilter: OpenApiTypes.UUID,
            filters.NumberFilter: OpenApiTypes.NUMBER,
            # TODO underspecified filters. fallback to STR
            # filters.ChoiceFilter: None,
            # filters.TypedChoiceFilter: None,
            # filters.MultipleChoiceFilter: None,
            # filters.DurationFilter: None,
            # filters.NumericRangeFilter: None,
            # filters.RangeFilter: None,
            # filters.BaseCSVFilter: None,
            # filters.LookupChoiceFilter: None,
        }
        return build_basic_type(mapping.get(filter_field.__class__, OpenApiTypes.STR))


class SpectacularDjangoFilterBackendMixin:
    """ DEPRECATED - superseded by FilterExtensions """
    def get_schema_operation_parameters(self, view):
        return super().get_schema_operation_parameters(view)


class DjangoFilterBackend(SpectacularDjangoFilterBackendMixin, OriginalDjangoFilterBackend):
    """ DEPRECATED - superseded by FilterExtensions """
    pass
