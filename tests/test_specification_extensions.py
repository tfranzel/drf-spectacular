from unittest import mock

import pytest
from rest_framework import serializers
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.views import APIView

from drf_spectacular.contrib.django_oauth_toolkit import DjangoOAuthToolkitScheme
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_serializer
from tests import generate_schema, get_request_schema, get_response_schema


@mock.patch('drf_spectacular.settings.spectacular_settings.EXTENSIONS_INFO', {
    'x-logo': {
        'altText': 'Django REST Framework Logo',
        'backgroundColor': "#ffffff",
        'url': 'https://www.django-rest-framework.org/img/logo.png',
    },
})
def test_root_info_spec_extensions(no_warnings):
    # https://redoc.ly/docs/api-reference-docs/specification-extensions/x-logo/

    class XAPIView(APIView):
        pass

    schema = generate_schema('x', view=XAPIView)
    assert schema['info']['x-logo'] == {
        'altText': 'Django REST Framework Logo',
        'backgroundColor': "#ffffff",
        'url': 'https://www.django-rest-framework.org/img/logo.png',
    }


def test_operation_spec_extensions(no_warnings):
    # https://mrin9.github.io/RapiDoc/api.html#vendor-extensions
    # https://mrin9.github.io/RapiDoc/examples/badges.html#overview

    @extend_schema(
        request=None,
        responses=None,
        extensions={
            'x-badges': [
                {'color': 'red', 'label': 'Beta'},
                {'color': 'orange', 'label': 'Slow'},
            ],
        },
    )
    @api_view(['GET'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('x', view_function=view_func)
    assert schema['paths']['/x']['get']['x-badges'] == [
        {'color': 'red', 'label': 'Beta'},
        {'color': 'orange', 'label': 'Slow'},
    ]


def test_operation_spec_extensions2(no_warnings):
    # https://mrin9.github.io/RapiDoc/api.html#vendor-extensions
    # https://mrin9.github.io/RapiDoc/examples/code-samples.html#get-/code-samples
    # https://redoc.ly/docs/api-reference-docs/specification-extensions/x-code-samples/

    @extend_schema(
        request=None,
        responses=None,
        extensions={
            'x-code-samples': [
                {'lang': 'js', 'label': 'JavaScript', 'source': 'console.log("Hello World");'},
                {'lang': 'python', 'label': 'Python', 'source': 'print("Hello World")'},
            ],
        },
    )
    @api_view(['GET'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('x', view_function=view_func)
    assert schema['paths']['/x']['get']['x-code-samples'] == [
        {'lang': 'js', 'label': 'JavaScript', 'source': 'console.log("Hello World");'},
        {'lang': 'python', 'label': 'Python', 'source': 'print("Hello World")'},
    ]


def test_operation_spec_extensions3(no_warnings):
    # https://openapi-generator.tech/docs/swagger-codegen-migration#body-parameter-name
    # https://github.com/OpenAPITools/openapi-generator/issues/729

    class UserSerializer(serializers.Serializer):
        name = serializers.CharField()
        age = serializers.IntegerField(min_value=0)

    @extend_schema(
        request=UserSerializer,
        responses=UserSerializer,
        extensions={'x-codegen-request-body-name': 'body'},
    )
    @api_view(['PATCH'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('x', view_function=view_func)
    operation = schema['paths']['/x']['patch']
    assert get_request_schema(operation)['$ref'] == '#/components/schemas/PatchedUser'
    assert operation['x-codegen-request-body-name'] == 'body'


def test_serializer_component_spec_extensions(no_warnings):
    # https://docs.apimatic.io/specification-extensions/swagger-codegen-extensions/#dynamic-response-extension

    @extend_schema_serializer(extensions={'x-is-dynamic': True})
    class UserSerializer(serializers.Serializer):
        name = serializers.CharField()
        age = serializers.IntegerField(min_value=0)

    @extend_schema(request=UserSerializer, responses=UserSerializer)
    @api_view(['GET'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('x', view_function=view_func)
    operation = schema['paths']['/x']['get']
    component = schema['components']['schemas']['User']
    assert get_response_schema(operation)['$ref'] == '#/components/schemas/User'
    assert component['x-is-dynamic'] is True


@pytest.mark.contrib('oauth2_provider')
def test_security_spec_extensions(no_warnings):
    # https://mrin9.github.io/RapiDoc/api.html#vendor-extensions
    # https://mrin9.github.io/RapiDoc/examples/oauth-vendor-extension.html#overview
    # https://redoc.ly/docs/api-reference-docs/specification-extensions/x-default-clientid/

    from oauth2_provider.contrib.rest_framework import OAuth2Authentication

    class CustomOAuth2Authentication(OAuth2Authentication):
        pass

    class CustomOAuthToolkitScheme(DjangoOAuthToolkitScheme):
        target_class = CustomOAuth2Authentication

        def get_security_definition(self, auto_schema):
            return {
                **super().get_security_definition(auto_schema),
                'x-client-id': 'my-client-id',
                'x-client-secret': 'my-client-secret',
            }

    @extend_schema(request=None, responses=None)
    @api_view(['GET'])
    @authentication_classes([CustomOAuth2Authentication])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('x', view_function=view_func)
    oauth2 = schema['components']['securitySchemes']['oauth2']
    assert oauth2['x-client-id'] == 'my-client-id'
    assert oauth2['x-client-secret'] == 'my-client-secret'


def test_parameter_spec_extensions(no_warnings):
    # this is a bad example as it is already part of 3.0.3, but others would work accordingly
    # https://github.com/Redocly/redoc/blob/master/docs/redoc-vendor-extensions.md#parameter-object

    @extend_schema(
        responses=None,
        parameters=[
            OpenApiParameter(
                name='q',
                type=str,
                location=OpenApiParameter.QUERY,
                extensions={'x-examples': ['foo', 'bar']}  # don't use this for examples!
            )
        ]
    )
    @api_view(['GET'])
    def view_func(request, format=None):
        pass  # pragma: no cover

    schema = generate_schema('x', view_function=view_func)
    assert schema['paths']['/x']['get']['parameters'][0] == {
        'in': 'query',
        'name': 'q',
        'schema': {'type': 'string'},
        'x-examples': ['foo', 'bar']
    }
