FAQ
===

I use library/app `XXX` and the generated schema is wrong or broken
-------------------------------------------------------------------
Sometimes DRF libraries do not cooperate well with the introspection mechanics.
Check the :ref:`blueprints` for already available fixes. If there aren't any,
learn how to do easy :ref:`customization`. Feel free to contribute back missing fixes.

If you think this is a bug in `drf-spectacular`, open a
`issue <https://github.com/tfranzel/drf-spectacular/issues>`_.


I cannot use :py:func:`@extend_schema <drf_spectacular.utils.extend_schema>` on library code
--------------------------------------------------------------------------------------------
You can easily adapt introspection for libraries/apps with the ``Extension`` mechanism.
``Extensions`` provide an easy way to attach schema information to code that you cannot
modify otherwise. Have a look at :ref:`customization` on how to use ``Extensions``


I get an empty schema or endpoints are missing
----------------------------------------------
This is usually due versioning (or more rarely due to permisssions).

In case you use versioning on all endpoints, that might be the intended output.
By default the schema will only contain unversioned endpoints. Explicitly specify
what version you want to generate.

.. code-block:: bash

    ./manage.py spectacular --api-version 'YOUR_VERSION'

This will contain unversioned endpoints together with the endpoints for the the specified version.

For the schema views you can either set a versioning class (implicit versioning via the request) or
explicitly override the version with ``SpectacularAPIView.as_view(api_version='YOUR_VERSION')``.


I expected a different schema
-----------------------------
Sometimes views declare one thing (via ``serializer_class`` and ``queryset``) and do
a entirely different thing. Usually this is attributed to making a library code flexible
under varying situations. In those cases it is best to override what the introspection
decuded and state explicitly what is to be expected.
Work through the steps in :ref:`customization` to adapt your schema.


I get duplicated operations with a ``{format}``-suffix
------------------------------------------------------
Your app likely uses DRF's ``format_suffix_patterns``. If those operations are
undesireable in your schema, you can simply exclude them with an already provided
:ref:`preprocessing hook <customization_preprocessing_hooks>`.


I get a lot of warnings
-----------------------
The warnings are emitted to inform you of discovered schema issues. Some
usage patterns like ``@api_view`` or ``APIView`` provide very
little discoverable information on your API. In those cases you can
easily augment those endpoints and serializers with additional information.
Look at :ref:`customization` options to fill those gaps and make the warnings
disappear.


I get warnings regarding my ``Enum`` or  my ``Enum`` names have a weird suffix
-------------------------------------------------------------------------------
This is because the ``Enum`` postprocessing hook is activated by default, which
attempts to find a name for a set of enum choices.

The naming mechanism uses the name of the field and possibly the name of the
component, followed by a suffix if necessary if there are clashes (if there are
two enum fields with the same name but different set of choices). This will
handle all encountered issues automatically, but also notify you of potential
problems, of two kinds:

* multiple names being produced for the same set of values, due to different
  field names (e.g. if you have a single currency enum used by distinct fields
  named like ``payment_currency`` and ``preferred_currency``, the naming
  mechanism will by default treat this as two different enums but emit a
  warning).
* clashes that result in a suffix being needed, as above.

You can resolve (or silence) enum issues by adding an entry to the
``ENUM_NAME_OVERRIDES`` setting. Values can take the form of choices (list of tuples), value lists
(list of strings), or import strings. Django's ``models.Choices`` and Python's ``Enum`` classes
are supported as well. The key is a string that you choose as a name to give to
this set of values.

For example:

.. code-block:: python

    SPECTACULAR_SETTINGS = {
        ...
        'ENUM_NAME_OVERRIDES': {
            # variable containing list of tuples, e.g. [('US', 'US'), ('RU', 'RU'),]
            'LanguageEnum': language_choices,
            # dedicated Enum or models.Choices class
            'CountryEnum': 'import_path.enums.CountryEnum',
            # choices is an attribute of class CurrencyContainer containing a list of tuples
            'CurrencyEnum': 'import_path.CurrencyContainer.choices',
        }
    }

If you have multiple semantically distinct enums that happen to have the same
set of values, and you want different names for them, this mechanism won't work.


My endpoints use different serializers depending on the situation
-----------------------------------------------------------------

Welcome to the real world! Use :py:func:`@extend_schema <drf_spectacular.utils.extend_schema>`
in combination with :py:class:`PolymorphicProxySerializer <drf_spectacular.utils.PolymorphicProxySerializer>`
like so:

.. code-block:: python

    class PersonView(viewsets.GenericViewSet):
        @extend_schema(responses={
            200: PolymorphicProxySerializer(
                    component_name='Person',
                    # on 200 either a legal or a natural person is returned
                    serializers=[LegalPersonSerializer, NaturalPersonSerializer],
                    resource_type_field_name='type',
            ),
            500: YourOptionalErrorSerializer,
        })
        def retrieve(self, request, *args, **kwargs)
            pass


My authentication method is not supported
-----------------------------------------
You can easily specify a custom authentication with
:py:class:`OpenApiAuthenticationExtension <drf_spectacular.extensions.OpenApiAuthenticationExtension>`.
Have a look at :ref:`customization` on how to use ``Extensions``


