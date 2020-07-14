.. _customization:

Workflow & schema customization
===============================

You are not satisfied with your generated schema? Follow these steps in order to get your
schema closer to your API.

.. note:: The warnings emitted by ``./manage.py spectacular --file schema.yaml --validate``
  are intended as an indicator to where `drf-spectacular` discovered issues.
  Sane fallbacks are used wherever possible and some warnings might not even be relevant to you.
  The remaining issues can be solved with the following steps.


Step 1: ``queryset`` and ``serializer_class``
---------------------------------------------
Introspection heavily relies on those two attributes. ``get_serializer_class()``
and ``get_serializer()`` are also used if available. You can also set those
on ``APIView``. Even though this is not supported by DRF, `drf-spectacular` will pick
them up and use them.


Step 2: :py:class:`@extend_schema <drf_spectacular.utils.extend_schema>`
------------------------------------------------------------------------
Decorate your view functions with the :py:func:`@extend_schema <drf_spectacular.utils.extend_schema>` decorator.
There is a multitude of override options, but you only need to override what was not properly
discovered in the introspection.

.. code-block:: python

    class PersonView(viewsets.GenericViewSet):
        @extend_schema(
            request=YourRequestSerializer,
            responses=YourResponseSerializer,
            # more customizations
        )
        def retrieve(self, request, *args, **kwargs)
            # your code

Step 3: :py:class:`@extend_schema_field <drf_spectacular.utils.extend_schema_field>` and type hints
---------------------------------------------------------------------------------------------------
A custom ``SerializerField`` might not get picked up properly. You can inform `drf-spectacular`
on what is to be expected with the :py:func:`@extend_schema_field <drf_spectacular.utils.extend_schema_field>`
decorator. It takes either basic types or a ``Serializer`` as argument. In case of basic types
(e.g. str int etc.) a type hint is already sufficient.

.. code-block:: python

    @extend_schema_field(OpenApiTypes.BYTE)  # also takes basic python types
    class CustomField(serializers.Field):
        def to_representation(self, value):
            return urlsafe_base64_encode(b'\xf0\xf1\xf2')


You can apply it also to the method of a `SerializerMethodField`.

.. code-block:: python

    class ErrorDetailSerializer(serializers.Serializer):
        field_custom = serializers.SerializerMethodField()

        @extend_schema_field(OpenApiTypes.DATETIME)
        def get_field_custom(self, object):
            return '2020-03-06 20:54:00.104248'

Step 4: Extensions
------------------
The core purpose of extensions is to make the above customization mechanisms also available for library code.
Usually, you cannot easily decorate or modify ``View``, ``Serializer`` or ``Field`` from libraries.
Extensions provide a way to hook into the introspection without actually touching the library.

All extensions work on the same principle. You provide a ``target_class`` (import path
string or actual class) and then state what `drf-spectcular` should use instead of what
it would normally discover.

.. note:: Only the first Extension matching the criteria is used. By setting the ``priority`` attribute
  on your extension, you can influence the matching order (default ``0``).
  Built-in Extensions have a priority of ``-1``. If you subclass built-in Extensions, don't forget to
  increase the priority.


Replace views with :py:class:`OpenApiViewExtension <drf_spectacular.extensions.OpenApiViewExtension>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Many libraries use ``@api_view`` or ``APIView`` instead of `ViewSet` or `GenericAPIView`.
In those cases, introspection has very little to work with. The purpose of this extension
is to augment or switch out the encountered view (only for schema generation). Simply extending
the discovered class ``class Fixed(self.target_class)`` with a ``queryset`` or
``serializer_class`` attribute will often solve most issues.

.. code-block:: python

    class Fix4(OpenApiViewExtension):
        target_class = 'oscarapi.views.checkout.UserAddressDetail'

        def view_replacement(self):
            from oscar.apps.address.models import UserAddress

            class Fixed(self.target_class):
                queryset = UserAddress.objects.none()
            return Fixed

Specify authentication with :py:class:`OpenApiAuthenticationExtension <drf_spectacular.extensions.OpenApiAuthenticationExtension>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Authentication classes that do not have 3rd party support will emit warnings and be ignored.
Luckily authentication extensions are very easy to implement. Have a look at the
`default authentication method extensions <https://github.com/tfranzel/drf-spectacular/blob/master/drf_spectacular/authentication.py>`_.
A simple custom HTTP header based authentication could be achieved like this:

.. code-block:: python

    class MyAuthenticationScheme(OpenApiAuthenticationExtension):
        target_class = 'my_app.MyAuthentication'  # full import path OR class ref
        name = 'MyAuthentication'  # name used in the schema

        def get_security_definition(self, auto_schema):
            return {
                'type': 'apiKey',
                'in': 'header',
                'name': 'api_key',
            }


