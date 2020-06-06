from unittest import mock

from rest_framework import generics, mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.views import APIView

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
    'LanguageEnum': 'tests.test_postprocessing.language_choices'
})
def test_global_enum_naming_override(no_warnings):
    # the override will prevent the warning for multiple names
    class XSerializer(serializers.Serializer):
        foo = serializers.ChoiceField(choices=language_choices)
        bar = serializers.ChoiceField(choices=language_choices)

    class XView(generics.RetrieveAPIView):
        serializer_class = XSerializer

    schema = generate_schema('/x', view=XView)
    assert 'LanguageEnum' in schema['components']['schemas']['X']['properties']['foo']['$ref']
    assert 'LanguageEnum' in schema['components']['schemas']['X']['properties']['bar']['$ref']
    assert len(schema['components']['schemas']) == 2


def test_enum_name_reuse_warning(capsys):
    class XSerializer(serializers.Serializer):
        foo = serializers.ChoiceField(choices=language_choices)
        bar = serializers.ChoiceField(choices=language_choices)

    class XView(generics.RetrieveAPIView):
        serializer_class = XSerializer

    generate_schema('/x', view=XView)
    assert 'encountered multiple names for the same choice set' in capsys.readouterr().err


def test_enum_collision_without_override(capsys):
    class XSerializer(serializers.Serializer):
        foo = serializers.ChoiceField(choices=[('A', 'A'), ('B', 'B')])

    class YSerializer(serializers.Serializer):
        foo = serializers.ChoiceField(choices=[('A', 'A'), ('B', 'B'), ('C', 'C')])

    class XAPIView(APIView):
        @extend_schema(request=XSerializer, responses=YSerializer)
        def post(self, request):
            pass  # pragma: no cover

    generate_schema('x', view=XAPIView)
    assert 'enum naming encountered a collision for field "foo"' in capsys.readouterr().err
