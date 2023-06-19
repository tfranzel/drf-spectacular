import sys
from typing import List
from unittest import mock

import pytest
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action

# Use 3.9 instead of 3.8 version because of missing __required_keys__ feature,
# which allows for a consistent test schema over different versions.
if sys.version_info >= (3, 9):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

from drf_spectacular.contrib.djangorestframework_camel_case import camelize_serializer_fields
from drf_spectacular.utils import OpenApiParameter, extend_schema
from tests import assert_schema, generate_schema


class NestedObject2(TypedDict):
    field_seven: int
    field_eight: str


class NestedObject(TypedDict):
    field_three: int
    field_four: str
    field_five: NestedObject2
    field_six: List[NestedObject2]
    field_ignored: int


class FakeSerializer(serializers.Serializer):
    field_one = serializers.CharField()
    field_two = serializers.CharField()
    field_ignored = serializers.CharField()

    field_nested = serializers.SerializerMethodField()
    field_nested_ignored = serializers.SerializerMethodField()

    def get_field_nested(self) -> NestedObject:  # type: ignore
        pass  # pragma: no cover

    def get_field_nested_ignored(self) -> NestedObject:  # type: ignore
        pass  # pragma: no cover


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="field_parameter",
            description="filter_parameter",
            required=False,
            type=str,
        ),
    ]
)
class FakeViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = FakeSerializer

    @extend_schema(responses=FakeSerializer)
    @action(detail=False, serializer_class=FakeSerializer)
    def home(self, request):
        ...  # pragma: no cover


@mock.patch(
    'drf_spectacular.settings.spectacular_settings.POSTPROCESSING_HOOKS',
    [camelize_serializer_fields]
)
@mock.patch(
    'djangorestframework_camel_case.settings.api_settings.JSON_UNDERSCOREIZE',
    {
        'no_underscore_before_number': False,
        'ignore_fields': ('field_nested_ignored',),
        'ignore_keys': ('field_ignored',),
    }
)
@pytest.mark.contrib('djangorestframework_camel_case')
def test_camelize_serializer_fields(no_warnings):
    assert_schema(
        generate_schema('a_b_c', FakeViewset),
        'tests/contrib/test_djangorestframework_camel_case.yml'
    )


@mock.patch(
    'django.conf.settings.MIDDLEWARE',
    ['djangorestframework_camel_case.middleware.CamelCaseMiddleWare'],
    create=True
)
@mock.patch(
    'drf_spectacular.settings.spectacular_settings.POSTPROCESSING_HOOKS',
    [camelize_serializer_fields]
)
@mock.patch(
    'djangorestframework_camel_case.settings.api_settings.JSON_UNDERSCOREIZE',
    {
        'no_underscore_before_number': False,
        'ignore_fields': ('field_nested_ignored',),
        'ignore_keys': ('field_ignored',),
    }
)
@pytest.mark.contrib('djangorestframework_camel_case')
def test_camelize_middleware(no_warnings):
    assert_schema(
        generate_schema('a_b_c', FakeViewset),
        'tests/contrib/test_djangorestframework_camel_case.yml',
        reverse_transforms=[lambda x: x.replace("field_parameter", "fieldParameter")]
    )
