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


# Test webhook with custom operationId
subscription_event_with_operation_id = OpenApiWebhook(
    name='SubscriptionEventWithOperationId',
    decorator=extend_schema(
        operation_id='custom_webhook_operation_id',
        summary="webhook with custom operation id",
        description='webhook that should include operationId in the generated schema',
        tags=["webhooks"],
        request={
            'application/json': EventSerializer,
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


@pytest.mark.urls(__name__)
@mock.patch('drf_spectacular.settings.spectacular_settings.OAS_VERSION', '3.1.0')
@mock.patch('drf_spectacular.settings.spectacular_settings.WEBHOOKS', [subscription_event_with_operation_id])
def test_webhooks_operation_id(no_warnings):
    """Test that operationId is included in webhook schema when specified in @extend_schema decorator."""
    assert_schema(
        SchemaGenerator().get_schema(request=None, public=True),
        'tests/test_webhooks_operation_id.yml'
    )


@pytest.mark.urls(__name__)
@mock.patch('drf_spectacular.settings.spectacular_settings.OAS_VERSION', '3.1.0')
@mock.patch('drf_spectacular.settings.spectacular_settings.WEBHOOKS', [subscription_event])
def test_webhooks_no_auto_generated_operation_id(no_warnings):
    """Test that operationId is NOT included for webhooks without explicit operation_id."""
    schema = SchemaGenerator().get_schema(request=None, public=True)

    # Check that webhooks section exists
    assert 'webhooks' in schema
    assert 'SubscriptionEvent' in schema['webhooks']

    # Check that operationId is NOT included when not explicitly provided
    webhook_operation = schema['webhooks']['SubscriptionEvent']['post']
    assert 'operationId' not in webhook_operation


# Test webhook with explicit None operationId (should also not be included)
subscription_event_with_none_operation_id = OpenApiWebhook(
    name='SubscriptionEventWithNoneOperationId',
    decorator=extend_schema(
        operation_id=None,
        summary="webhook with explicit None operation id",
        description='webhook with None operation_id should not include operationId',
        tags=["webhooks"],
        request={
            'application/json': EventSerializer,
        },
        responses={
            200: OpenApiResponse(description='event was successfully received'),
        },
    ),
)


@pytest.mark.urls(__name__)
@mock.patch('drf_spectacular.settings.spectacular_settings.OAS_VERSION', '3.1.0')
@mock.patch('drf_spectacular.settings.spectacular_settings.WEBHOOKS', [subscription_event_with_none_operation_id])
def test_webhooks_explicit_none_operation_id(no_warnings):
    """Test that operationId is NOT included when explicitly set to None."""
    schema = SchemaGenerator().get_schema(request=None, public=True)

    # Check that webhooks section exists
    assert 'webhooks' in schema
    assert 'SubscriptionEventWithNoneOperationId' in schema['webhooks']

    # Check that operationId is NOT included when explicitly set to None
    webhook_operation = schema['webhooks']['SubscriptionEventWithNoneOperationId']['post']
    assert 'operationId' not in webhook_operation
