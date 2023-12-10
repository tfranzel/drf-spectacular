from typing import TYPE_CHECKING
from unittest import mock

from django.contrib.auth.models import User
from rest_framework import fields, mixins, pagination, permissions, serializers, viewsets
from rest_framework.authentication import BaseAuthentication
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.extensions import (
    OpenApiAuthenticationExtension, OpenApiSerializerExtension, OpenApiSerializerFieldExtension,
    OpenApiViewExtension,
)
from drf_spectacular.plumbing import (
    ResolvedComponent, build_array_type, build_basic_type, build_object_type, force_instance,
)
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import Direction, extend_schema, extend_schema_field, extend_schema_view
from tests import generate_schema, get_response_schema
from tests.models import SimpleModel, SimpleSerializer

if TYPE_CHECKING:
    from drf_spectacular.openapi import AutoSchema


class Base64Field(fields.Field):
    pass  # pragma: no cover


def test_serializer_field_extension(no_warnings):
    class Base64FieldExtension(OpenApiSerializerFieldExtension):
        target_class = 'tests.test_extensions.Base64Field'

        def map_serializer_field(self, auto_schema, direction):
            return build_basic_type(OpenApiTypes.BYTE)

    class XSerializer(serializers.Serializer):
        hash = Base64Field()

    class XViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
        serializer_class = XSerializer

    schema = generate_schema('x', XViewset)
    assert schema['components']['schemas']['X']['properties']['hash']['type'] == 'string'
    assert schema['components']['schemas']['X']['properties']['hash']['format'] == 'byte'


def test_serializer_field_extension_can_return_none(no_warnings):
    """Field extensions can return None, which should exclude them from schema"""

    class BlindBase64Field(fields.Field):
        pass  # pragma: no cover

    class Base64FieldExtension(OpenApiSerializerFieldExtension):
        target_class = BlindBase64Field

        def map_serializer_field(self, auto_schema, direction):
            return None

    # At least 1 field is required to generate schema, include 'other'
    class XSerializer(serializers.Serializer):
        hash = BlindBase64Field()
        other = fields.CharField()

    class XViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
        serializer_class = XSerializer

    schema = generate_schema('x', XViewset)

    # field 'hash' is missing from the schema output
    assert schema['components']['schemas']['X'] == {
        'type': 'object', 'properties': {'other': {'type': 'string'}}, 'required': ['other']
    }


class Base32Field(fields.Field):
    pass  # pragma: no cover


def test_serializer_field_extension_with_breakout(no_warnings):
    class Base32FieldExtension(OpenApiSerializerFieldExtension):
        target_class = 'tests.test_extensions.Base32Field'

        def get_name(self):
            return 'FieldComponentName'

        def map_serializer_field(self, auto_schema, direction):
            return build_basic_type(OpenApiTypes.BYTE)

    class XSerializer(serializers.Serializer):
        hash = Base32Field()

    class XViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
        serializer_class = XSerializer

    schema = generate_schema('x', XViewset)
    assert schema['components']['schemas']['FieldComponentName'] == {
        'type': 'string', 'format': 'byte'
    }


class XView(APIView):
    """ underspecified library view """
    def get(self):
        """ docstring for GET """
        return Response(1.234)  # pragma: no cover


def test_view_extension(no_warnings):
    class FixXView(OpenApiViewExtension):
        target_class = 'tests.test_extensions.XView'

        def view_replacement(self):
            class Fixed(self.target_class):
                @extend_schema(responses=OpenApiTypes.FLOAT)
                def get(self, request):
                    pass  # pragma: no cover

            return Fixed

    schema = generate_schema('x', view=XView)
    operation = schema['paths']['/x']['get']
    assert get_response_schema(operation)['type'] == 'number'
    assert operation['description'] == 'docstring for GET'


@api_view()
def x_view_function(request):
    """ underspecified library view """
    return Response(1.234)  # pragma: no cover


def test_view_function_extension(no_warnings):
    class FixXFunctionView(OpenApiViewExtension):
        target_class = 'tests.test_extensions.x_view_function'

        def view_replacement(self):
            fixed = extend_schema(responses=OpenApiTypes.FLOAT)(self.target_class)
            return fixed

    schema = generate_schema('x', view_function=x_view_function)
    operation = schema['paths']['/x']['get']
    assert get_response_schema(operation)['type'] == 'number'
    assert operation['description'].strip() == 'underspecified library view'