How can I i18n/internationalize my schema and UI?
----------------------------------------------------

You can use the Django internationalization as you would normally do. The workflow is as one
would expect: ``USE_I18N=True``, settings the languages, ``makemessages``, and ``compilemessages``.

The CLI tool accepts a language parameter (``./manage.py spectacular --lang="de-de"``) for offline
generation. The schema view as well as the UI views accept a ``lang`` query parameter for
explicitly requesting a language (``example.com/api/schema?lang=de``). If i18n is enabled and there
is no query parameter provided, the ``ACCEPT_LANGUAGE`` header is used. Otherwise the translation
falls back to the default language.

.. code-block:: python

    from django.utils.translation import gettext_lazy as _

    class PersonView(viewsets.GenericViewSet):
        __doc__ = _("""
        More lengthy explanation of the view
        """)

        @extend_schema(summary=_('Main endpoint for creating person'))
        def retrieve(self, request, *args, **kwargs)
            pass


FileField (ImageField) is not handled properly in the schema
------------------------------------------------------------
In contrast to most other fields, ``FileField`` behaves differently for requests and responses.
This duality is impossible to represent in a single component schema.

For these cases, there is an option to split components into request and response parts
by setting ``COMPONENT_SPLIT_REQUEST = True``. Note that this influences the whole schema,
not just components with ``FileFields``.

Also consider explicitly setting ``parser_classes = [parsers.MultiPartParser]`` (or any file compatible parser)
on your `View` or write a custom `get_parser_classes`. These fields do not work with the default ``JsonParser``
and that fact should be represented in the schema.


I'm using ``@action(detail=False)`` but the response schema is not a list
-------------------------------------------------------------------------

``detail=True/False`` only specifies whether the action should be routed at ``x/{id}/action`` or ``x/action``.
The ``detail`` parameter in itself makes no statement about the action's response. Also note that the default
for underspecified endpoints is a non-list response. To signal a listed response, you can use
``@extend_schema(responses=XSerializer(many=True))``.


Using ``@extend_schema`` on ``APIView`` has no effect
-----------------------------------------------------

``@extend_schema`` needs to be applied to the entrypoint method of the view. For views derived from ``Viewset``,
these are methods like ``retrieve``, ``list``, ``create``. For ``APIView`` based views, these are ``get``, ``post``,
``create``. This confusion commonly occurs while using convenience classes like ``ListAPIView``. ``ListAPIView`` does
in fact have a ``list`` method (via mixin), but the actual entrypoint is still the ``get`` method, and the ``list``
call is proxied through the entrypoint.


Where should I put my extensions? / my extensions are not detected
------------------------------------------------------------------

The extensions register themselves automatically. Just be sure that the python interpreter sees them at least once.
To that end, we suggest creating a ``PROJECT/schema.py`` file and importing it in your ``PROJECT/__init__.py``
(same directory as ``settings.py`` and ``urls.py``) with ``import PROJECT.schema``. Please do not import the file in
``settings.py`` as this may potentially lead to cyclic import issues.


My ``@action`` is erroneously paginated or has filter parameters that I do not want
-----------------------------------------------------------------------------------

This usually happens when ``@extend_schema(responses=XSerializer(many=True))`` is used. Actions inherit filter
and pagination classes from their ``ViewSet``. If the response is then marked as a list, the ``pagination_class``
kicks in. Since actions are handled manually by the user, this behavior is usually not immediately obvious.
To make make your intentions clear to `drf-spectacular`, you need to clear the offening classes in the action
decorator, e.g. setting ``pagination_class=None``.

Users of ``django-filter`` might also see unwanted query parameters. Since the same mechanics apply here too,
you can remove those parameters by resetting the filter backends with ``@action(...,filter_backends=[])``.

.. code-block:: python

    class XViewset(viewsets.ModelViewSet):
        queryset = SimpleModel.objects.all()
        pagination_class = pagination.LimitOffsetPagination

        @extend_schema(responses=SimpleSerializer(many=True))
        @action(methods=['GET'], detail=False, pagination_class=None)
        def custom_action(self):
            pass


How to I wrap my responses? / My endpoints are wrapped in a generic envelope
----------------------------------------------------------------------------

This non-native behavior can be conventiently modeled with a simple helper function. You simply need
to wrap the actual serializer with your envelope serializer and provide it to ``@extend_schema``.

Here is an example on how to build an ``enveloper`` helper function. In this example, the actual
serializer is put into the ``data`` field, while ``status`` is some arbitrary envelope field.
Adapt to your specific requirements.

.. code-block:: python

    def enveloper(serializer_class, many):
        component_name = 'Enveloped{}{}'.format(
            serializer_class.__name__.replace("Serializer", ""),
            "List" if many else "",
        )

        @extend_schema_serializer(many=False, component_name=component_name)
        class EnvelopeSerializer(serializers.Serializer):
            status = serializers.BooleanField()  # some arbitrary envelope field
            data = serializer_class(many=many)  # the enveloping part

        return EnvelopeSerializer


    class XViewset(GenericViewSet):
        @extend_schema(responses=enveloper(XSerializer, True))
        def list(self, request, *args, **kwargs):
            ...
