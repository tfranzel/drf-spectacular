import json
import typing
from enum import Enum, IntEnum, IntFlag
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
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_field
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


class LanguageStrEnumWithCallable(str, Enum):
    EN = 'en'

    @classmethod
    def as_choices(cls):
        return ((cls.EN, 'English'),)


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
    'LanguageEnum': 'tests.test_postprocessing.LanguageStrEnumWithCallable.as_choices'
})
def test_global_enum_naming_override_callable(no_warnings, clear_caches):
    class XSerializer(serializers.Serializer):
        foo = serializers.ChoiceField(choices=LanguageStrEnumWithCallable.as_choices())
        bar = serializers.ChoiceField(choices=LanguageStrEnumWithCallable.as_choices())

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


class ColorChoices(TextChoices):
    # deliberately distinctive values so the set is unique across the test process
    CRIMSON = 'clr_crimson', 'Crimson'
    AZURE = 'clr_azure', 'Azure'


@mock.patch('drf_spectacular.settings.spectacular_settings.ENUM_NAME_FROM_CLASS', True)
def test_enum_name_from_choices_class(capsys, clear_caches):
    class XSerializer(serializers.Serializer):
        # field name differs from the backing Choices class on purpose
        kind = serializers.ChoiceField(choices=ColorChoices.choices)

    class XView(generics.RetrieveAPIView):
        serializer_class = XSerializer

    schema = generate_schema('/x', view=XView)
    # component is named after the Choices class (+ ENUM_SUFFIX), not the field "kind"
    assert 'ColorChoicesEnum' in schema['components']['schemas']['X']['properties']['kind']['$ref']
    assert 'ColorChoicesEnum' in schema['components']['schemas']
    assert 'KindEnum' not in schema['components']['schemas']
    assert 'ColorChoices' not in capsys.readouterr().err  # not flagged ambiguous


class PriorityLevelChoices(IntegerChoices):
    # distinctive integer values so the set is unique across the test process
    LOW = 11, 'Low'
    HIGH = 99, 'High'


@mock.patch('drf_spectacular.settings.spectacular_settings.ENUM_NAME_FROM_CLASS', True)
def test_enum_name_from_integer_choices_class(capsys, clear_caches):
    class XSerializer(serializers.Serializer):
        # field name differs from the backing IntegerChoices class on purpose
        rank = serializers.ChoiceField(choices=PriorityLevelChoices.choices)

    class XView(generics.RetrieveAPIView):
        serializer_class = XSerializer

    schema = generate_schema('/x', view=XView)
    # component is named after the IntegerChoices class (+ ENUM_SUFFIX), not the field "rank"
    enum = schema['components']['schemas']['PriorityLevelChoicesEnum']
    assert 'PriorityLevelChoicesEnum' in schema['components']['schemas']['X']['properties']['rank']['$ref']
    assert 'RankEnum' not in schema['components']['schemas']
    assert enum['type'] == 'integer'
    assert enum['enum'] == [11, 99]
    assert 'PriorityLevelChoices' not in capsys.readouterr().err  # not flagged ambiguous


class GaugeEnum(TextChoices):
    # class name already ends in ENUM_SUFFIX; distinctive values keep the set unique
    LOW = 'gauge_low', 'Low'
    HIGH = 'gauge_high', 'High'


@mock.patch('drf_spectacular.settings.spectacular_settings.ENUM_NAME_FROM_CLASS', True)
def test_enum_name_from_choices_class_no_double_suffix(clear_caches):
    class XSerializer(serializers.Serializer):
        level = serializers.ChoiceField(choices=GaugeEnum.choices)

    class XView(generics.RetrieveAPIView):
        serializer_class = XSerializer

    schema = generate_schema('/x', view=XView)
    schemas = schema['components']['schemas']
    # class name already ends in ENUM_SUFFIX, so it is used as-is, not "GaugeEnumEnum"
    assert 'GaugeEnum' in schemas['X']['properties']['level']['$ref']
    assert 'GaugeEnumEnum' not in schemas
    assert 'LevelEnum' not in schemas


@mock.patch('drf_spectacular.settings.spectacular_settings.ENUM_NAME_FROM_CLASS', True)
@mock.patch('drf_spectacular.settings.spectacular_settings.ENUM_NAME_OVERRIDES', {
    'Shade': 'tests.test_postprocessing.ColorChoices'
})
def test_enum_name_from_choices_class_explicit_override_wins(clear_caches):
    class XSerializer(serializers.Serializer):
        kind = serializers.ChoiceField(choices=ColorChoices.choices)

    class XView(generics.RetrieveAPIView):
        serializer_class = XSerializer

    schema = generate_schema('/x', view=XView)
    # explicit ENUM_NAME_OVERRIDES takes precedence over the auto class-derived name
    assert 'Shade' in schema['components']['schemas']['X']['properties']['kind']['$ref']
    assert 'ColorChoicesEnum' not in schema['components']['schemas']


