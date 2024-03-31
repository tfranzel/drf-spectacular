import typing
from enum import Enum
from unittest import mock

import pytest
from django import __version__ as DJANGO_VERSION
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.views import APIView

try:
    from django.db.models.enums import IntegerChoices, TextChoices
except ImportError:
    TextChoices = object  # type: ignore  # django < 3.0 handling
    IntegerChoices = object  # type: ignore  # django < 3.0 handling

from drf_spectacular.plumbing import _load_enum_name_overrides, list_hash, load_enum_name_overrides
from drf_spectacular.utils import OpenApiParameter, extend_schema
from tests import assert_schema, generate_schema

language_choices = (
    ('en', 'en'),
    ('es', 'es'),
    ('ru', 'ru'),
    ('cn', 'cn'),
)

blank_null_language_choices = (
    ('en', 'en'),
    ('es', 'es'),
    ('ru', 'ru'),
    ('cn', 'cn'),
    ('', 'not provided'),
    (None, 'unknown'),
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


blank_null_language_list = ['en', '', None]


class BlankNullLanguageEnum(Enum):
    EN = 'en'
    BLANK = ''
    NULL = None


class BlankNullLanguageStrEnum(str, Enum):
    EN = 'en'
    BLANK = ''
    # These will still be included since the values get cast to strings so 'None' != None
    NULL = None


if '3' < DJANGO_VERSION < '5':
    # Django 5 added a sanity check that prohibits None
    class BlankNullLanguageChoices(TextChoices):
        EN = 'en'
        BLANK = ''
        # These will still be included since the values get cast to strings so 'None' != None
        NULL = None


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


@mock.patch('drf_spectacular.settings.spectacular_settings.ENUM_NAME_OVERRIDES', {
    'LanguageEnum': 'tests.test_postprocessing.blank_null_language_choices'
})
def test_global_enum_naming_override_with_blank_and_none(no_warnings, clear_caches):
    """Test that choices with blank values can still have their name overridden."""
    class XSerializer(serializers.Serializer):
        foo = serializers.ChoiceField(choices=blank_null_language_choices)
        bar = serializers.ChoiceField(choices=blank_null_language_choices)

    class XView(generics.RetrieveAPIView):
        serializer_class = XSerializer

    schema = generate_schema('/x', view=XView)
    foo_data = schema['components']['schemas']['X']['properties']['foo']
    bar_data = schema['components']['schemas']['X']['properties']['bar']

    assert len(foo_data['oneOf']) == 3
    assert len(bar_data['oneOf']) == 3

    foo_ref_values = [ref_object['$ref'] for ref_object in foo_data['oneOf']]
    bar_ref_values = [ref_object['$ref'] for ref_object in bar_data['oneOf']]

    assert foo_ref_values == [
        '#/components/schemas/LanguageEnum',
        '#/components/schemas/BlankEnum',
        '#/components/schemas/NullEnum'
    ]
    assert bar_ref_values == [
        '#/components/schemas/LanguageEnum',
        '#/components/schemas/BlankEnum',
        '#/components/schemas/NullEnum'
    ]


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
    enum_override_variations = [
        ('language_list', [('en', 'en')]),
        ('LanguageEnum', [('en', 'EN')]),
        ('LanguageStrEnum', [('en', 'EN')]),
    ]
    if DJANGO_VERSION > '3':
        enum_override_variations += [
            ('LanguageChoices', [('en', 'En')]),
            ('LanguageChoices.choices', [('en', 'En')])
        ]

    for variation, expected_hashed_keys in enum_override_variations:
        with mock.patch(
            'drf_spectacular.settings.spectacular_settings.ENUM_NAME_OVERRIDES',
            {'LanguageEnum': f'tests.test_postprocessing.{variation}'}
        ):
            _load_enum_name_overrides.cache_clear()
            assert list_hash(expected_hashed_keys) in load_enum_name_overrides()


def test_enum_override_variations_with_blank_and_null(no_warnings):
    enum_override_variations = [
        ('blank_null_language_list', [('en', 'en')]),
        ('BlankNullLanguageEnum', [('en', 'EN')]),
        ('BlankNullLanguageStrEnum', [('en', 'EN'), ('None', 'NULL')])
    ]
    if '3' < DJANGO_VERSION < '5':
        # Django 5 added a sanity check that prohibits None
        enum_override_variations += [
            ('BlankNullLanguageChoices', [('en', 'En'), ('None', 'Null')]),
            ('BlankNullLanguageChoices.choices', [('en', 'En'), ('None', 'Null')])
        ]

    for variation, expected_hashed_keys in enum_override_variations:
        with mock.patch(
            'drf_spectacular.settings.spectacular_settings.ENUM_NAME_OVERRIDES',
            {'LanguageEnum': f'tests.test_postprocessing.{variation}'}
        ):
            _load_enum_name_overrides.cache_clear()
            # Should match after None and blank strings are removed
            assert list_hash(expected_hashed_keys) in load_enum_name_overrides()


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


def test_uuid_choices(no_warnings):

    import uuid

    class XSerializer(serializers.Serializer):
        foo = serializers.ChoiceField(
            choices=[
                (uuid.UUID('93d7527f-de3c-4a76-9cc2-5578675630d4'), 'baz'),
                (uuid.UUID('47a4b873-409e-4e43-81d5-fafc3faeb849'), 'bar')
            ]
        )

    class XAPIView(APIView):
        @extend_schema(responses=XSerializer)
        def get(self, request):
            pass  # pragma: no cover

    schema = generate_schema('x', view=XAPIView)

    assert 'FooEnum' in schema['components']['schemas']
    assert schema['components']['schemas']['FooEnum']['enum'] == [
        uuid.UUID('93d7527f-de3c-4a76-9cc2-5578675630d4'),
        uuid.UUID('47a4b873-409e-4e43-81d5-fafc3faeb849')
    ]


@pytest.mark.skipif(DJANGO_VERSION < '3', reason='Not available before Django 3.0')
def test_equal_choices_different_semantics(no_warnings):

    class Health(IntegerChoices):
        OK = 0
        FAIL = 1

    class Status(IntegerChoices):
        GREEN = 0
        RED = 1

    class Test(IntegerChoices):
        A = 0, _("test group A")
        B = 1, _("test group B")

    class XSerializer(serializers.Serializer):
        some_health = serializers.ChoiceField(choices=Health.choices)
        some_status = serializers.ChoiceField(choices=Status.choices)
        some_test = serializers.ChoiceField(choices=Test.choices)

    class XAPIView(APIView):
        @extend_schema(responses=XSerializer)
        def get(self, request):
            pass  # pragma: no cover

    # This should not generate a warning even though the enum list is identical
    # in both Enums. We now also differentiate the Enums by their labels.
    schema = generate_schema('x', view=XAPIView)

    assert schema['components']['schemas']['SomeHealthEnum'] == {
        'enum': [0, 1], 'type': 'integer', 'description': '* `0` - Ok\n* `1` - Fail'
    }
    assert schema['components']['schemas']['SomeStatusEnum'] == {
        'enum': [0, 1], 'type': 'integer', 'description': '* `0` - Green\n* `1` - Red'
    }
    assert schema['components']['schemas']['SomeTestEnum'] == {
        'enum': [0, 1], 'type': 'integer', 'description': '* `0` - test group A\n* `1` - test group B',
    }


@mock.patch('drf_spectacular.settings.spectacular_settings.ENUM_NAME_OVERRIDES', {
    'VoteChoices': 'tests.test_postprocessing.vote_choices'
})
def test_enum_suffix(no_warnings, clear_caches):
    """Test that enums generated have the suffix from the settings."""
    # check variations of suffix
    enum_suffix_variations = ['Type', 'Enum', 'Testing', '']
    for variation in enum_suffix_variations:
        with mock.patch('drf_spectacular.settings.spectacular_settings.ENUM_SUFFIX', variation):
            schema = generate_schema('a', AViewset)

            assert f'Null{variation}' in schema['components']['schemas']
            assert f'Blank{variation}' in schema['components']['schemas']
            assert f'Language{variation}' in schema['components']['schemas']
            # vote choices is overridden, so should not have the suffix added
            assert f'Vote{variation}' not in schema['components']['schemas']
            assert 'VoteChoices' in schema['components']['schemas']
