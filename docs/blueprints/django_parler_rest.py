from django.conf import settings

from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from drf_spectacular.plumbing import build_object_type


class TranslationsFieldFix(OpenApiSerializerFieldExtension):
    target_class = 'parler_rest.fields.TranslatedFieldsField'

    def map_serializer_field(self, auto_schema, direction):
        # Obtain auto-generated sub-serializer from parler_rest
        # Contains the fields wrapped in parler.models.TranslatedFields()
        translation_serializer = self.target.serializer_class
        # resolve translation sub-serializer into reusable component.
        translation_component = auto_schema.resolve_serializer(
            translation_serializer, direction
        )
        # advertise each language provided in PARLER_LANGUAGES
        return build_object_type(
            properties={
                i['code']: translation_component.ref for i in settings.PARLER_LANGUAGES[None]
            }
        )