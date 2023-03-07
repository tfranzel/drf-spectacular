from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import append_meta
from drf_spectacular.plumbing import build_basic_type
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import Direction


class Base64FileFieldSchema(OpenApiSerializerFieldExtension):
    target_class = "drf_extra_fields.fields.Base64FileField"

    def map_serializer_field(self, auto_schema, direction):
        if direction == "request":
            return build_basic_type(OpenApiTypes.BYTE)
        elif direction == "response":
            if self.target.represent_in_base64:
                return build_basic_type(OpenApiTypes.BYTE)
            else:
                return build_basic_type(OpenApiTypes.URI)


class Base64ImageFieldSchema(Base64FileFieldSchema):
    target_class = "drf_extra_fields.fields.Base64ImageField"


class PresentablePrimaryKeyRelatedFieldSchema(OpenApiSerializerFieldExtension):
    target_class = 'drf_extra_fields.relations.PresentablePrimaryKeyRelatedField'

    def map_serializer_field(self, auto_schema: AutoSchema, direction: Direction):
        if direction == 'request':
            return build_basic_type(OpenApiTypes.INT)

        meta = auto_schema._get_serializer_field_meta(self.target, direction)
        schema = auto_schema.resolve_serializer(
            self.target.presentation_serializer(
                context=self.target.context, **self.target.presentation_serializer_kwargs,
            ),
            direction,
        ).ref
        return append_meta(schema, meta)
