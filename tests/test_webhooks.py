from unittest import mock

import pytest
from rest_framework import serializers

from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.utils import OpenApiResponse, OpenApiWebhook, extend_schema
from tests import assert_schema


class EventSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    change = serializers.CharField()
    external_id = serializers.CharField(write_only=True)


urlpatterns = []  # type: ignore

subscription_event = OpenApiWebhook(
    name='SubscriptionEvent',
    decorator=extend_schema(
        summary="some summary",
        description='pushes events to a webhook url as "application/x-www-form-urlencoded"',
        tags=["webhooks"],
        request={
            'application/x-www-form-urlencoded': EventSerializer,
        },
        responses={
            200: OpenApiResponse(description='event was successfully received'),
            '4XX': OpenApiResponse(description='event will be retried shortly'),
        },
    ),
)


@pytest.mark.urls(__name__)
@mock.patch('drf_spectacular.settings.spectacular_settings.OAS_VERSION', '3.1.0')
@mock.patch('drf_spectacular.settings.spectacular_settings.WEBHOOKS', [subscription_event])
def test_webhooks_settings(no_warnings):
    assert_schema(
        SchemaGenerator().get_schema(request=None, public=True),
        'tests/test_webhooks.yml'
    )
