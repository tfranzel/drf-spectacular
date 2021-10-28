from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from drf_spectacular.plumbing import build_basic_type
from drf_spectacular.types import OpenApiTypes


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
