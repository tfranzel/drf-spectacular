From `drf-yasg` to OpenAPI 3
==============================

`drf-yasg <https://github.com/axnsan12/drf-yasg>`_ is an excellent library and the most popular
choice for generating OpenAPI 2.0 / Swagger schemas with DRF. Unfortunately, it currently does
not provide OpenAPI 3 support. Migration from `drf-yasg` to `drf-spectacular` requires
only minor modifications.

- ``@swagger_auto_schema`` is largely equivalent to :py:func:`@extend_schema <drf_spectacular.utils.extend_schema>`.

- ``manual_parameters`` is called ``parameters``

- ``openapi.Parameter`` is roughly equivalent to :py:class:`OpenApiParameter <drf_spectacular.utils.OpenApiParameter>`.

- ``@swagger_serializer_method`` is equivalent to :py:func:`@extend_schema_field <drf_spectacular.utils.extend_schema_field>`.

- ``ref_name`` on Serializer ``Meta`` classes is supported (excluding inlining with ``ref_name=None``)
