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
This is usually due to endpoint permissions or versioning.

In case you use versioning on all endpoints, that might be the intended output.
By default the schema will only contain unversioned endpoints. Explicitly specify
what version you want to generate.

.. code-block:: bash

    ./manage.py spectacular --api-version 'YOUR_VERSION'

This will contain unversioned endpoints together with the endpoints for the the specified version.

If that does not help, open an `issue <https://github.com/tfranzel/drf-spectacular/issues>`_.


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
This is because the ``Enum`` postprocessing hook is activated by default. Enum suffixes like
``LanguageCa22Enum`` mean that there was a naming collision that got resolved. Other
warnings might indicate that you use one and the same choice set under different names.

The naming mechanism will handle all encountered issues automatically, but also notify you of
potential problems. You can resolve (or silence) enum issues by adding an entry to the
``ENUM_NAME_OVERRIDES`` setting. Values can take the form of choices (list of tuples), value lists
(list of strings), or import strings. Django's ``models.Choices`` and Python's ``Enum`` classes
are supported as well.

.. code-block:: python

    'ENUM_NAME_OVERRIDES': {
        # variable containing list of tuples, e.g. [('US', 'US'), ('RU', 'RU'),]
        'LanguageEnum': language_choices,
        # dedicated Enum or models.Choices class
        'CountryEnum': 'import_path.enums.CountryEnum',
        # choices is an attribute of class CurrencyContainer containing a list of tuples
        'CurrencyEnum': 'import_path.CurrencyContainer.choices',
    }


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
