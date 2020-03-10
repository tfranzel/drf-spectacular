import enum
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID


class OpenApiTypes(enum.Enum):
    """
    Basic types known to the OpenApi specification or at least
    common format extension of it.

    - Use BYTE for base64 encoded data wrapped in a string
    - Use BINARY for raw binary data
    - Use OBJECT for arbitrary free-form object (usually a dict)

    """
    FLOAT = enum.auto()
    BOOL = enum.auto()
    STR = enum.auto()
    BYTE = enum.auto()  # base64 encoded
    BINARY = enum.auto()
    INT = enum.auto()
    UUID = enum.auto()
    URI = enum.auto()
    IP4 = enum.auto()
    IP6 = enum.auto()
    HOSTNAME = enum.auto()
    DECIMAL = enum.auto()
    DATETIME = enum.auto()
    DATE = enum.auto()
    EMAIL = enum.auto()
    OBJECT = enum.auto()
    NONE = enum.auto()


# make a copy with dict() before modifying returned dict
OPENAPI_TYPE_MAPPING = {
    OpenApiTypes.FLOAT: {'type': 'number', 'format': 'float'},
    OpenApiTypes.BOOL: {'type': 'boolean'},
    OpenApiTypes.STR: {'type': 'string'},
    OpenApiTypes.BYTE: {'type': 'string', 'format': 'byte'},
    OpenApiTypes.BINARY: {'type': 'string', 'format': 'binary'},
    OpenApiTypes.INT: {'type': 'integer'},
    OpenApiTypes.UUID: {'type': 'string', 'format': 'uuid'},
    OpenApiTypes.URI: {'type': 'string', 'format': 'uri'},
    OpenApiTypes.IP4: {'type': 'string', 'format': 'ipv4'},
    OpenApiTypes.IP6: {'type': 'string', 'format': 'ipv6'},
    OpenApiTypes.HOSTNAME: {'type': 'string', 'format': 'hostname'},
    OpenApiTypes.DECIMAL: {'type': 'number', 'format': 'double'},
    OpenApiTypes.DATETIME: {'type': 'string', 'format': 'date-time'},
    OpenApiTypes.DATE: {'type': 'string', 'format': 'date'},
    OpenApiTypes.EMAIL: {'type': 'string', 'format': 'email'},
    OpenApiTypes.OBJECT: {'type': 'object', 'additionalProperties': {}},
    OpenApiTypes.NONE: {},
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
}
