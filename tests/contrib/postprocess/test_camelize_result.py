from unittest import mock

from rest_framework import serializers, viewsets, mixins
from rest_framework.decorators import action

from drf_spectacular.utils import extend_schema
from tests import generate_schema
from drf_spectacular.contrib.postprocess import camelize_result


class FakeSerializer(serializers.Serializer):
    field_one = serializers.CharField()
    field_two = serializers.CharField()


class FakeViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = FakeSerializer

    @extend_schema(responses=FakeSerializer)
    @action(detail=False, serializer_class=FakeSerializer)
    def home(self, request):
        ...  # pragma: no cover


def test_should_camelize_result():
    with mock.patch(
        'drf_spectacular.settings.spectacular_settings.POSTPROCESSING_HOOKS', [
            camelize_result
        ]
    ):
        schema = generate_schema('a', FakeViewset)

        fake = schema['components']['schemas']['Fake']['properties']

        assert 'fieldOne' in fake
        assert 'fieldTwo' in fake