explicit_clash_choices = [('xclash_1', 'One'), ('xclash_2', 'Two')]


class GadgetEnumChoices(TextChoices):
    # class-derived name (+ suffix) collides with the explicit override name below, but for a
    # different value set; distinctive values keep the set unique across the test process
    SPROCKET = 'gdg_sprocket', 'Sprocket'
    WIDGET = 'gdg_widget', 'Widget'


@mock.patch('drf_spectacular.settings.spectacular_settings.ENUM_NAME_FROM_CLASS', True)
@mock.patch('drf_spectacular.settings.spectacular_settings.ENUM_NAME_OVERRIDES', {
    # explicit name equals the class-derived name (GadgetEnumChoices -> GadgetEnumChoicesEnum)
    # but maps a different value set
    'GadgetEnumChoicesEnum': 'tests.test_postprocessing.explicit_clash_choices'
})
def test_enum_name_from_choices_class_explicit_collision_auto_yields(capsys, clear_caches):
    class XSerializer(serializers.Serializer):
        explicit_field = serializers.ChoiceField(choices=explicit_clash_choices)
        auto_field = serializers.ChoiceField(choices=GadgetEnumChoices.choices)

    class XView(generics.RetrieveAPIView):
        serializer_class = XSerializer

    schema = generate_schema('/x', view=XView)
    schemas = schema['components']['schemas']
    props = schemas['X']['properties']
    # explicit override keeps the contested name; the auto-derived class yields to field-name
    assert 'GadgetEnumChoicesEnum' in props['explicit_field']['$ref']
    assert schemas['GadgetEnumChoicesEnum']['enum'] == ['xclash_1', 'xclash_2']
    assert 'AutoFieldEnum' in props['auto_field']['$ref']
    assert schemas['AutoFieldEnum']['enum'] == ['gdg_sprocket', 'gdg_widget']
    # yielding to an explicit override is a clean resolution, not the ambiguous-warning case:
    # the contested name is not the subject of a warning (other unrelated enums may warn)
    assert 'GadgetEnumChoicesEnum' not in capsys.readouterr().err


@mock.patch('drf_spectacular.settings.spectacular_settings.ENUM_NAME_FROM_CLASS', True)
def test_enum_name_from_choices_class_ambiguous_falls_back(capsys, clear_caches):
    # two distinct Choices classes with an identical value set; defined locally so they are
    # garbage-collected (and drop out of __subclasses__) after this test
    class AmbiguousAChoices(TextChoices):
        X = 'ambig_x', 'X'
        Y = 'ambig_y', 'Y'

    class AmbiguousBChoices(TextChoices):
        X = 'ambig_x', 'X'
        Y = 'ambig_y', 'Y'

    class XSerializer(serializers.Serializer):
        kind = serializers.ChoiceField(choices=AmbiguousAChoices.choices)

    class XView(generics.RetrieveAPIView):
        serializer_class = XSerializer

    schema = generate_schema('/x', view=XView)
    stderr = capsys.readouterr().err
    # the shared value set is ambiguous -> warn and fall back to field-name resolution
    assert 'could not name an enum' in stderr
    assert 'KindEnum' in schema['components']['schemas']
    assert any(n in stderr for n in ('AmbiguousAChoices', 'AmbiguousBChoices'))


@mock.patch('drf_spectacular.settings.spectacular_settings.ENUM_NAME_FROM_CLASS', True)
def test_enum_name_from_choices_class_name_collision_falls_back(capsys, clear_caches):
    # two classes sharing a __name__ but different values (as across apps) would collapse into
    # one component, so neither claims the name. local so they are GC'd after the test.
    # functional API takes (member_name, value) pairs; values deliberately distinctive
    NameClashA = TextChoices('SameNameChoices', [('CA1', 'clash_a1'), ('CA2', 'clash_a2')])
    NameClashB = TextChoices('SameNameChoices', [('CB1', 'clash_b1'), ('CB2', 'clash_b2')])

    class XSerializer(serializers.Serializer):
        # distinct field names so the fallback yields two distinct, correct components
        alpha = serializers.ChoiceField(choices=NameClashA.choices)
        beta = serializers.ChoiceField(choices=NameClashB.choices)

    class XView(generics.RetrieveAPIView):
        serializer_class = XSerializer

    schema = generate_schema('/x', view=XView)
    schemas = schema['components']['schemas']
    stderr = capsys.readouterr().err
    # collision detected -> warn and fall back; neither enum collapses into the other
    assert 'could not name an enum' in stderr
    assert 'SameNameChoicesEnum' not in schemas
    assert schemas['AlphaEnum']['enum'] == ['clash_a1', 'clash_a2']
    assert schemas['BetaEnum']['enum'] == ['clash_b1', 'clash_b2']


