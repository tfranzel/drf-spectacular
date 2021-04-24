import enum
import typing
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from drf_spectacular.settings import spectacular_settings


class OpenApiTypes(enum.Enum):
    """
    Basic types known to the OpenApi specification or at least
    common format extension of it.

    - Use BYTE for base64 encoded data wrapped in a string
    - Use BINARY for raw binary data
    - Use OBJECT for arbitrary free-form object (usually a dict)

    """
    NUMBER = enum.auto()
    FLOAT = enum.auto()
    DOUBLE = enum.auto()
    BOOL = enum.auto()
    STR = enum.auto()
    BYTE = enum.auto()  # base64 encoded
    BINARY = enum.auto()
    PASSWORD = enum.auto()
    INT = enum.auto()
    INT32 = enum.auto()
    INT64 = enum.auto()
    UUID = enum.auto()
    URI = enum.auto()
    IP4 = enum.auto()
    IP6 = enum.auto()
    HOSTNAME = enum.auto()
    DECIMAL = enum.auto()
    DATETIME = enum.auto()
    DATE = enum.auto()
    TIME = enum.auto()
    DURATION = enum.auto()
    EMAIL = enum.auto()
    OBJECT = enum.auto()
    NONE = enum.auto()
    ANY = enum.auto()


def build_generic_type():
    if spectacular_settings.GENERIC_ADDITIONAL_PROPERTIES is None:
        return {'type': 'object'}
    elif spectacular_settings.GENERIC_ADDITIONAL_PROPERTIES == 'bool':
        return {'type': 'object', 'additionalProperties': True}
    else:
        return {'type': 'object', 'additionalProperties': {}}


# make a copy with dict() before modifying returned dict
OPENAPI_TYPE_MAPPING = {
    OpenApiTypes.NUMBER: {'type': 'number'},
    OpenApiTypes.FLOAT: {'type': 'number', 'format': 'float'},
    OpenApiTypes.DOUBLE: {'type': 'number', 'format': 'double'},
    OpenApiTypes.BOOL: {'type': 'boolean'},
    OpenApiTypes.STR: {'type': 'string'},
    OpenApiTypes.BYTE: {'type': 'string', 'format': 'byte'},
    OpenApiTypes.BINARY: {'type': 'string', 'format': 'binary'},
    OpenApiTypes.PASSWORD: {'type': 'string', 'format': 'password'},
    OpenApiTypes.INT: {'type': 'integer'},
    OpenApiTypes.INT32: {'type': 'integer', 'format': 'int32'},
    OpenApiTypes.INT64: {'type': 'integer', 'format': 'int64'},
    OpenApiTypes.UUID: {'type': 'string', 'format': 'uuid'},
    OpenApiTypes.URI: {'type': 'string', 'format': 'uri'},
    OpenApiTypes.IP4: {'type': 'string', 'format': 'ipv4'},
    OpenApiTypes.IP6: {'type': 'string', 'format': 'ipv6'},
    OpenApiTypes.HOSTNAME: {'type': 'string', 'format': 'hostname'},
    OpenApiTypes.DECIMAL: {'type': 'number', 'format': 'double'},
    OpenApiTypes.DATETIME: {'type': 'string', 'format': 'date-time'},
    OpenApiTypes.DATE: {'type': 'string', 'format': 'date'},
    OpenApiTypes.TIME: {'type': 'string', 'format': 'time'},
    OpenApiTypes.DURATION: {'type': 'string', 'format': 'duration'},  # ISO 8601
    OpenApiTypes.EMAIL: {'type': 'string', 'format': 'email'},
    OpenApiTypes.OBJECT: build_generic_type(),
    OpenApiTypes.ANY: {},
    OpenApiTypes.NONE: None,
}


PYTHON_TYPE_MAPPING = {
    str: OpenApiTypes.STR,
    float: OpenApiTypes.FLOAT,
    bool: OpenApiTypes.BOOL,
    bytes: OpenApiTypes.BINARY,
    int: OpenApiTypes.INT,
    UUID: OpenApiTypes.UUID,
    Decimal: OpenApiTypes.DECIMAL,
    datetime: OpenApiTypes.DATETIME,
    date: OpenApiTypes.DATE,
    dict: OpenApiTypes.OBJECT,
    typing.Any: OpenApiTypes.ANY,
    None: OpenApiTypes.NONE,
}

DJANGO_PATH_CONVERTER_MAPPING = {
    'int': OpenApiTypes.INT,
    'path': OpenApiTypes.STR,
    'slug': OpenApiTypes.STR,
    'str': OpenApiTypes.STR,
    'uuid': OpenApiTypes.UUID,
    'drf_format_suffix': OpenApiTypes.STR,
}
