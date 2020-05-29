from unittest import mock

from rest_framework import serializers, viewsets, mixins, generics
from rest_framework.decorators import action

from drf_spectacular.utils import extend_schema
from tests import assert_schema, generate_schema

language_choices = (
    ('en', 'en'),
    ('es', 'es'),
    ('ru', 'ru'),
    ('cn', 'cn'),
)


class ASerializer(serializers.Serializer):
    language = serializers.ChoiceField(choices=language_choices)


class BSerializer(serializers.Serializer):
    language = serializers.ChoiceField(choices=language_choices)


class AViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ASerializer

    @extend_schema(responses=BSerializer)
    @action(detail=False, serializer_class=BSerializer)
    def selection(self, request):
        pass  # pragma: no cover


def test_postprocessing(no_warnings):
    schema = generate_schema('a', AViewset)
    assert_schema(schema, 'tests/test_postprocessing.yml')


@mock.patch('drf_spectacular.settings.spectacular_settings.ENUM_NAME_OVERRIDES', {
    'LanguageEnum': language_choices
})
def test_global_enum_naming_override(no_warnings):

    class XSerializer(serializers.Serializer):
        foo = serializers.ChoiceField(choices=language_choices)
        bar = serializers.ChoiceField(choices=language_choices)

    class XView(generics.RetrieveAPIView):
        serializer_class = XSerializer

    schema = generate_schema('/x', view=XView)
    assert 'LanguageEnum' in schema['components']['schemas']['X']['properties']['foo']['$ref']
    assert 'LanguageEnum' in schema['components']['schemas']['X']['properties']['bar']['$ref']
    assert len(schema['components']['schemas']) == 2
