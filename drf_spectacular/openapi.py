import inspect
import re
import sys
import typing
from collections import OrderedDict
from decimal import Decimal
from operator import attrgetter
from urllib.parse import urljoin

import uritemplate
from django.core import validators
from django.db import models
from django.utils.encoding import force_str
from rest_framework import exceptions, permissions, renderers, serializers, views, viewsets
from rest_framework.fields import _UnvalidatedField, empty
from rest_framework.schemas.generators import BaseSchemaGenerator
from rest_framework.schemas.inspectors import ViewInspector
from rest_framework.schemas.utils import get_pk_description, is_list_view

from drf_spectacular.app_settings import spectacular_settings
from drf_spectacular.types import OpenApiTypes, resolve_basic_type, PYTHON_TYPE_MAPPING, OPENAPI_TYPE_MAPPING
from drf_spectacular.utils import PolymorphicResponse

AUTHENTICATION_SCHEMES = {
    cls.authentication_class: cls for cls in spectacular_settings.SCHEMA_AUTHENTICATION_CLASSES
}


def warn(msg):
    print(f'WARNING: {msg}', file=sys.stderr)


def anyisinstance(obj, type_list):
    return any([isinstance(obj, t) for t in type_list])


def force_serializer_instance(serializer):
    if inspect.isclass(serializer) and issubclass(serializer, serializers.Serializer):
        return serializer()
    else:
        return serializer


class ComponentRegistry:
    def __init__(self):
        self.schemas = {}
        self.security_schemes = {}

    def get_components(self):
        return {
            'securitySchemes': self.security_schemes,
            'schemas': self.schemas,
        }


class SchemaGenerator(BaseSchemaGenerator):
    def __init__(self, *args, **kwargs):
        self.registry = ComponentRegistry()
        super().__init__(*args, **kwargs)

    def create_view(self, callback, method, request=None):
        """
        customized create_view which is called when all routes are traversed. part of this
        is instatiating views with default params. in case of custom routes (@action) the
        custom AutoSchema is injected properly through 'initkwargs' on view. However, when
        decorating plain views like retrieve, this initialization logic is not running.
        Therefore forcefully set the schema if @extend_schema decorator was used.
        """
        view = super().create_view(callback, method, request)

        if isinstance(view, viewsets.GenericViewSet) or isinstance(view, viewsets.ViewSet):
            action = getattr(view, view.action)
        elif isinstance(view, views.APIView):
            action = getattr(view, method.lower())
        else:
            raise RuntimeError('not supported subclass. Must inherit from APIView or subclass of APIView')

        if hasattr(action, 'kwargs') and 'schema' in action.kwargs:
            # might already be properly set in case of @action but overwrite for all cases
            view.schema = action.kwargs['schema']

        return view

    def parse(self, request=None):
        result = {}

        paths, view_endpoints = self._get_paths_and_endpoints(request)

        # Only generate the path prefix for paths that will be included
        if not paths:
            return None

        # Iterate endpoints generating per method path operations.
        for path, method, view in view_endpoints:
            if not self.has_view_permissions(path, method, view):
                continue
            # keep reference to schema as every access yields a fresh object (descriptor pattern)
            schema = view.schema
            operation = schema.get_operation(path, method, self.registry)
            # Normalise path for any provided mount url.
            if path.startswith('/'):
                path = path[1:]
            path = urljoin(self.url or '/', path)

            result.setdefault(path, {})
            result[path][method.lower()] = operation

        return result

    def get_schema(self, request=None, public=False):
        """
        Generate a OpenAPI schema.
        """
        self._initialise_endpoints()

        schema = {
            'openapi': '3.0.3',
            'servers': [
                {'url': self.url or 'http://127.0.0.1:8000'},
            ],
            'info': {
                'title': self.title or '',
                'version': getattr(self, 'version', None) or '0.0.0',  # attr for drf<3.11, fallback to prevent invalid schema
                'description': self.description or '',
            },
            'paths': self.parse(None if public else request),
            'components': self.registry.get_components(),
        }
        return schema


