from rest_framework import serializers, viewsets
from rest_framework.decorators import action

from drf_spectacular.utils import OpenApiCallback, OpenApiResponse, extend_schema, inline_serializer
from tests import assert_schema, generate_schema
from tests.models import SimpleModel, SimpleSerializer


class EventSerializer(serializers.Serializer):
    change = serializers.CharField()


class XViewset(viewsets.ReadOnlyModelViewSet):
    queryset = SimpleModel.objects.none()
    serializer_class = SimpleSerializer

    @extend_schema(
        request=inline_serializer(
            name='SubscribeSerializer',
            fields={'callbackUrl': serializers.URLField()},
        ),
        responses=None,
        callbacks=[
            OpenApiCallback(
                name='SubscriptionEvent',
                path='{$request.body#/callbackUrl}',
                decorator=extend_schema(
                    summary="some summary",
                    description='pushes events to callbackUrl as "application/x-www-form-urlencoded"',
                    request={
                        'application/x-www-form-urlencoded': EventSerializer,
                    },
                    responses={
                        200: OpenApiResponse(description='event was successfully received'),
                        '4XX': OpenApiResponse(description='event will be retried shortly'),
                    },
                ),
            ),
        ]
    )
    @action(detail=False, methods=['POST'])
    def subscription(self):
        pass  # pragma: no cover

    @extend_schema(
        request=inline_serializer(
            name='HealthSerializer',
            fields={'callbackUrl': serializers.URLField()},
        ),
        responses=None,
        callbacks=[
            OpenApiCallback(
                name='HealthEvent',
                path='{$request.body#/callbackUrl}',
                decorator={
                    'post': extend_schema(
                        request=EventSerializer,
                        responses=OpenApiResponse(description='status new ack'),
                    ),
                    'delete': extend_schema(
                        deprecated=True,
                        responses={200: OpenApiResponse(description='status expiration')},
                    ),
                    # raw schema
                    'patch': {
                        'requestBody': {'content': {'application/yaml': {'schema': {'type': 'integer'}}}},
                        'responses': {'200': {'description': 'Raw schema'}}
                    },
                },
            ),
        ]
    )
    @action(detail=False, methods=['POST'])
    def health(self):
        pass  # pragma: no cover


def test_callbacks(no_warnings):
    assert_schema(
        generate_schema('/x', XViewset),
        'tests/test_callbacks.yml'
    )
