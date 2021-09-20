import typing
from enum import Enum
from unittest import mock

import pytest
from django import __version__ as DJANGO_VERSION
from rest_framework import generics, mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.views import APIView

try:
    from django.db.models.enums import TextChoices
except ImportError:
    TextChoices = object  # type: ignore  # django < 3.0 handling

from drf_spectacular.plumbing import list_hash, load_enum_name_overrides
from drf_spectacular.utils import OpenApiParameter, extend_schema
from tests import assert_schema, generate_schema

language_choices = (
    ('en', 'en'),
    ('es', 'es'),
    ('ru', 'ru'),
    ('cn', 'cn'),
)

vote_choices = (
    (1, 'Positive'),
    (0, 'Neutral'),
    (-1, 'Negative'),
)

language_list = ['en']


class LanguageEnum(Enum):
    EN = 'en'


class LanguageStrEnum(str, Enum):
    EN = 'en'


class LanguageChoices(TextChoices):
    EN = 'en'


class ASerializer(serializers.Serializer):
    language = serializers.ChoiceField(choices=language_choices)
    vote = serializers.ChoiceField(choices=vote_choices)


class BSerializer(serializers.Serializer):
    language = serializers.ChoiceField(choices=language_choices, allow_blank=True, allow_null=True)


class AViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ASerializer

    @extend_schema(responses=BSerializer)
    @action(detail=False, serializer_class=BSerializer)
    def selection(self, request):
        pass  # pragma: no cover


def test_postprocessing(no_warnings):
    schema = generate_schema('a', AViewset)
    assert_schema(schema, 'tests/test_postprocessing.yml')


@mock.patch(
    'drf_spectacular.settings.spectacular_settings.ENUM_ADD_EXPLICIT_BLANK_NULL_CHOICE', False
)
def test_no_blank_and_null_in_enum_choices(no_warnings):
    schema = generate_schema('a', AViewset)
    assert 'NullEnum' not in schema['components']['schemas']
    assert 'BlankEnum' not in schema['components']['schemas']
    assert 'oneOf' not in schema['components']['schemas']['B']['properties']['language']


@mock.patch('drf_spectacular.settings.spectacular_settings.ENUM_NAME_OVERRIDES', {
    'LanguageEnum': 'tests.test_postprocessing.language_choices'
})
def test_global_enum_naming_override(no_warnings, clear_caches):
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
        foo = serializers.ChoiceField(choices=[('A', 'A')])

    class YSerializer(serializers.Serializer):
        foo = serializers.ChoiceField(choices=[('A', 'A'), ('B', 'B')])

    class ZSerializer(serializers.Serializer):
        foo = serializers.ChoiceField(choices=[('A', 'A'), ('B', 'B')])

    class XAPIView(APIView):
        @extend_schema(responses=ZSerializer)
        def get(self, request):
            pass  # pragma: no cover

        @extend_schema(request=XSerializer, responses=YSerializer)
        def post(self, request):
            pass  # pragma: no cover

    generate_schema('x', view=XAPIView)
    assert 'enum naming encountered a non-optimally resolvable' in capsys.readouterr().err


def test_resolvable_enum_collision(no_warnings):
    class XSerializer(serializers.Serializer):
        foo = serializers.ChoiceField(choices=[('A', 'A')])

    class YSerializer(serializers.Serializer):
        foo = serializers.ChoiceField(choices=[('A', 'A'), ('B', 'B')])

    class XAPIView(APIView):
        @extend_schema(request=XSerializer, responses=YSerializer)
        def post(self, request):
            pass  # pragma: no cover

    schema = generate_schema('x', view=XAPIView)
    assert 'XFooEnum' in schema['components']['schemas']
    assert 'YFooEnum' in schema['components']['schemas']


@mock.patch('drf_spectacular.settings.spectacular_settings.COMPONENT_SPLIT_PATCH', True)
@mock.patch('drf_spectacular.settings.spectacular_settings.COMPONENT_SPLIT_REQUEST', True)
def test_enum_resolvable_collision_with_patched_and_request_splits():
    class XSerializer(serializers.Serializer):
        foo = serializers.ChoiceField(choices=[('A', 'A')])

    class YSerializer(serializers.Serializer):
        foo = serializers.ChoiceField(choices=[('A', 'A'), ('B', 'B')])

    class XViewset(viewsets.GenericViewSet):
        @extend_schema(request=XSerializer, responses=YSerializer)
        def create(self, request):
            pass  # pragma: no cover

        @extend_schema(
            request=XSerializer,
            responses=YSerializer,
            parameters=[OpenApiParameter('id', int, OpenApiParameter.PATH)]
        )
        def partial_update(self, request):
            pass  # pragma: no cover

    schema = generate_schema('/x', XViewset)
    components = schema['components']['schemas']
    assert 'XFooEnum' in components and 'YFooEnum' in components
    assert '/XFooEnum' in components['XRequest']['properties']['foo']['$ref']
    assert '/XFooEnum' in components['PatchedXRequest']['properties']['foo']['$ref']


def test_enum_override_variations(no_warnings):
    enum_override_variations = ['language_list', 'LanguageEnum', 'LanguageStrEnum']
    if DJANGO_VERSION > '3':
        enum_override_variations += ['LanguageChoices', 'LanguageChoices.choices']

    for variation in enum_override_variations:
        with mock.patch(
            'drf_spectacular.settings.spectacular_settings.ENUM_NAME_OVERRIDES',
            {'LanguageEnum': f'tests.test_postprocessing.{variation}'}
        ):
            load_enum_name_overrides.cache_clear()
            assert list_hash(['en']) in load_enum_name_overrides()


@mock.patch('drf_spectacular.settings.spectacular_settings.ENUM_NAME_OVERRIDES', {
    'LanguageEnum': 'tests.test_postprocessing.NOTEXISTING'
})
def test_enum_override_loading_fail(capsys, clear_caches):
    load_enum_name_overrides()
    assert 'unable to load choice override for LanguageEnum' in capsys.readouterr().err


@pytest.mark.skipif(DJANGO_VERSION < '3', reason='Not available before Django 3.0')
def test_textchoice_annotation(no_warnings):
    class QualityChoices(TextChoices):
        GOOD = 'GOOD'
        BAD = 'BAD'

    class XSerializer(serializers.Serializer):
        quality_levels = serializers.SerializerMethodField()

        def get_quality_levels(self, obj) -> typing.List[QualityChoices]:
            return [QualityChoices.GOOD, QualityChoices.BAD]  # pragma: no cover

    class XAPIView(APIView):
        @extend_schema(responses=XSerializer)
        def get(self, request):
            pass  # pragma: no cover

    schema = generate_schema('x', view=XAPIView)
    assert 'QualityLevelsEnum' in schema['components']['schemas']
    assert schema['components']['schemas']['X']['properties']['quality_levels'] == {
        'type': 'array',
        'items': {'$ref': '#/components/schemas/QualityLevelsEnum'},
        'readOnly': True
    }