class AutoSchema(ViewInspector):
    method_mapping = {
        'get': 'retrieve',
        'post': 'create',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy',
    }

    def get_operation(self, path, method, registry):
        self.registry = registry
        operation = {}

        operation['operationId'] = self.get_operation_id(path, method)
        operation['description'] = self.get_description(path, method)

        parameters = sorted(
            [
                *self._get_path_parameters(path, method),
                *self._get_filter_parameters(path, method),
                *self._get_pagination_parameters(path, method),
                *self.get_extra_parameters(path, method),
            ],
            key=lambda parameter: parameter.get('name')
        )
        if parameters:
            operation['parameters'] = parameters

        tags = self.get_tags(path, method)
        if tags:
            operation['tags'] = tags

        request_body = self._get_request_body(path, method)
        if request_body:
            operation['requestBody'] = request_body

        auth = self.get_auth(path, method)
        if auth:
            operation['security'] = auth

        operation['responses'] = self._get_response_bodies(path, method)

        return operation

    def get_extra_parameters(self, path, method):
        """ override this for custom behaviour """
        return []

    def get_description(self, path, method):
        """ override this for custom behaviour """
        action_or_method = getattr(self.view, getattr(self.view, 'action', method.lower()), None)
        view_doc = inspect.getdoc(self.view) or ''
        action_doc = inspect.getdoc(action_or_method) or ''
        return action_doc or view_doc

    def get_auth(self, path, method):
        """ override this for custom behaviour """
        view_auths = [
            self.resolve_authentication(method, a) for a in self.view.get_authenticators()
        ]
        view_perms = [p.__class__ for p in self.view.get_permissions()]

        if permissions.AllowAny in view_perms:
            view_auths.append({})
        elif permissions.IsAuthenticatedOrReadOnly in view_perms and method not in ('PUT', 'PATCH', 'POST'):
            view_auths.append({})
        return view_auths

    def get_request_serializer(self, path, method):
        """ override this for custom behaviour """
        return self._get_serializer(path, method)

    def get_response_serializers(self, path, method):
        """ override this for custom behaviour """
        return self._get_serializer(path, method)

    def get_tags(self, path, method) -> typing.List[str]:
        """ override this for custom behaviour """
        tokenized_path = self._tokenize_path(path)
        # use first non-parameter path part as tag
        return tokenized_path[:1]

    def get_operation_id(self, path, method):
        """ override this for custom behaviour """
        tokenized_path = self._tokenize_path(path)
        # replace dashes as they can be problematic later in code generation
        tokenized_path = [t.replace('-', '_') for t in tokenized_path]

        if is_list_view(path, method, self.view):
            action = 'list'
        else:
            action = self.method_mapping[method.lower()]

        return '_'.join(tokenized_path + [action])

    def _tokenize_path(self, path):
        # remove path prefix
        path = re.sub(
            pattern=spectacular_settings.SCHEMA_PATH_PREFIX,
            repl='',
            string=path,
            flags=re.IGNORECASE
        )
        # cleanup and tokenize remaining parts.
        path = path.rstrip('/').lstrip('/').split('/')
        # remove path variables and empty tokens
        return [t for t in path if t and not t.startswith('{')]

    def _get_path_parameters(self, path, method):
        """
        Return a list of parameters from templated path variables.
        """
        model = getattr(getattr(self.view, 'queryset', None), 'model', None)
        parameters = []
        schema = resolve_basic_type(OpenApiTypes.STR)
        description = ''

        for variable in uritemplate.variables(path):
            if not model:
                warn(f'{self.view.__class__} had no queryset attribute. could not estimate type of parameter "{variable}". defaulting to string.')
            else:
                try:
                    model_field = model._meta.get_field(variable)
                    schema = self._map_model_field(model_field)

                    if model_field.help_text:
                        description = force_str(model_field.help_text)
                    elif model_field.primary_key:
                        description = get_pk_description(model, model_field)
                except Exception:
                    pass

            parameters.append({
                "name": variable,
                "in": "path",
                "required": True,
                "description": description,
                'schema': schema,
            })

        return parameters

    def _get_filter_parameters(self, path, method):
        if not self._allows_filters(path, method):
            return []
        parameters = []
        for filter_backend in self.view.filter_backends:
            parameters += filter_backend().get_schema_operation_parameters(self.view)
        return parameters

    def _allows_filters(self, path, method):
        """
        Determine whether to include filter Fields in schema.

        Default implementation looks for ModelViewSet or GenericAPIView
        actions/methods that cause filtering on the default implementation.
        """
        if getattr(self.view, 'filter_backends', None) is None:
            return False
        if hasattr(self.view, 'action'):
            return self.view.action in ["list", "retrieve", "update", "partial_update", "destroy"]
        return method.lower() in ["get", "put", "patch", "delete"]

    def _get_pagination_parameters(self, path, method):
        view = self.view

        if not is_list_view(path, method, view):
            return []

        paginator = self._get_paginator()
        if not paginator:
            return []

        return paginator.get_schema_operation_parameters(view)

    def _map_choicefield(self, field):
        choices = list(OrderedDict.fromkeys(field.choices))  # preserve order and remove duplicates
        if all(isinstance(choice, bool) for choice in choices):
            type = 'boolean'
        elif all(isinstance(choice, int) for choice in choices):
            type = 'integer'
        elif all(isinstance(choice, (int, float, Decimal)) for choice in choices):  # `number` includes `integer`
            # Ref: https://tools.ietf.org/html/draft-wright-json-schema-validation-00#section-5.21
            type = 'number'
        elif all(isinstance(choice, str) for choice in choices):
            type = 'string'
        else:
            type = None

        mapping = {
            # The value of `enum` keyword MUST be an array and SHOULD be unique.
            # Ref: https://tools.ietf.org/html/draft-wright-json-schema-validation-00#section-5.20
            'enum': choices
        }

        # If We figured out `type` then and only then we should set it. It must be a string.
        # Ref: https://swagger.io/docs/specification/data-models/data-types/#mixed-type
        # It is optional but it can not be null.
        # Ref: https://tools.ietf.org/html/draft-wright-json-schema-validation-00#section-5.21
        if type:
            mapping['type'] = type
        return mapping

    def _map_model_field(self, field):
        # in django 3.0 checking both auto and int field is not required but in 2.2 it is
        if anyisinstance(field, [models.AutoField, models.IntegerField]):
            return resolve_basic_type(OpenApiTypes.INT)
        # TODO make this save for django version not having those fields
        # elif anyisinstance(field, [models.SmallAutoField, models.SmallIntegerField]):
        #     return resolve_basic_type(OpenApiTypes.INT)
        # elif anyisinstance(field, [models.BigAutoField, models.BigIntegerField]):
        #     return resolve_basic_type(OpenApiTypes.INT)
        elif isinstance(field, models.UUIDField):
            return resolve_basic_type(OpenApiTypes.UUID)
        else:
            warn(f'could not resolve model field "{field}" due to missing mapping')
            return resolve_basic_type(OpenApiTypes.STR)

    def _map_serializer_field(self, method, field):
        if isinstance(field, serializers.ListSerializer):
            return {
                'type': 'array',
                'items': self.resolve_serializer(method, field.child)
            }

        if isinstance(field, serializers.Serializer):
            return self.resolve_serializer(method, field, nested=True)

        # Related fields.
        if isinstance(field, serializers.ManyRelatedField):
            return {
                'type': 'array',
                'items': self._map_serializer_field(method, field.child_relation)
            }

        if isinstance(field, serializers.PrimaryKeyRelatedField):
            model = getattr(field.queryset, 'model', None)

            if not model:
                warn(f'unable to map model field {field} due to missing model. defaulting to "string"')
                return resolve_basic_type(OpenApiTypes.STR)
            else:
                return self._map_model_field(model._meta.pk)

        # ChoiceFields (single and multiple).
        # Q:
        # - Is 'type' required?
        # - can we determine the TYPE of a choicefield?
        if isinstance(field, serializers.MultipleChoiceField):
            return {
                'type': 'array',
                'items': self._map_choicefield(field)
            }

        if isinstance(field, serializers.ChoiceField):
            return self._map_choicefield(field)

        if isinstance(field, serializers.ListField):
            mapping = {
                'type': 'array',
                'items': {},
            }
            # TODO check this
            if not isinstance(field.child, _UnvalidatedField):
                map_field = self._map_serializer_field(method, field.child)
                items = {
                    "type": map_field.get('type')
                }
                if 'format' in map_field:
                    items['format'] = map_field.get('format')
                mapping['items'] = items
            return mapping

        # DateField and DateTimeField type is string
        if isinstance(field, serializers.DateField):
            return resolve_basic_type(OpenApiTypes.DATE)

        if isinstance(field, serializers.DateTimeField):
            return resolve_basic_type(OpenApiTypes.DATETIME)

        if isinstance(field, serializers.EmailField):
            return resolve_basic_type(OpenApiTypes.EMAIL)

        if isinstance(field, serializers.URLField):
            return resolve_basic_type(OpenApiTypes.URI)

        if isinstance(field, serializers.UUIDField):
            return resolve_basic_type(OpenApiTypes.UUID)

        if isinstance(field, serializers.IPAddressField):
            if 'IPv4' == field.protocol:
                return resolve_basic_type(OpenApiTypes.IP4)
            elif 'IPv6' == field.protocol:
                return resolve_basic_type(OpenApiTypes.IP6)
            else:
                return resolve_basic_type(OpenApiTypes.STR)

        # DecimalField has multipleOf based on decimal_places
        if isinstance(field, serializers.DecimalField):
            content = {
                'type': 'number'
            }
            if field.decimal_places:
                content['multipleOf'] = float('.' + (field.decimal_places - 1) * '0' + '1')
            if field.max_whole_digits:
                content['maximum'] = int(field.max_whole_digits * '9') + 1
                content['minimum'] = -content['maximum']
            self._map_min_max(field, content)
            return content

        if isinstance(field, serializers.FloatField):
            content = resolve_basic_type(OpenApiTypes.FLOAT)
            self._map_min_max(field, content)
            return content

        if isinstance(field, serializers.IntegerField):
            content = resolve_basic_type(OpenApiTypes.INT)
            self._map_min_max(field, content)
            # 2147483647 is max for int32_size, so we use int64 for format
            if int(content.get('maximum', 0)) > 2147483647 or int(content.get('minimum', 0)) > 2147483647:
                content['format'] = 'int64'
            return content

        if isinstance(field, serializers.FileField):
            return resolve_basic_type(OpenApiTypes.BINARY)

        if isinstance(field, serializers.SerializerMethodField):
            method = getattr(field.parent, field.method_name)
            return self._map_type_hint(method)

        if isinstance(field, serializers.BooleanField):
            return resolve_basic_type(OpenApiTypes.BOOL)

        if anyisinstance(field, [serializers.JSONField, serializers.DictField, serializers.HStoreField]):
            return resolve_basic_type(OpenApiTypes.OBJECT)

        if isinstance(field, serializers.CharField):
            return resolve_basic_type(OpenApiTypes.STR)

        # TODO serializer fields
        # serializers.ReadOnlyField
        # serializers.CreateOnlyDefault
        # serializers.RegexField

        warn(f'could not resolve serializer field {field}. defaulting to "string"')
        return resolve_basic_type(OpenApiTypes.STR)

    def _map_min_max(self, field, content):
        if field.max_value:
            content['maximum'] = field.max_value
        if field.min_value:
            content['minimum'] = field.min_value

    def _map_serializer(self, method, serializer, nested=False):
        required = []
        properties = {}

        for field in serializer.fields.values():
            if isinstance(field, serializers.HiddenField):
                continue

            if field.required:
                required.append(field.field_name)

            schema = self._map_serializer_field(method, field)
            if field.read_only:
                schema['readOnly'] = True
            if field.write_only:
                schema['writeOnly'] = True
            if field.allow_null:
                schema['nullable'] = True
            if field.default is not None and field.default != empty and not callable(field.default):
                schema['default'] = field.default
            if field.help_text:
                schema['description'] = str(field.help_text)

            self._map_field_validators(field, schema)

            properties[field.field_name] = schema

        result = {
            'type': 'object',
            'properties': properties
        }
        if required and method != 'PATCH':
            result['required'] = required

        return result

    def _map_field_validators(self, field, schema):
        for v in field.validators:
            # "Formats such as "email", "uuid", and so on, MAY be used even though undefined by this specification."
            # https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.3.md#data-types
            if isinstance(v, validators.EmailValidator):
                schema['format'] = 'email'
            if isinstance(v, validators.URLValidator):
                schema['format'] = 'uri'
            if isinstance(v, validators.RegexValidator):
                schema['pattern'] = v.regex.pattern
            elif isinstance(v, validators.MaxLengthValidator):
                attr_name = 'maxLength'
                if isinstance(field, serializers.ListField):
                    attr_name = 'maxItems'
                schema[attr_name] = v.limit_value
            elif isinstance(v, validators.MinLengthValidator):
                attr_name = 'minLength'
                if isinstance(field, serializers.ListField):
                    attr_name = 'minItems'
                schema[attr_name] = v.limit_value
            elif isinstance(v, validators.MaxValueValidator):
                schema['maximum'] = v.limit_value
            elif isinstance(v, validators.MinValueValidator):
                schema['minimum'] = v.limit_value
            elif isinstance(v, validators.DecimalValidator):
                if v.decimal_places:
                    schema['multipleOf'] = float('.' + (v.decimal_places - 1) * '0' + '1')
                if v.max_digits:
                    digits = v.max_digits
                    if v.decimal_places is not None and v.decimal_places > 0:
                        digits -= v.decimal_places
                    schema['maximum'] = int(digits * '9') + 1
                    schema['minimum'] = -schema['maximum']

    def _map_type_hint(self, method, hint=None):
        if not hint:
            hint = typing.get_type_hints(method).get('return')

        if hasattr(method, '_spectacular_annotation'):
            if isinstance(force_serializer_instance(method._spectacular_annotation), serializers.BaseSerializer):
                return self._map_serializer_field(method, force_serializer_instance(method._spectacular_annotation))
            elif method._spectacular_annotation in OPENAPI_TYPE_MAPPING:
                return resolve_basic_type(method._spectacular_annotation)
            else:
                warn(f'unknown decorated type "{repr(method._spectacular_annotation)}". defaulting to string')
                return resolve_basic_type(OpenApiTypes.STR)
        elif hint in PYTHON_TYPE_MAPPING:
            return resolve_basic_type(hint)
        else:
            warn(f'type hint for SerializerMethodField function "{method.__name__}" is unknown. defaulting to string.')
            return resolve_basic_type(OpenApiTypes.STR)

    def _get_paginator(self):
        pagination_class = getattr(self.view, 'pagination_class', None)
        if pagination_class:
            return pagination_class()
        return None

    def map_parsers(self, path, method):
        return list(map(attrgetter('media_type'), self.view.parser_classes))

    def map_renderers(self, path, method):
        media_types = []
        for renderer in self.view.renderer_classes:
            # BrowsableAPIRenderer not relevant to OpenAPI spec
            if renderer == renderers.BrowsableAPIRenderer:
                continue
            media_types.append(renderer.media_type)
        return media_types

    def _get_serializer(self, path, method):
        view = self.view

        if not hasattr(view, 'get_serializer'):
            return None

        try:
            return view.get_serializer()
        except exceptions.APIException:
            warn(
                '{}.get_serializer() raised an exception during '
                'schema generation. Serializer fields will not be '
                'generated for {} {}.'.format(view.__class__.__name__, method, path)
            )
            return None

    def _get_request_body(self, path, method):
        if method not in ('PUT', 'PATCH', 'POST'):
            return {}

        serializer = force_serializer_instance(self.get_request_serializer(path, method))

        if isinstance(serializer, serializers.Serializer):
            schema = self.resolve_serializer(method, serializer)
        else:
            warn(
                f'could not resolve request body for {method} {path}. defaulting to generic '
                'free-form object. (maybe annotate a Serializer class?)'
            )
            schema = {
                'type': 'object',
                'additionalProperties': {},  # https://github.com/swagger-api/swagger-codegen/issues/1318
                'description': 'Unspecified request body',
            }

        # serializer has no fields so skip content enumeration
        if not schema:
            return {}

        return {
            'content': {
                request_media_types: {'schema': schema} for request_media_types in self.map_parsers(path, method)
            }
        }

    def _get_response_bodies(self, path, method):
        response_serializers = self.get_response_serializers(path, method)

        if anyisinstance(force_serializer_instance(response_serializers), [serializers.Serializer, PolymorphicResponse]):
            if method == 'DELETE':
                return {'204': {'description': 'No response body'}}
            return {'200': self._get_response_for_code(path, method, response_serializers)}
        elif isinstance(response_serializers, dict):
            # custom handling for overriding default return codes with @extend_schema
            return {
                code: self._get_response_for_code(path, method, serializer)
                for code, serializer in response_serializers.items()
            }
        else:
            warn(f'could not resolve response for {method} {path}. defaulting to generic free-form object.')
            schema = {
                'type': 'object',
                'description': 'Unspecified response body',
            }
            return {'200': self._get_response_for_code(path, method, schema)}

    def _get_response_for_code(self, path, method, serializer):
        # convenience feature: auto instantiate serializer classes
        serializer = force_serializer_instance(serializer)

        if not serializer:
            return {'description': 'No response body'}
        elif isinstance(serializer, serializers.Serializer):
            schema = self.resolve_serializer(method, serializer)
            if not schema:
                return {'description': 'No response body'}
        elif isinstance(serializer, PolymorphicResponse):
            # custom handling for @extend_schema's injection of polymorphic responses
            schemas = []

            for serializer in serializer.serializers:
                assert isinstance(serializer, serializers.Serializer)
                schema_option = self.resolve_serializer(method, serializer)
                if schema_option:
                    schemas.append(schema_option)

            schema = {
                'oneOf': schemas,
                'discriminator': {
                    'propertyName': serializer.resource_type_field_name
                }
            }
        elif isinstance(serializer, serializers.ListSerializer):
            schema = self.resolve_serializer(method, serializer.child)
        elif isinstance(serializer, dict):
            # bypass processing and use given schema directly
            schema = serializer
        else:
            raise ValueError('Serializer type unsupported')

        if isinstance(serializer, serializers.ListSerializer) or is_list_view(path, method, self.view):
            # TODO i fear is_list_view is not covering all the cases
            schema = {
                'type': 'array',
                'items': schema,
            }
            paginator = self._get_paginator()
            if paginator:
                schema = paginator.get_paginated_response_schema(schema)

        return {
            'content': {
                mt: {'schema': schema} for mt in self.map_renderers(path, method)
            },
            # Description is required by spec, but descriptions for each response code don't really
            # fit into our model. Description is therefore put into the higher level slots.
            # https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.3.md#responseObject
            'description': ''
        }

    def _get_serializer_name(self, method, serializer, nested):
        name = serializer.__class__.__name__

        if name.endswith('Serializer'):
            name = name[:-10]
        if method == 'PATCH' and not serializer.read_only:  # TODO maybe even use serializer.partial
            name = 'Patched' + name

        return name

    def resolve_authentication(self, method, authentication):
        auth_scheme = AUTHENTICATION_SCHEMES.get(authentication.__class__)

        if not auth_scheme:
            raise ValueError('no auth scheme registered for {}'.format(authentication.__name__))

        if auth_scheme.name not in self.registry.security_schemes:
            self.registry.security_schemes[auth_scheme.name] = auth_scheme.schema

        return {auth_scheme.name: []}

    def resolve_serializer(self, method, serializer, nested=False):
        name = self._get_serializer_name(method, serializer, nested)

        if name not in self.registry.schemas:
            # add placeholder to prevent recursion loop
            self.registry.schemas[name] = None

            schema = self._map_serializer(method, serializer, nested)
            # empty serializer - usually a transactional serializer.
            # no need to put it explicitly in the spec
            if not schema['properties']:
                del self.registry.schemas[name]
                return {}
            else:
                self.registry.schemas[name] = schema

        return {'$ref': '#/components/schemas/{}'.format(name)}
