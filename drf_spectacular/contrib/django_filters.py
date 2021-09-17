from django.db import models

from drf_spectacular.drainage import add_trace_message, get_override, has_override, warn
from drf_spectacular.extensions import OpenApiFilterExtension
from drf_spectacular.plumbing import (
    build_array_type, build_basic_type, build_parameter_type, follow_field_source, get_type_hints,
    get_view_model, is_basic_type,
)
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter


class DjangoFilterExtension(OpenApiFilterExtension):
    """
    Extensions that specifically deals with ``django-filter`` fields. The introspection
    attempts to estimate the underlying model field types to generate filter types.

    However, there are under-specified filter fields for which heuristics need to be performed.
    This serves as an explicit list of all partially-handled filter fields:

    - ``AllValuesFilter``: skip choices to prevent DB query
    - ``AllValuesMultipleFilter``: skip choices to prevent DB query, multi handled though
    - ``ChoiceFilter``: enum handled, type under-specified
    - ``DateRangeFilter``: N/A
    - ``LookupChoiceFilter``: N/A
    - ``ModelChoiceFilter``: enum handled
    - ``ModelMultipleChoiceFilter``: enum, multi handled
    - ``MultipleChoiceFilter``: enum, multi handled
    - ``RangeFilter``: min/max handled, type under-specified
    - ``TypedChoiceFilter``: enum handled
    - ``TypedMultipleChoiceFilter``: enum, multi handled

    In case of warnings or incorrect filter types, you can manually override the underlying
    field type with a manual ``extend_schema_field`` decoration.

    .. code-block::

        class SomeFilter(FilterSet):
            some_field = extend_schema_field(OpenApiTypes.NUMBER)(
                RangeFilter(field_name='some_manually_annotated_field_in_qs')
            )

    """
    target_class = 'django_filters.rest_framework.DjangoFilterBackend'

    def get_schema_operation_parameters(self, auto_schema, *args, **kwargs):
        model = get_view_model(auto_schema.view)
        if not model:
            return []

        filterset_class = self.target.get_filterset_class(auto_schema.view, model.objects.none())
        if not filterset_class:
            return []

        result = []
        with add_trace_message(filterset_class.__name__):
            for field_name, filter_field in filterset_class.base_filters.items():
                result += self.resolve_filter_field(
                    auto_schema, model, filterset_class, field_name, filter_field
                )
        return result

    def resolve_filter_field(self, auto_schema, model, filterset_class, field_name, filter_field):
        from django_filters import filters

        unambiguous_mapping = {
            filters.CharFilter: OpenApiTypes.STR,
            filters.BooleanFilter: OpenApiTypes.BOOL,
            filters.DateFilter: OpenApiTypes.DATE,
            filters.DateTimeFilter: OpenApiTypes.DATETIME,
            filters.IsoDateTimeFilter: OpenApiTypes.DATETIME,
            filters.TimeFilter: OpenApiTypes.TIME,
            filters.UUIDFilter: OpenApiTypes.UUID,
            filters.DurationFilter: OpenApiTypes.DURATION,
            filters.OrderingFilter: OpenApiTypes.STR,
            filters.TimeRangeFilter: OpenApiTypes.TIME,
            filters.DateFromToRangeFilter: OpenApiTypes.DATE,
            filters.IsoDateTimeFromToRangeFilter: OpenApiTypes.DATETIME,
            filters.DateTimeFromToRangeFilter: OpenApiTypes.DATETIME,
        }
        if has_override(filter_field, 'field'):
            annotation = get_override(filter_field, 'field')
            if is_basic_type(annotation):
                schema = build_basic_type(annotation)
            else:
                schema = annotation
        elif isinstance(filter_field, tuple(unambiguous_mapping)):
            for cls in filter_field.__class__.__mro__:
                if cls in unambiguous_mapping:
                    schema = build_basic_type(unambiguous_mapping[cls])
                    break
        elif isinstance(filter_field, (filters.NumberFilter, filters.NumericRangeFilter)):
            # NumberField is underspecified by itself. try to find the
            # type that makes the most sense or default to generic NUMBER
            if filter_field.method:
                schema = self._build_filter_method_type(filterset_class, filter_field)
                if schema['type'] not in ['integer', 'number']:
                    schema = build_basic_type(OpenApiTypes.NUMBER)
            else:
                model_field = self._get_model_field(filter_field, model)
                if isinstance(model_field, (models.IntegerField, models.AutoField)):
                    schema = build_basic_type(OpenApiTypes.INT)
                elif isinstance(model_field, models.FloatField):
                    schema = build_basic_type(OpenApiTypes.FLOAT)
                elif isinstance(model_field, models.DecimalField):
                    schema = build_basic_type(OpenApiTypes.NUMBER)  # TODO may be improved
                else:
                    schema = build_basic_type(OpenApiTypes.NUMBER)
        elif filter_field.method:
            # try to make best effort on the given method
            schema = self._build_filter_method_type(filterset_class, filter_field)
        else:
            try:
                # the last resort is to lookup the type via the model or queryset field.
                # first search for the field in the model as this has the least amount of
                # potential side effects. Only after that fails, attempt to call
                # get_queryset() to check for potential query annotations.
                model_field = self._get_model_field(filter_field, model)
                if not isinstance(model_field, models.Field):
                    qs = auto_schema.view.get_queryset()
                    model_field = qs.query.annotations[filter_field.field_name].field
                schema = auto_schema._map_model_field(model_field, direction=None)
            except Exception as exc:
                warn(
                    f'Exception raised while trying resolve model field for django-filter '
                    f'field "{field_name}". Defaulting to string (Exception: {exc})'
                )
                schema = build_basic_type(OpenApiTypes.STR)

        # primary keys are usually non-editable (readOnly=True) and map_model_field correctly
        # signals that attribute. however this does not apply in this context.
        schema.pop('readOnly', None)
        # enrich schema with additional info from filter_field
        enum = schema.pop('enum', None)
        if 'choices' in filter_field.extra:
            enum = [c for c, _ in filter_field.extra['choices']]
        if enum:
            schema['enum'] = sorted(enum, key=str)

        description = schema.pop('description', None)
        if filter_field.extra.get('help_text', None):
            description = filter_field.extra['help_text']
        elif filter_field.label is not None:
            description = filter_field.label

        # parameter style variations based on filter base class
        if isinstance(filter_field, filters.BaseCSVFilter):
            schema = build_array_type(schema)
            field_names = [field_name]
            explode = False
            style = 'form'
        elif isinstance(filter_field, filters.MultipleChoiceFilter):
            schema = build_array_type(schema)
            field_names = [field_name]
            explode = True
            style = 'form'
        elif isinstance(filter_field, (filters.RangeFilter, filters.NumericRangeFilter)):
            try:
                suffixes = filter_field.field_class.widget.suffixes
            except AttributeError:
                suffixes = ['min', 'max']
            field_names = [
                f'{field_name}_{suffix}' if suffix else field_name for suffix in suffixes
            ]
            explode = None
            style = None
        else:
            field_names = [field_name]
            explode = None
            style = None

        return [
            build_parameter_type(
                name=field_name,
                required=filter_field.extra['required'],
                location=OpenApiParameter.QUERY,
                description=description,
                schema=schema,
                explode=explode,
                style=style
            )
            for field_name in field_names
        ]

    def _build_filter_method_type(self, filterset_class, filter_field):
        if callable(filter_field.method):
            filter_method = filter_field.method
        else:
            filter_method = getattr(filterset_class, filter_field.method)

        try:
            filter_method_hints = get_type_hints(filter_method)
        except:  # noqa: E722
            filter_method_hints = {}

        if 'value' in filter_method_hints and is_basic_type(filter_method_hints['value']):
            return build_basic_type(filter_method_hints['value'])
        else:
            return build_basic_type(OpenApiTypes.STR)

    def _get_model_field(self, filter_field, model):
        if not filter_field.field_name:
            return None
        path = filter_field.field_name.split('__')
        return follow_field_source(model, path, emit_warnings=False)
