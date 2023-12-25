from unittest import mock

import pytest
from rest_framework import serializers

from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.utils import OpenApiResponse, OpenApiWebhook, extend_schema
from tests import assert_schema, generate_schema


class EventSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    change = serializers.CharField()
    external_id = serializers.CharField(write_only=True)


urlpatterns = []  # type: ignore
openapi_webhooks = [
    OpenApiWebhook(
        name='SubscriptionEvent',
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
    )
]


@mock.patch('drf_spectacular.settings.spectacular_settings.OAS_VERSION', '3.1.0')
def test_webhooks(no_warnings):
    assert_schema(
        generate_schema(None, patterns=[], webhooks=openapi_webhooks),
        'tests/test_webhooks.yml'
    )


@pytest.mark.urls(__name__)
@mock.patch('drf_spectacular.settings.spectacular_settings.OAS_VERSION', '3.1.0')
@mock.patch('drf_spectacular.settings.spectacular_settings.WEBHOOKS', openapi_webhooks)
def test_webhooks_settings(no_warnings):
    assert_schema(
        SchemaGenerator().get_schema(request=None, public=True),
        'tests/test_webhooks.yml'
    )
