From `drf-yasg` to OpenAPI 3
============================

`drf-yasg`__ is an excellent library and the most popular choice for generating OpenAPI 2.0 (formerly known as Swagger
2.0) schemas with `Django REST Framework`__. Unfortunately, it currently does not provide support for OpenAPI 3.x.
Migration from ``drf-yasg`` to ``drf-spectacular`` requires some modifications, the complexity of which depends on what
features are being used.

__ https://pypi.org/project/drf-yasg
__ https://pypi.org/project/djangorestframework/

.. note:: In contrast to `drf-yasg`, we don't package Redoc & Swagger UI but serve them via hyperliked CDNs instead.
  If you want or need to serve those files yourself, you can do that with the optional
  `drf-spectacular-sidecar <https://github.com/tfranzel/drf-spectacular-sidecar>`_. See
  :ref:`installation instructions <self-contained-ui-installation>` for further details.


Decorators
----------

- :py:func:`@swagger_auto_schema <drf_yasg.utils.swagger_auto_schema>` is largely equivalent to
  :py:func:`@extend_schema <drf_spectacular.utils.extend_schema>`.

  - ``operation_description`` argument is called ``description``
  - ``operation_summary`` argument is called ``summary``
  - ``manual_parameters`` and ``query_serializer`` arguments are merged into a single ``parameters`` argument
  - ``security`` argument is called ``auth``
  - ``request_body`` arguments is called ``request``

    - Use ``None`` instead of :py:class:`drf_yasg.utils.no_body`

  - ``method`` argument doesn't exist, use ``methods`` instead (also supported by ``drf-yasg``)
  - ``auto_schema`` has no equivalent.
  - ``extra_overrides`` has no equivalent.
  - ``field_inspectors`` has no equivalent.
  - ``filter_inspectors`` has no equivalent.
  - ``paginator_inspectors`` has no equivalent.
  - Additional arguments are also available: ``exclude``, ``operation``, ``versions``, ``examples``.

- :py:func:`@swagger_serializer_method <drf_yasg.utils.swagger_serializer_method>` is equivalent to
  :py:func:`@extend_schema_field <drf_spectacular.utils.extend_schema_field>`.

  - ``component_name`` can be provided to break the field out as a separate component.

- :py:func:`@extend_schema_serializer <drf_spectacular.utils.extend_schema_serializer>` is available for overriding
  behavior of serializers.

- Instead of using :py:func:`@method_decorator <django.utils.decorators.method_decorator>`, use
  :py:func:`@extend_schema_view <drf_spectacular.utils.extend_schema_view>`.

Helper Classes
--------------

- :py:class:`~drf_yasg.openapi.Parameter` is roughly equivalent to :py:class:`~drf_spectacular.utils.OpenApiParameter`.

  - ``in_`` argument is called ``location``.
  - ``schema`` argument should be passed as ``type``.
  - ``format`` argument is merged into ``type`` argument by using
    :py:class:`OpenApiTypes <drf_spectacular.types.OpenApiTypes>`.

- :py:class:`~drf_yasg.openapi.Response` is largely identical to :py:class:`~drf_spectacular.utils.OpenApiResponse`.

  - ``schema`` argument is called ``response``
  - Order of arguments differs, so use keyword arguments.

- :py:class:`~drf_spectacular.utils.OpenApiExample` is available for providing ``examples`` to 
  :py:func:`@extend_schema <drf_spectacular.utils.extend_schema>`.

- :py:class:`~drf_yasg.openapi.Schema` is not required and can be eliminated. Use a plain :py:class:`dict` instead.

Types & Formats
---------------

In place of separate ``drf_yasg.openapi.TYPE_*`` and ``drf_yasg.openapi.FORMAT_*`` constants, ``drf-spectacular``
provides the :py:class:`~drf_spectacular.types.OpenApiTypes` enum:

- :py:data:`~drf_yasg.openapi.TYPE_BOOLEAN` is called :py:attr:`~drf_spectacular.types.OpenApiTypes.BOOL`, but you
  can use :py:class:`bool`.

- :py:data:`~drf_yasg.openapi.TYPE_FILE` should be replaced by :py:attr:`~drf_spectacular.types.OpenApiTypes.BINARY`

- :py:data:`~drf_yasg.openapi.TYPE_INTEGER` is called :py:attr:`~drf_spectacular.types.OpenApiTypes.INT`, but you can
  use :py:class:`int`.
- :py:data:`~drf_yasg.openapi.TYPE_INTEGER` with :py:data:`~drf_yasg.openapi.FORMAT_INT32` is called
  :py:attr:`~drf_spectacular.types.OpenApiTypes.INT32`
- :py:data:`~drf_yasg.openapi.TYPE_INTEGER` with :py:data:`~drf_yasg.openapi.FORMAT_INT64` is called
  :py:attr:`~drf_spectacular.types.OpenApiTypes.INT64`

