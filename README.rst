===============
drf-spectacular
===============

|build-status-image| |pypi-version|

Sane and flexible `OpenAPI 3 <https://github.com/OAI/OpenAPI-Specification>`_ schema generation for `Django REST framework <https://www.django-rest-framework.org/>`_.

This project has 3 goals:
    1. Extract as much schema information from DRF as possible.
    2. Provide flexibility to make the schema usable in the real world (not only toy examples).
    3. Generate a schema that works well the most popular client generators.

The code is a heavily modified fork of the
`DRF OpenAPI generator <https://github.com/encode/django-rest-framework/blob/master/rest_framework/schemas/openapi.py/>`_,
which is/was lacking all of the below listed features.

Features
    - abstraction of serializers into components (better support for openapi-generator)
        - recursive components (e.g. nested PersonSerializer->PersonSerializer->...)
        - components are named after Serializers (i.e. the main interface of your API)
    - ``@extend_schema`` decorator for customization of APIView, Viewsets, function-based views, and ``@action``
        - additional manual query parameters
        - request/response serializer override
        - response status code override
        - polymorphic responses (manual by providing serializer list or rest_polymorphic)
        - and more customization options
    - easy to use hooks for extending the spectacular ``AutoSchema``
    - authentication methods in schema (default DRF methods included, easily extendable)
    - ``MethodSerializerField()`` type via type hinting
    - schema tags for operations plus override option (very useful in Swagger UI)
    - support for `django-polymorphic <https://github.com/django-polymorphic/django-polymorphic>`_ / `rest_polymorphic <https://github.com/apirobot/django-rest-polymorphic>`_ (automatic polymorphic responses for PolymorphicSerializers)
    - description extraction from doc strings
    - sane fallbacks where there are no serializers available (free-form objects)
    - operation_id naming based on endpoint path instead of model name (preventing operation_id duplication)


Incomplete features (in progress):
    - optional separate component versions for PATCH serializers (no required fields)
    - optional input/output serializer component split


Requirements
------------

-  Python >= 3.6
-  Django (2.2, 3.0)
-  Django REST Framework (3.10, 3.11)

Installation
------------

Install using ``pip``\ …

.. code:: bash

    $ pip install drf-spectacular

then add drf-spectacular to installed apps in ``settings.py``

.. code:: python

    INSTALLED_APPS = [
        # ALL YOUR APPS
        'drf_spectacular',
    ]


and finally register our spectacular AutoSchema with DRF

.. code:: python

    REST_FRAMEWORK = {
        # YOUR SETTINGS
        'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
        # OR this for usage with rest_polymorphic/django-polymorphic
        # 'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.contrib.rest_polymorphic.PolymorphicAutoSchema',
    }

Take it for a spin
------------------

`drf-spectacular` is KISS. It only generates a valid OpenAPI 3 specification for you and nothing else.
You can easily view your schema with the excellent Swagger UI or any other compliant UI or tool:

.. code:: bash

    $ ./manage.py spectacular --file schema.yml
    $ docker run -p 80:8080 -e SWAGGER_JSON=/schema.yml -v ${PWD}/schema.yml:/schema.yml swaggerapi/swagger-ui


Usage
-----

`drf-spectacular` works pretty well out of the box. The toy examples do not cover your cases?
No problem, you can heavily customize how your schema will be rendered.

Customization by using @extend_schema
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Most customization cases should be covered by the ``extend_schema`` decorator. We usually get
pretty far with specifying ``QueryParameter`` and splitting request/response serializers, but
the sky is the limit.

.. code:: python

    from drf_spectacular.utils import extend_schema, QueryParameter

    class AlbumViewset(viewset.ModelViewset)
        serializer_class = AlbumSerializer

        @extend_schema(
            request=AlbumCreationSerializer
            responses={201: AlbumSerializer},
        )
        def create(self, request):
            # your non-standard behaviour
            return super().create(request)

        @extend_schema(
            # extra parameters added to the schema
            extra_parameters=[
                QueryParameter(name='artist', description='Filter by artist', required=False, type=str),
                QueryParameter(name='year', description='Filter by year', required=False, type=int),
            ],
            # override default docstring extraction
            description='More descriptive text',
            # provide Authentication class that deviates from the views default
            auth=None,
            # change the auto-generated operation name
            operation_id=None,
            # or even completely override what AutoSchema would generate. Provide raw Open API spec as Dict.
            operation=None,
        )
        def list(self, request):
            # your non-standard behaviour
            return super().list(request)

        @extend_schema(
            request=AlbumLikeSerializer
            responses={204: None},
        )
        @action(detail=True, methods=['post'])
        def set_password(self, request, pk=None):
            # your action behaviour



Customization by overriding ``AutoSchema``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Still not satisifed? You want more! We still got you covered. We prepared some convenient hooks for things that
are probably up to taste. If you are careful, you can change pretty much anything.

Don't forget to register your custom AutoSchema in the ``DEFAULT_SCHEMA_CLASS``.

.. code:: python

    from drf_spectacular.openapi import AutoSchema

    class CustomAutoSchema(AutoSchema):
        def get_tags(self, path, method):
            return ['AllUnderOneTag']


Extras
^^^^^^

got endpoints that yield list of differing objects? Enter ``PolymorphicResponse``

.. code:: python

    @extend_schema(
        responses=PolymorphicResponse(
            serializers=[SerializerA, SerializerB],
            resource_type_field_name='type',
        )
    )
    @api_view()
    def poly_list(request):
        return Response(list_of_multiple_object_types)


Testing
-------

Install testing requirements.

.. code:: bash

    $ pip install -r requirements.txt

Run with runtests.

.. code:: bash

    $ ./runtests.py

You can also use the excellent `tox`_ testing tool to run the tests
against all supported versions of Python and Django. Install tox
globally, and then simply run:

.. code:: bash

    $ tox

.. _tox: http://tox.readthedocs.org/en/latest/

.. |build-status-image| image:: https://secure.travis-ci.org/tfranzel/drf-spectacular.svg?branch=master
   :target: https://travis-ci.org/tfranzel/drf-spectacular?branch=master
.. |pypi-version| image:: https://img.shields.io/pypi/v/drf-spectacular.svg
   :target: https://pypi.python.org/pypi/drf-spectacular