@mock.patch('drf_spectacular.settings.spectacular_settings.ENUM_NAME_FROM_CLASS', True)
def test_enum_name_from_native_enum_name_collision_falls_back(capsys, clear_caches):
    # same as the collision test above, but via the type-hint capture path: two native enums
    # sharing a __name__ with different values must not collapse into one component.
    NativeClashA = Enum('SharedName', [('A1', 'native_a1'), ('A2', 'native_a2')])
    NativeClashB = Enum('SharedName', [('B1', 'native_b1'), ('B2', 'native_b2')])

    class XSerializer(serializers.Serializer):
        alpha = serializers.SerializerMethodField()
        beta = serializers.SerializerMethodField()

        @extend_schema_field(NativeClashA)
        def get_alpha(self, obj):
            return 'native_a1'  # pragma: no cover

        @extend_schema_field(NativeClashB)
        def get_beta(self, obj):
            return 'native_b1'  # pragma: no cover

    class XView(generics.RetrieveAPIView):
        serializer_class = XSerializer

    schema = generate_schema('/x', view=XView)
    schemas = schema['components']['schemas']
    stderr = capsys.readouterr().err
    assert 'could not name an enum' in stderr
    assert 'SharedNameEnum' not in schemas
    assert schemas['AlphaEnum']['enum'] == ['native_a1', 'native_a2']
    assert schemas['BetaEnum']['enum'] == ['native_b1', 'native_b2']


class NativeSuit(Enum):
    # native enum.Enum reached via a type hint; distinctive values, field name will differ
    HEART = 'native_heart'
    SPADE = 'native_spade'


class NativePriorityRank(IntEnum):
    # native enum.IntEnum reached via a type hint; distinctive values
    LOW = 4101
    HIGH = 4109


class NativeAccessFlag(IntFlag):
    # native enum.IntFlag reached via a type hint; bitwise (power-of-two) values
    READ = 4096
    WRITE = 8192
    EXECUTE = 16384


@mock.patch('drf_spectacular.settings.spectacular_settings.ENUM_NAME_FROM_CLASS', True)
def test_enum_name_from_native_enum_via_type_hint(capsys, clear_caches):
    class XSerializer(serializers.Serializer):
        suit = serializers.SerializerMethodField()  # field name != class name

        @extend_schema_field(NativeSuit)
        def get_suit(self, obj):
            return 'native_heart'  # pragma: no cover

    class XView(generics.RetrieveAPIView):
        serializer_class = XSerializer

    schema = generate_schema('/x', view=XView)
    schemas = schema['components']['schemas']
    suit = schemas['X']['properties']['suit']
    ref = suit.get('$ref') or suit['allOf'][0]['$ref']  # read-only method field wraps in allOf
    # named after the native Enum class captured at the source (x-spec-enum-name), not field "suit"
    assert 'NativeSuitEnum' in ref
    assert 'NativeSuitEnum' in schemas
    assert 'SuitEnum' not in schemas
    # the x-spec-enum-name helper must never leak into the emitted schema
    assert 'x-spec-enum-name' not in json.dumps(schema)
    assert 'NativeSuit' not in capsys.readouterr().err  # not flagged ambiguous


@mock.patch('drf_spectacular.settings.spectacular_settings.ENUM_NAME_FROM_CLASS', True)
def test_enum_name_from_native_int_enum_via_type_hint(clear_caches):
    class XSerializer(serializers.Serializer):
        rank = serializers.SerializerMethodField()  # field name != class name

        @extend_schema_field(NativePriorityRank)
        def get_rank(self, obj):
            return 4101  # pragma: no cover

    class XView(generics.RetrieveAPIView):
        serializer_class = XSerializer

    schema = generate_schema('/x', view=XView)
    schemas = schema['components']['schemas']
    enum = schemas['NativePriorityRankEnum']
    rank = schemas['X']['properties']['rank']
    ref = rank.get('$ref') or rank['allOf'][0]['$ref']  # read-only method field wraps in allOf
    assert 'NativePriorityRankEnum' in ref
    assert 'RankEnum' not in schemas
    assert enum['type'] == 'integer'
    assert enum['enum'] == [4101, 4109]