- :py:data:`~drf_yasg.openapi.TYPE_NUMBER` is called :py:attr:`~drf_spectacular.types.OpenApiTypes.NUMBER`
- :py:data:`~drf_yasg.openapi.TYPE_NUMBER` with :py:data:`~drf_yasg.openapi.FORMAT_FLOAT` is called
  :py:attr:`~drf_spectacular.types.OpenApiTypes.FLOAT`, but you can use :py:class:`float`.
- :py:data:`~drf_yasg.openapi.TYPE_NUMBER` with :py:data:`~drf_yasg.openapi.FORMAT_DOUBLE` is called
  :py:attr:`~drf_spectacular.types.OpenApiTypes.DOUBLE` (or :py:attr:`~drf_spectacular.types.OpenApiTypes.DECIMAL`,
  but you can use :py:class:`~decimal.Decimal`)

- :py:data:`~drf_yasg.openapi.TYPE_OBJECT` is called :py:attr:`~drf_spectacular.types.OpenApiTypes.OBJECT`, but you can
  use :py:class:`dict`.

- :py:data:`~drf_yasg.openapi.TYPE_STRING` is called :py:attr:`~drf_spectacular.types.OpenApiTypes.STR`, but you can
  use :py:class:`str`.
- :py:data:`~drf_yasg.openapi.TYPE_STRING` with :py:data:`~drf_yasg.openapi.FORMAT_BASE64` is called
  :py:attr:`~drf_spectacular.types.OpenApiTypes.BYTE` (which is base64 encoded).
- :py:data:`~drf_yasg.openapi.TYPE_STRING` with :py:data:`~drf_yasg.openapi.FORMAT_BINARY` is called
  :py:attr:`~drf_spectacular.types.OpenApiTypes.BINARY`, but you can use :py:class:`bytes`.
- :py:data:`~drf_yasg.openapi.TYPE_STRING` with :py:data:`~drf_yasg.openapi.FORMAT_DATETIME` is called
  :py:attr:`~drf_spectacular.types.OpenApiTypes.DATETIME`, but you can use :py:class:`datetime.datetime`.
- :py:data:`~drf_yasg.openapi.TYPE_STRING` with :py:data:`~drf_yasg.openapi.FORMAT_DATE` is called
  :py:attr:`~drf_spectacular.types.OpenApiTypes.DATE`, but you can use :py:class:`datetime.date`.
- :py:data:`~drf_yasg.openapi.TYPE_STRING` with :py:data:`~drf_yasg.openapi.FORMAT_EMAIL` is called
  :py:attr:`~drf_spectacular.types.OpenApiTypes.EMAIL`
- :py:data:`~drf_yasg.openapi.TYPE_STRING` with :py:data:`~drf_yasg.openapi.FORMAT_IPV4` is called
  :py:attr:`~drf_spectacular.types.OpenApiTypes.IP4`, but you can use :py:class:`ipaddress.IPv4Address`.
- :py:data:`~drf_yasg.openapi.TYPE_STRING` with :py:data:`~drf_yasg.openapi.FORMAT_IPV6` is called
  :py:attr:`~drf_spectacular.types.OpenApiTypes.IP6`, but you can use :py:class:`ipaddress.IPv6Address`.
- :py:data:`~drf_yasg.openapi.TYPE_STRING` with :py:data:`~drf_yasg.openapi.FORMAT_PASSWORD` is called
  :py:attr:`~drf_spectacular.types.OpenApiTypes.PASSWORD`
- :py:data:`~drf_yasg.openapi.TYPE_STRING` with :py:data:`~drf_yasg.openapi.FORMAT_URI` is called
  :py:attr:`~drf_spectacular.types.OpenApiTypes.URI`
- :py:data:`~drf_yasg.openapi.TYPE_STRING` with :py:data:`~drf_yasg.openapi.FORMAT_UUID` is called
  :py:attr:`~drf_spectacular.types.OpenApiTypes.UUID`, but you can use :py:class:`uuid.UUID`.
- :py:data:`~drf_yasg.openapi.TYPE_STRING` with :py:data:`~drf_yasg.openapi.FORMAT_SLUG` has no direct equivalent. Use
  :py:attr:`~drf_spectacular.types.OpenApiTypes.STR` or :py:class:`str` instead.

- :py:data:`~drf_yasg.openapi.TYPE_ARRAY` has no direct equivalent.

