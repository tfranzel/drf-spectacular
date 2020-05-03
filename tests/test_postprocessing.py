from rest_framework import serializers, viewsets, mixins
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