def test_extension_not_found_for_installed_app(capsys):
    class FixXFunctionView(OpenApiViewExtension):
        target_class = 'tests.test_extensions.NotExistingClass'

        def view_replacement(self):
            pass  # pragma: no cover

    OpenApiViewExtension.get_match(object())
    assert 'target class was not found' in capsys.readouterr().err


class MultiHeaderAuth(BaseAuthentication):
    pass


def test_multi_auth_scheme_extension(no_warnings):
    class MultiHeaderAuthExtension(OpenApiAuthenticationExtension):
        target_class = 'tests.test_extensions.MultiHeaderAuth'
        name = ['apiKey', 'appId']

        def get_security_definition(self, auto_schema):
            return [
                {'type': 'apiKey', 'in': 'header', 'name': 'X-API-KEY'},
                {'type': 'apiKey', 'in': 'header', 'name': 'X-APP-ID'},
            ]

    class XViewset(viewsets.ReadOnlyModelViewSet):
        queryset = SimpleModel.objects.none()
        serializer_class = SimpleSerializer
        authentication_classes = [MultiHeaderAuth]
        permission_classes = [permissions.IsAuthenticated]

    schema = generate_schema('/x', XViewset)
    assert schema['components']['securitySchemes'] == {
        'apiKey': {'type': 'apiKey', 'in': 'header', 'name': 'X-API-KEY'},
        'appId': {'type': 'apiKey', 'in': 'header', 'name': 'X-APP-ID'}
    }
    assert schema['paths']['/x/']['get']['security'] == [{'apiKey': [], 'appId': []}]


def test_serializer_list_extension(no_warnings):

    class CustomListSerializer(serializers.ListSerializer):
        def to_representation(self, data):
            return {'foo': 1, 'data': super().to_representation(data)}   # pragma: no cover

    # ListSerializer can be injected either via Meta attribute or by overriding many_init()
    class XSerializer(serializers.ModelSerializer):
        class Meta:
            model = SimpleModel
            fields = '__all__'
            list_serializer_class = CustomListSerializer

    class CustomListExtension(OpenApiSerializerExtension):
        target_class = CustomListSerializer

        def map_serializer(self, auto_schema, direction):
            component = auto_schema.resolve_serializer(self.target.child, direction)
            schema = build_object_type(
                properties={'foo': build_basic_type(int), 'data': build_array_type(component.ref)}
            )
            list_component = ResolvedComponent(
                name=f'{component.name}List',
                type=ResolvedComponent.SCHEMA,
                object=self.target.child,
                schema=schema
            )
            auto_schema.registry.register_on_missing(list_component)
            return list_component.ref

    class XViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
        serializer_class = XSerializer

    schema = generate_schema('x', XViewset)
    op_schema = get_response_schema(schema['paths']['/x/']['get'])
    assert op_schema == {'$ref': '#/components/schemas/XList'}
    assert schema['components']['schemas']['XList'] == {
        'type': 'object',
        'properties': {
            'foo': {'type': 'integer'},
            'data': {'type': 'array', 'items': {'$ref': '#/components/schemas/X'}}
        }
    }


@mock.patch('drf_spectacular.settings.spectacular_settings.COMPONENT_SPLIT_REQUEST', True)
def test_serializer_envelope_through_extension(no_warnings):
    class EnvelopeMixin:
        pass

    # actual enveloping not implemented. This could be done internally with
    # to_representation or externally with a custom Renderer
    class XSerializer(EnvelopeMixin, serializers.ModelSerializer):
        name = serializers.CharField()

        class Meta:
            model = SimpleModel
            fields = '__all__'
            envelope = 'foo'  # some arbitrary addition to Meta for example

    class EnvelopeFix(OpenApiSerializerExtension):
        target_class = EnvelopeMixin
        match_subclasses = True

        def get_name(self, auto_schema: 'AutoSchema', direction: Direction):
            if direction == 'request':
                return None
            else:
                return f"Enveloped{self.target.__class__.__name__}"

        def map_serializer(self, auto_schema: 'AutoSchema', direction: Direction):
            if direction == 'request':
                return auto_schema._map_serializer(self.target, direction, bypass_extensions=True)
            else:
                component = auto_schema.resolve_serializer(self.target, direction, bypass_extensions=True)
                if not component:
                    return {}
                return build_object_type(
                    properties={self.target.Meta.envelope: component.ref}
                )

    class XViewset(viewsets.ModelViewSet):
        serializer_class = XSerializer
        queryset = SimpleModel.objects.none()

    schema = generate_schema('/x', XViewset)
    assert 'X' in schema['components']['schemas']
    assert 'EnvelopedX' in schema['components']['schemas']
    assert 'XRequest' in schema['components']['schemas']
    assert 'PatchedXRequest' in schema['components']['schemas']