- The following additional types are also available:

  - :py:attr:`~drf_spectacular.types.OpenApiTypes.ANY` for which you can use :py:class:`typing.Any`.
  - :py:attr:`~drf_spectacular.types.OpenApiTypes.DURATION` for which you can use :py:class:`datetime.timedelta`.
  - :py:attr:`~drf_spectacular.types.OpenApiTypes.HOSTNAME`
  - :py:attr:`~drf_spectacular.types.OpenApiTypes.IDN_EMAIL`
  - :py:attr:`~drf_spectacular.types.OpenApiTypes.IDN_HOSTNAME`
  - :py:attr:`~drf_spectacular.types.OpenApiTypes.IRI_REF`
  - :py:attr:`~drf_spectacular.types.OpenApiTypes.IRI`
  - :py:attr:`~drf_spectacular.types.OpenApiTypes.JSON_PTR_REL`
  - :py:attr:`~drf_spectacular.types.OpenApiTypes.JSON_PTR`
  - :py:attr:`~drf_spectacular.types.OpenApiTypes.NONE` for which you can use :py:data:`None`.
  - :py:attr:`~drf_spectacular.types.OpenApiTypes.REGEX`
  - :py:attr:`~drf_spectacular.types.OpenApiTypes.TIME` for which you can use :py:class:`datetime.time`.
  - :py:attr:`~drf_spectacular.types.OpenApiTypes.URI_REF`
  - :py:attr:`~drf_spectacular.types.OpenApiTypes.URI_TPL`

Parameter Location
------------------

``drf_yasg.openapi.IN_*`` constants are roughtly equivalent to constants defined on the
:py:class:`~drf_spectacular.utils.OpenApiParameter` class:

- :py:data:`~drf_yasg.openapi.IN_PATH` is called :py:attr:`~drf_spectacular.utils.OpenApiParameter.PATH`
- :py:data:`~drf_yasg.openapi.IN_QUERY` is called :py:attr:`~drf_spectacular.utils.OpenApiParameter.QUERY`
- :py:data:`~drf_yasg.openapi.IN_HEADER` is called :py:attr:`~drf_spectacular.utils.OpenApiParameter.HEADER`
- :py:data:`~drf_yasg.openapi.IN_BODY` and :py:data:`~drf_yasg.openapi.IN_FORM` have no direct equivalent.
  Instead you can use ``@extend_schema(request={"<media-type>": ...})`` or
  ``@extend_schema(request={("<status-code>", "<media-type"): ...})``.
- :py:attr:`~drf_spectacular.utils.OpenApiParameter.COOKIE` is also available.

Docstring Parsing
-----------------

``drf-yasg`` has some special handling for docstrings that is not supported by ``drf-spectacular``.

It attempts to split the first line from the rest of the docstring to use as the operation summary, and the remainder
is used as the operation description. ``drf-spectacular`` uses the entire docstring as the description. Use the
``summary`` and ``description`` arguments of :py:func:`@extend_schema <drf_spectacular.utils.extend_schema>` instead.
Optionally, the docstring can still be used to populate the operation description.

.. code-block:: python

    # Supported by drf-yasg:
    class UserViewSet(ViewSet):
        def list(self, request):
            """
            List all the users.

            Return a list of all usernames in the system.
            """
            ...

    # Updated for drf-spectacular using decorator for description:
    class UserViewSet(ViewSet):
        @extend_schema(
            summary="List all the users.",
            description="Return a list of all usernames in the system.",
        )
        def list(self, request):
            ...

    # Updated for drf-spectacular using docstring for description:
    class UserViewSet(ViewSet):
        @extend_schema(summary="List all the users.")
        def list(self, request):
            """Return a list of all usernames in the system."""
            ...

In addition, ``drf-yasg`` also supports `named sections`__, but these are not supported by ``drf-spectacular``. Again,
use the ``summary`` and ``description`` arguments of :py:func:`@extend_schema <drf_spectacular.utils.extend_schema>`
instead:

__ https://www.django-rest-framework.org/coreapi/schemas/#schemas-as-documentation

.. code-block:: python

    # Supported by drf-yasg:
    class UserViewSet(ViewSet):
        """
        list:
            List all the users.

            Return a list of all usernames in the system.

        retrieve:
            Retrieve user

            Get details of a specific user
        """
        ...

    # Updated for drf-spectacular using decorator for description:
    @extend_schema_view(
        list=extend_schema(
            summary="List all the users.",
            description="Return a list of all usernames in the system.",
        ),
        retrieve=extend_schema(
            summary="Retrieve user",
            description="Get details of a specific user",
        ),
    )
    class UserViewSet(ViewSet):
        ...

Authentication
--------------

In ``drf-yasg`` it was necessary to :doc:`manually describe authentication schemes <drf-yasg:security>`.

In ``drf-spectacular`` there is support for auto-generating the security definitions for a number of authentication
classes built in to DRF as well as other popular third-party packages.
:py:class:`~drf_spectacular.extensions.OpenApiAuthenticationExtension` is available to help tie in custom
authentication clasees -- see the :ref:`customization guide <customization_authentication_extension>`.

Compatibility
-------------

For compatibility, the following features of ``drf-yasg`` have been implemented:

- ``ref_name`` on ``Serializer`` ``Meta`` classes is supported (excluding inlining with ``ref_name=None``)

  - See :ref:`drf-yasg's documentation <drf-yasg:swagger_schema_fields>` for further details.
  - The equivalent in ``drf-spectacular`` is ``@extend_schema_serializer(component_name="...")``

- ``swagger_fake_view`` is available as attribute on views to signal schema generation
