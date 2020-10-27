from mongoengine import document, fields  # type: ignore
from rest_framework.utils.model_meta import get_field_info
from rest_framework_mongoengine import serializers, viewsets  # type: ignore

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import (
    anyisinstance, build_basic_type, error, get_lib_doc_excludes, warn,
)
from drf_spectacular.types import OpenApiTypes


class MongoEngineAutoSchema(AutoSchema):
    def _map_model_field(self, model_field, direction):
        assert isinstance(model_field, fields.BaseField)
        # to get a fully initialized serializer field we use DRF's own init logic
        try:
            field_cls, field_kwargs = serializers.DocumentSerializer().build_field(
                field_name=model_field.name,
                info=get_field_info(model_field.model),
                model_class=model_field.model,
                nested_depth=0,
            )
            field = field_cls(**field_kwargs)
        except:  # noqa
            field = None

        if field and not anyisinstance(field, [fields.EmbeddedDocumentField, fields.EmbeddedDocumentListField]):
            return self._map_serializer_field(field, direction)
        elif isinstance(model_field, fields.ReferenceField):
            return self._map_model_field(model_field.target_field, direction)
        elif hasattr(document, model_field.__class__.__name__):
            # be graceful when the document field is not explicitly mapped to a serializer
            internal_type = getattr(document, model_field.__class__.__name__)
            field_cls = serializers.DocumentSerializer.serializer_field_mapping.get(internal_type)
            if not field_cls:
                warn(
                    f'document field "{model_field.__class__.__name__}" has no mapping in '
                    f'DocumentSerializer. it may be a deprecated field. defaulting to "string"'
                )
                return build_basic_type(OpenApiTypes.STR)
            return self._map_serializer_field(field_cls(), direction)
        else:
            error(
                f'could not resolve document field "{model_field}". failed to resolve through '
                f'serializer_field_mapping, get_internal_type(), or any override mechanism. '
                f'defaulting to "string"'
            )
            return build_basic_type(OpenApiTypes.STR)


def get_mongoengine_extended_doc_excludes():
    return get_lib_doc_excludes() + [
        serializers.DocumentSerializer,
        serializers.EmbeddedDocumentSerializer,
        viewsets.ModelViewSet,
        viewsets.GenericViewSet,
        viewsets.ReadOnlyModelViewSet
    ]
