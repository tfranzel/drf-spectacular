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
            parameters=[
              QuerySerializer,  # serializer fields are converted to parameters
              OpenApiParameter("nested", QuerySerializer),  # serializer object is converted to a parameter
              OpenApiParameter("queryparam1", OpenApiTypes.UUID, OpenApiParameter.QUERY),
              OpenApiParameter("pk", OpenApiTypes.UUID, OpenApiParameter.PATH), # path variable was overridden
            ],
            request=YourRequestSerializer,
            responses=YourResponseSerializer,
            # more customizations
        )
        def retrieve(self, request, pk, *args, **kwargs)
            # your code

.. note:: ``responses`` can be detailed further by providing a dictionary instead. This could be for example
  ``{201: YourRequestSerializer, ...}`` or ``{(200, 'application/pdf'): OpenApiTypes.BINARY, ...}``.

.. note:: For simple responses, you might not go through the hassle of writing an explicit serializer class.
  In those cases, you can simply specify the request/response with a call to
  :py:func:`inline_serializer <drf_spectacular.utils.inline_serializer>`.
  This lets you conveniently define the endpoint's schema inline without actually writing a serializer class.

.. note:: If you want to annotate methods that are provided by the base classes of a view, you have nothing to
  attach :py:func:`@extend_schema <drf_spectacular.utils.extend_schema>` to. In those instances you can use
  :py:func:`@extend_schema_view <drf_spectacular.utils.extend_schema_view>` to conveniently annotate the
  default implementations.

  .. code-block:: python

        class XViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
            @extend_schema(description='text')
            def list(self, request, *args, **kwargs):
                return super().list(request, *args, **kwargs)

  is equivalent to

  .. code-block:: python

        @extend_schema_view(
            list=extend_schema(description='text')
        )
        class XViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
            ...

.. note:: You may also use :py:func:`@extend_schema <drf_spectacular.utils.extend_schema>` on views
  to attach annotations to all methods in that view (e.g. tags). Method annotations will take precedence
  over view annotation.

Step 3: :py:class:`@extend_schema_field <drf_spectacular.utils.extend_schema_field>` and type hints
---------------------------------------------------------------------------------------------------
A custom ``SerializerField`` might not get picked up properly. You can inform `drf-spectacular`
on what is to be expected with the :py:func:`@extend_schema_field <drf_spectacular.utils.extend_schema_field>`
decorator. It takes either basic types or a ``Serializer`` as argument. In case of basic types
(e.g. ``str``, ``int``, etc.) a type hint is already sufficient.

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


Step 4: :py:class:`@extend_schema_serializer <drf_spectacular.utils.extend_schema_serializer>`
-----------------------------------------------------------------------------------------------

You may also decorate your serializer with :py:func:`@extend_schema_serializer <drf_spectacular.utils.extend_schema_serializer>`.
Mainly used for excluding specific fields from the schema or attaching request/response examples.
On rare occasions (e.g. envelope serializers), overriding list detection with ``many=False`` may come in handy.

.. code:: python

    @extend_schema_serializer(
        exclude_fields=('single',), # schema ignore these fields
        examples = [
             OpenApiExample(
                'Valid example 1',
                summary='short summary',
                description='longer description',
                value={
                    'songs': {'top10': True},
                    'single': {'top10': True}
                },
                request_only=True, # signal that example only applies to requests
                response_only=False, # signal that example only applies to responses
            ),
        ]
    )
    class AlbumSerializer(serializers.ModelSerializer):
        songs = SongSerializer(many=True)
        single = SongSerializer(read_only=True)

        class Meta:
            fields = '__all__'
            model = Album


Step 5: Extensions
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

.. _customization_authentication_extension:

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

Declare custom/library filters with :py:class:`OpenApiFilterExtension <drf_spectacular.extensions.OpenApiFilterExtension>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This extension only applies to filter and pagination classes and is rarely used. Built-in support for
`django-filters` is realized with this extension. :py:class:`OpenApiFilterExtension <drf_spectacular.extensions.OpenApiFilterExtension>`
replaces the filter's native ``get_schema_operation_parameters`` with your customized version, where you
have full access to `drf-spectacular's` more advanced introspection features.


Step 6: Postprocessing hooks
----------------------------

The generated schema is still not to your liking? You are no easy customer, but there is one
more thing you can do. Postprocessing hooks run at the very end of schema generation. This is how
the choice ``Enum`` are consolidated into component objects. You can register additional hooks with the
``POSTPROCESSING_HOOKS`` setting.

.. code-block:: python

    def custom_postprocessing_hook(result, generator, request, public):
        # your modifications to the schema in parameter result
        return result


Step 7: Preprocessing hooks
---------------------------
.. _customization_preprocessing_hooks:

Preprocessing hooks are applied shortly after collecting all API operations and before the
actual schema generation starts. They provide an easy mechanism to alter which operations
should be represented in your schema. You can exclude specific operations, prefix paths,
introduce or hardcode path parameters or modify view initiation.
additional hooks with the ``PREPROCESSING_HOOKS`` setting.

.. code-block:: python

    def custom_preprocessing_hook(endpoints):
        # your modifications to the list of operations that are exposed in the schema
        for (path, path_regex, method, callback) in endpoints:
            pass
        return endpoints


.. note:: A common use case would be the removal of duplicated ``{format}``-suffixed operations,
  for which we already provide the
  :py:func:`drf_spectacular.hooks.preprocess_exclude_path_format <drf_spectacular.hooks.preprocess_exclude_path_format>`
  hook. You can simply enable this hook by adding the import path string to the ``PREPROCESSING_HOOKS``.

Congratulations
---------------

You should now have no more warnings and a spectacular schema that satisfies all your requirements.
If that is not the case, feel free to open an `issue <https://github.com/tfranzel/drf-spectacular/issues>`_
and make a suggestion for improvement.