@mock.patch('drf_spectacular.settings.spectacular_settings.ENUM_NAME_FROM_CLASS', True)
def test_enum_name_from_native_int_flag_via_type_hint(clear_caches):
    # IntFlag is an Enum subclass, so it flows through the same capture path; pin that the
    # individual (bitwise, power-of-two) member values are enumerated and integer-typed
    class XSerializer(serializers.Serializer):
        access = serializers.SerializerMethodField()  # field name != class name

        @extend_schema_field(NativeAccessFlag)
        def get_access(self, obj):
            return 4096  # pragma: no cover

    class XView(generics.RetrieveAPIView):
        serializer_class = XSerializer

    schema = generate_schema('/x', view=XView)
    schemas = schema['components']['schemas']
    enum = schemas['NativeAccessFlagEnum']
    access = schemas['X']['properties']['access']
    ref = access.get('$ref') or access['allOf'][0]['$ref']  # read-only method field wraps in allOf
    # named after the IntFlag class, not the field "access"
    assert 'NativeAccessFlagEnum' in ref
    assert 'AccessEnum' not in schemas
    assert enum['type'] == 'integer'
    # the member values themselves are enumerated (bitwise combinations are not)
    assert enum['enum'] == [4096, 8192, 16384]


@mock.patch('drf_spectacular.settings.spectacular_settings.ENUM_NAME_FROM_CLASS', True)
def test_enum_name_from_native_enum_ambiguous_falls_back(capsys, clear_caches):
    # two native enums with the same values but different names, via the type-hint capture path.
    # they cannot be told apart by value, so the name is dropped and the warning names both.
    NativeAmbigA = Enum('NativeAmbigA', [('M1', 'ambig_native_1'), ('M2', 'ambig_native_2')])
    NativeAmbigB = Enum('NativeAmbigB', [('M1', 'ambig_native_1'), ('M2', 'ambig_native_2')])

    class XSerializer(serializers.Serializer):
        alpha = serializers.SerializerMethodField()
        beta = serializers.SerializerMethodField()

        @extend_schema_field(NativeAmbigA)
        def get_alpha(self, obj):
            return 'ambig_native_1'  # pragma: no cover

        @extend_schema_field(NativeAmbigB)
        def get_beta(self, obj):
            return 'ambig_native_1'  # pragma: no cover

    class XView(generics.RetrieveAPIView):
        serializer_class = XSerializer

    schema = generate_schema('/x', view=XView)
    schemas = schema['components']['schemas']
    stderr = capsys.readouterr().err
    # ambiguous shared value set -> warn (naming both culprits) and fall back to field names
    assert 'could not name an enum' in stderr
    assert 'NativeAmbigAEnum' in stderr and 'NativeAmbigBEnum' in stderr
    assert 'AlphaEnum' in schemas and 'BetaEnum' in schemas


@mock.patch('drf_spectacular.settings.spectacular_settings.ENUM_NAME_FROM_CLASS', False)
def test_enum_name_from_class_disabled_keeps_field_name(clear_caches):
    # with the setting off, naming is unchanged (field-derived) and no helper field leaks
    class XSerializer(serializers.Serializer):
        suit = serializers.SerializerMethodField()

        @extend_schema_field(NativeSuit)
        def get_suit(self, obj):
            return 'native_heart'  # pragma: no cover

    class XView(generics.RetrieveAPIView):
        serializer_class = XSerializer

    schema = generate_schema('/x', view=XView)
    schemas = schema['components']['schemas']
    suit = schemas['X']['properties']['suit']
    ref = suit.get('$ref') or suit['allOf'][0]['$ref']  # read-only method field wraps in allOf
    assert 'SuitEnum' in ref
    assert 'NativeSuitEnum' not in schemas
    assert 'x-spec-enum-name' not in json.dumps(schema)


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


def test_unsorted_enum(no_warnings):
    enum_override_variations = [
        ('LanguageEnum', [('fr', 'FR'), ('en', 'EN'), ('es', 'ES')]),
        ('LanguageStrEnum', [('en', 'EN'), ('es', 'ES'), ('fr', 'FR')]),
    ]

    for variation, expected_hashed_keys in enum_override_variations:
        with mock.patch(
            'drf_spectacular.settings.spectacular_settings.ENUM_NAME_OVERRIDES',
            {'LanguageEnum': [('es', 'ES'), ('en', 'EN'), ('fr', 'FR')]}
        ):
            _load_enum_name_overrides.cache_clear()
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