Declare field output with :py:class:`OpenApiSerializerFieldExtension <drf_spectacular.extensions.OpenApiSerializerFieldExtension>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This is mainly targeted to custom `SerializerField`'s that are within library code. This extension
is functionally equivalent to :py:func:`@extend_schema_field <drf_spectacular.utils.extend_schema_field>`

.. code-block:: python

    class CategoryFieldFix(OpenApiSerializerFieldExtension):
        target_class = 'oscarapi.serializers.fields.CategoryField'

        def map_serializer_field(self, auto_schema, direction):
            # equivalent to return {'type': 'string'}
            return build_basic_type(OpenApiTypes.STR)


Declare serializer magic with :py:class:`OpenApiSerializerExtension <drf_spectacular.extensions.OpenApiSerializerExtension>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This is one of the more involved extension mechanisms. `drf-spectacular` uses those to implement
`polymorphic serializers <https://github.com/tfranzel/drf-spectacular/blob/master/drf_spectacular/serializers.py>`_.
The usage of this extension is rarely necessary because most custom ``Serializer`` classes stay very
close to the default behaviour.


Step 5: Postprocessing hooks
----------------------------

The generated schema is still not to your liking? You are no easy customer, but there is one
more thing you can do. Postprocessing hooks run at the very end of schema generation. This is how
the choice ``Enum`` are consolidated into component objects. You can register additional hooks with the
``POSTPROCESSING_HOOKS`` setting.

.. code-block:: python

    def custom_hook(result, generator, request, public):
        # your modifications to the schema in parameter result
        return result


Step 6: Preprocessing
---------------------

While most schema problems should be addressed using postprocessing hooks, there
are also two preprocessing settings ``ENDPOINT_ENUMERATOR_CLASS`` and ``DEFAULT_GENERATOR_CLASS``
that can be changed to custom classes that alter the endpoints to be processed, and the
broad generation process.

The enumeration class can be used to exclude certain endpoints, preventing them from
going through the inspection of the generation processes.

The following prevents any occurrence of `{format}` at the end of endpoint paths.

.. code-block:: python

    class NoFormatEndpointEnumerator(EndpointEnumerator):

        def should_include_endpoint(self, path, callback):
            """
            Return `True` if the given endpoint should be included.
            """
            if not super().should_include_endpoint(path, callback):
                return False

            # DRF only excludes .json style URLs.
            # This also excludes other uses of `{format}` at the end of the path
            if path.endswith('{format}') or path.endswith('{format}/'):
                return False

            return True


The generator class is responsible for the entire process of generating the
OpenAPI document.  It provides the implementation for instantiating views and view inspectors
for each enumerated endpoint, obtaining the schemas from each view inspector, and
combining everything into the final OpenAPI document.

This includes checking of the view permissions and API versioning of the endpoints.

As such, extending the schema generator class provides many opportunities for radically
altering the way the API is constructed.

For example, if using ``@extend_schema`` and extensions are impractical because there are many views
using the same pattern that the schema inspector does not support, or seems impossible because the
views are dynamically generated or varies based on the request, a custom view inspector can be created
for those views.

.. code-block:: python

    class ProjectSpecificSchemaGenerator(SchemaGenerator):

        def create_view(self, callback, method, request=None):
            if hasattr(view, 'get_response_serializer'):
                from drf_spectacular.openapi import AutoSchema
                import mock

                request = mock.Mock()
                request.method = method
                ...

                view = super().create_view(callback, method, request)

                response_serializer = view.get_response_serializer()

                class CustomResponseSchema(AutoSchema):
                    def get_response_serializers(self):
                        return response_serializer

                view.schema = CustomResponseSchema()
                return view

            return super().create_view(callback, method, request)


If the view instantiation and resulting schema does not depend on the request,
the above example could be more simply achieved by extending
:py:class:`AutoSchema <drf_spectacular.openapi.AutoSchema>`,
and declaring that in ``REST_FRAMEWORK['DEFAULT_SCHEMA_CLASS']``.

.. code-block:: python

    class ProjectSpecificAutoSchema(AutoSchema):
        def get_response_serializers(self):
            if hasattr(self.view, 'get_response_serializer'):
                return self.view.response_serializer
            else:
                return super().get_response_serializers()


Congratulations
---------------

You should now have no more warnings and a spectacular schema that satisfies all your requirements.
If that is not the case, feel free to open an `issue <https://github.com/tfranzel/drf-spectacular/issues>`_
and make a suggestion for improvement.