def test_serializer_method_pagination_through_extension(no_warnings):
    class PaginationWrapper(serializers.BaseSerializer):
        def __init__(self, serializer_class, pagination_class, **kwargs):
            self.serializer_class = serializer_class
            self.pagination_class = pagination_class
            super().__init__(**kwargs)

    class PaginationWrapperExtension(OpenApiSerializerExtension):
        target_class = PaginationWrapper  # this can also be an import string

        def get_name(self, auto_schema, direction):
            return auto_schema.get_paginated_name(
                auto_schema._get_serializer_name(
                    serializer=force_instance(self.target.serializer_class),
                    direction=direction
                )
            )

        def map_serializer(self, auto_schema, direction):
            component = auto_schema.resolve_serializer(self.target.serializer_class, direction)
            paginated_schema = self.target.pagination_class().get_paginated_response_schema(component.ref)
            return paginated_schema

    class XSerializer(serializers.ModelSerializer):
        method = serializers.SerializerMethodField()

        @extend_schema_field(
            PaginationWrapper(
                serializer_class=SimpleSerializer,
                pagination_class=pagination.LimitOffsetPagination
            )
        )
        def get_method(self, obj):
            pass  # pragma: no cover

        class Meta:
            fields = '__all__'
            model = SimpleModel

    class XViewset(viewsets.ModelViewSet):
        serializer_class = XSerializer
        queryset = SimpleModel.objects.none()

    schema = generate_schema('x', XViewset)

    assert 'Simple' in schema['components']['schemas']
    assert 'PaginatedSimpleList' in schema['components']['schemas']
    assert schema['components']['schemas']['PaginatedSimpleList']['properties']['results'] == {
        '$ref': '#/components/schemas/Simple'
    }


def test_serializer_with_dynamic_fields(no_warnings):
    class DynamicFieldsModelSerializer(serializers.ModelSerializer):
        """
        A ModelSerializer that takes an additional `fields` argument that
        controls which fields should be displayed.

        Taken from (only added ref_name)
        https://www.django-rest-framework.org/api-guide/serializers/#dynamically-modifying-fields
        """
        def __init__(self, *args, **kwargs):
            # Don't pass the 'fields' arg up to the superclass
            fields = kwargs.pop('fields', None)
            self.ref_name = kwargs.pop('ref_name', None)  # only change to original version!

            # Instantiate the superclass normally
            super().__init__(*args, **kwargs)

            if fields is not None:
                # Drop any fields that are not specified in the `fields` argument.
                allowed = set(fields)
                existing = set(self.fields)
                for field_name in existing - allowed:
                    self.fields.pop(field_name)

    class UserSerializer(DynamicFieldsModelSerializer):
        class Meta:
            model = User
            fields = ['id', 'username', 'email']

    class DynamicFieldsModelSerializerExtension(OpenApiSerializerExtension):
        target_class = DynamicFieldsModelSerializer  # this can also be an import string
        match_subclasses = True

        def map_serializer(self, auto_schema: 'AutoSchema', direction: Direction):
            return auto_schema._map_serializer(self.target, direction, bypass_extensions=True)

        def get_name(self, auto_schema, direction):
            return self.target.ref_name

    @extend_schema_view(
        list=extend_schema(responses=UserSerializer(fields=['id'], ref_name='CompactUser'))
    )
    class XViewset(viewsets.ModelViewSet):
        serializer_class = UserSerializer
        queryset = User.objects.none()

    schema = generate_schema('x', XViewset)

    assert schema['components']['schemas']['User']['properties'] == {
        'id': {'type': 'integer', 'readOnly': True},
        'username': {
            'type': 'string',
            'description': 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
            'pattern': '^[\\w.@+-]+$',
            'maxLength': 150
        },
        'email': {'type': 'string', 'format': 'email', 'title': 'Email address', 'maxLength': 254}
    }
    assert schema['components']['schemas']['CompactUser']['properties'] == {
        'id': {'type': 'integer', 'readOnly': True}
    }
