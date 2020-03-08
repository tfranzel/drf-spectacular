import inspect

from rest_framework.settings import api_settings

from drf_spectacular.types import resolve_basic_type


class PolymorphicProxySerializer:
    """
    This class is to be used with @extend_schema to signal a request/response
    might be polymorphic (accepts/returns data possibly from different serializers)

    Beware that this is not a real serializer and therefore is not derived
    from serializers.Serializer. It *cannot* be used in views as serializer_class
    or as field in a actual serializer. You likely want to handle this in the view
    method.
    """
    def __init__(self, component_name, serializers, resource_type_field_name):
        self.component_name = component_name
        self.serializers = serializers
        self.resource_type_field_name = resource_type_field_name


class OpenApiSchemaBase:
    """ reusable base class for objects that can be translated to a schema """

    def to_schema(self):
        raise NotImplementedError('translation to schema required.')


class ExtraParameter(OpenApiSchemaBase):
    QUERY = 'query'
    PATH = 'path'
    HEADER = 'header'

    def __init__(self, name, type=str, location=QUERY, required=False, description=''):
        self.name = name
        self.type = type
        self.location = location
        self.required = required
        self.description = description

    def to_schema(self):
        schema = {
            'in': self.location,
            'name': self.name,
            'schema': resolve_basic_type(self.type),
            'description': self.description,
        }
        if self.location != self.PATH:
            schema['required'] = self.required
        return schema


def extend_schema(
        operation=None,
        operation_id=None,
        extra_parameters=None,
        responses=None,
        request=None,
        auth=None,
        description=None,
):
    """
    TODO some heavy explaining

    :param operation:
    :param operation_id:
    :param extra_parameters:
    :param responses:
    :param request:
    :param auth:
    :param description:
    :return:
    """

    def decorator(f):
        class ExtendedSchema(api_settings.DEFAULT_SCHEMA_CLASS):
            def get_operation(self, path, method, registry):
                if operation:
                    return operation
                return super().get_operation(path, method, registry)

            def get_operation_id(self, path, method):
                if operation_id:
                    return operation_id
                return super().get_operation_id(path, method)

            def get_extra_parameters(self, path, method):
                if extra_parameters:
                    return [
                        p.to_schema() if isinstance(p, OpenApiSchemaBase) else p
                        for p in extra_parameters
                    ]
                return super().get_extra_parameters(path, method)

            def get_auth(self, path, method):
                if auth:
                    return auth
                return super().get_auth(path, method)

            def get_request_serializer(self, path, method):
                if request:
                    return request
                return super().get_request_serializer(path, method)

            def get_response_serializers(self, path, method):
                if responses:
                    return responses
                return super().get_response_serializers(path, method)

            def get_description(self, path, method):
                if description:
                    return description
                return super().get_description(path, method)

        if inspect.isclass(f):
            class ExtendedView(f):
                schema = ExtendedSchema()

            return ExtendedView
        elif callable(f):
            # custom actions have kwargs in their context, others don't. create it so our create_view
            # implementation can overwrite the default schema
            if not hasattr(f, 'kwargs'):
                f.kwargs = {}

            # this simulates what @action is actually doing. somewhere along the line in this process
            # the schema is picked up from kwargs and used. it's involved my dear friends.
            f.kwargs['schema'] = ExtendedSchema()
            return f
        else:
            return f

    return decorator


def extend_schema_field(response):
    """
    Decorator for the "field" kind. Can be used with ``SerializerMethodField()`` (annotate the actual method)
    or with custom ``serializers.Field`` implementations.

    If your custom serializer field base class is already the desired type, decoration is not necessary. To
    override the discovered base class type, you can decorate your custom field class.

    Always takes precedence over other mechanisms (e.g. type hints, auto-discovery).

    :param response: accepts a Serializer or OpenApiTypes
    :return:
    """
    def decorator(f):
        f._spectacular_annotation = response
        return f

    return decorator
