FAQ
===

I use library/app *XXX* and the generated schema is wrong or broken
-------------------------------------------------------------------

Sometimes DRF libraries do not cooperate well with the introspection mechanics.
Check the :ref:`blueprints` for already available fixes. If there aren't any,
learn how to do easy :ref:`customization`. Feel free to contribute back missing fixes.

If you think this is a bug in *drf-spectacular*, open an
`issue <https://github.com/tfranzel/drf-spectacular/issues>`_.

My Swagger UI and/or Redoc page is blank
----------------------------------------

Chances are high that you are using `django-csp <https://django-csp.readthedocs.io/en/latest/index.html>`_.
Take a look inside your browser console and confirm that you have ``Content Security Policy`` errors.
By default, ``django-csp`` usually breaks our UIs for 2 reasons: external assets and inline scripts.

Using the `sidecar <https://github.com/tfranzel/drf-spectacular#self-contained-ui-installation>`_
will mitigate the remote asset loading violation by serving the asset from your ``self``. Alternatively,
you can also adapt ``CSP_DEFAULT_SRC`` to allow for those CDN assets instead.

Solution for Swagger UI:
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    # Option: SIDECAR
    SPECTACULAR_SETTINGS = {
         ...
        'SWAGGER_UI_DIST': 'SIDECAR',
        'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    }
    CSP_DEFAULT_SRC = ("'self'", "'unsafe-inline'")
    CSP_IMG_SRC = ("'self'", "data:")

    # Option: CDN
    CSP_DEFAULT_SRC = ("'self'", "'unsafe-inline'", "cdn.jsdelivr.net")
    CSP_IMG_SRC = ("'self'", "data:", "cdn.jsdelivr.net")

.. note:: Depending on how paranoid you are, you may avoid having to use ``unsafe-inline`` by using
  ``SpectacularSwaggerSplitView`` instead, which does a separate request for the script. Note however
  that some URL rewriting deployments will break it. Use this option only if you really need to.

Solution for Redoc:
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    # Option: SIDECAR
    SPECTACULAR_SETTINGS = {
         ...
        'REDOC_DIST': 'SIDECAR',
    }
    # Option: CDN
    CSP_DEFAULT_SRC = ("'self'", "cdn.jsdelivr.net")

    # required for both CDN and SIDECAR
    CSP_WORKER_SRC = ("'self'", "blob:")
    CSP_IMG_SRC = ("'self'", "data:", "cdn.redoc.ly")
    CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "fonts.googleapis.com")
    CSP_FONT_SRC = ("'self'", "fonts.gstatic.com")

I cannot use :py:func:`@extend_schema <drf_spectacular.utils.extend_schema>` on library code
--------------------------------------------------------------------------------------------

You can easily adapt introspection for libraries/apps with the *Extension* mechanism.
*Extensions* provide an easy way to attach schema information to code that you cannot
modify otherwise. Have a look at :ref:`customization` on how to use *Extensions*

I get an empty schema or endpoints are missing
----------------------------------------------

This is usually due to versioning (or more rarely due to permissions).

In case you use versioning on all endpoints, that might be the intended output.
By default the schema will only contain unversioned endpoints. Explicitly specify
what version you want to generate.

.. code-block:: bash

    ./manage.py spectacular --api-version 'YOUR_VERSION'

This will contain unversioned endpoints together with the endpoints for the specified version.

For the schema views you can either set a versioning class (implicit versioning via the request) or
explicitly override the version with ``SpectacularAPIView.as_view(api_version='YOUR_VERSION')``.

I expected a different schema
-----------------------------

Sometimes views declare one thing (via ``serializer_class`` and ``queryset``) and do
a entirely different thing. Usually this is attributed to making a library code flexible
under varying situations. In those cases it is best to override what the introspection
decided and state explicitly what is to be expected.
Work through the steps in :ref:`customization` to adapt your schema.

I get duplicated operations with a ``{format}``-suffix
------------------------------------------------------

Your app likely uses DRF's ``format_suffix_patterns``. If those operations are
undesirable in your schema, you can simply exclude them with an already provided
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
------------------------------------------------------------------------------

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
Have a look at :ref:`customization` on how to use *Extensions*

How can I i18n/internationalize my schema and UI?
-------------------------------------------------

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
        def retrieve(self, request, *args, **kwargs):
            pass

FileField (ImageField) is not handled properly in the schema
------------------------------------------------------------

In contrast to most other fields, ``FileField`` behaves differently for requests and responses.
This duality is impossible to represent in a single component schema.

For these cases, there is an option to split components into request and response parts
by setting ``COMPONENT_SPLIT_REQUEST = True``. Note that this influences the whole schema,
not just components with ``FileFields``.

Also consider explicitly setting ``parser_classes = [parsers.MultiPartParser]`` (or any file compatible parser)
on your ``View`` or write a custom ``get_parser_classes``. These fields do not work with the default ``JsonParser``
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

The extensions register themselves automatically. Just be sure that the Python interpreter sees them at least once.
It is good practice to collect your extensions in ``YOUR_MAIN_APP_NAME/schema.py`` and to import that
file in your ``YOUR_MAIN_APP_NAME/apps.py``. Performing the import in the ``ready()`` method is the most robust
approach. It will make sure your environment (e.g. settings) is properly set up prior to loading.

  .. code-block:: python

    # your_main_app_name/apps.py
    class YourMainAppNameConfig(AppConfig):
        default_auto_field = "django.db.models.BigAutoField"
        name = "your_main_app_name"

        def ready(self):
            import your_main_app_name.schema  # noqa: E402



While there are certainly other ways of loading your extensions, this is a battle-proven and robust way to do it.
Generally in Django/DRF, importing stuff in the wrong order often results in weird errors or circular
import issues, which this approach tries to carefully circumvent.


My ``@action`` is erroneously paginated or has filter parameters that I do not want
-----------------------------------------------------------------------------------

This usually happens when ``@extend_schema(responses=XSerializer(many=True))`` is used. Actions inherit filter
and pagination classes from their ``ViewSet``. If the response is then marked as a list, the ``pagination_class``
kicks in. Since actions are handled manually by the user, this behavior is usually not immediately obvious.
To make your intentions clear to *drf-spectacular*, you need to clear the offending classes in the action
decorator, e.g. setting ``pagination_class=None``.

Users of *django-filter* might also see unwanted query parameters. Since the same mechanics apply here too,
you can remove those parameters by resetting the filter backends with ``@action(...,filter_backends=[])``.

.. code-block:: python

    class XViewset(viewsets.ModelViewSet):
        queryset = SimpleModel.objects.all()
        pagination_class = pagination.LimitOffsetPagination

        @extend_schema(responses=SimpleSerializer(many=True))
        @action(methods=['GET'], detail=False, pagination_class=None)
        def custom_action(self):
            pass

How do I wrap my responses? / My endpoints are wrapped in a generic envelope
----------------------------------------------------------------------------

This non-native behavior can be conveniently modeled with a simple helper function. You simply need
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

How can I have multiple ``SpectacularAPIView`` with differing settings
----------------------------------------------------------------------

First, define your base settings in ``settings.py`` with ``SPECTACULAR_SETTINGS``. Then,
if you need another schema with different settings, you can provide scoped overrides by
providing a ``custom_settings`` argument. ``custom_settings`` expects a ``dict`` and only
allows keys that represent valid setting names.

Beware that using this mechanic is not thread-safe at the moment.

Also note that overriding ``SERVE_*`` or ``DEFAULT_GENERATOR_CLASS`` in ``custom_settings`` is
not allowed. ``SpectacularAPIView`` has dedicated arguments for overriding these settings.

.. code-block:: python

    urlpatterns = [
        path('api/schema/', SpectacularAPIView.as_view(),
        path('api/schema-custom/', SpectacularAPIView.as_view(
            custom_settings={
                'TITLE': 'your custom title',
                'SCHEMA_PATH_PREFIX': 'your custom regex',
                ...
            }
        ), name='schema-custom'),
    ]

How to correctly annotate function-based views that use ``@api_view()``
-----------------------------------------------------------------------

DRF provides a convenient way to write function-based views. ``@api_view()`` in essence wraps a regular
function and implicitly converts it to a ``APIView`` class. For single-method cases, simply use
:py:func:`@extend_schema <drf_spectacular.utils.extend_schema>` just as you would with a normal view method.

.. code-block:: python

    @extend_schema(request=XSerializer, responses=XSerializer)
    @api_view(['POST'])
    def view_func(request, format=None):
        return ...

For functions that provide multiple methods, its advisable to use :py:func:`@extend_schema_view <drf_spectacular.utils.extend_schema_view>`
and break down each case separately.

.. code-block:: python

    @extend_schema_view(
        get=extend_schema(description='get desc', responses=XSerializer),
        post=extend_schema(description='post desc', request=None, responses=OpenApiTypes.UUID),
    )
    @api_view(['GET', 'POST'])
    def view_func(request, format=None):
        return ...

My ``get_queryset()`` depends on some attributes not available at schema generation time
----------------------------------------------------------------------------------------

In certain situations we need to call ``get_serializer``, which in turn calls ``get_queryset``.
If your ``get_queryset`` (or ``get_serializer_class``) depends on attributes not available at
schema generation time (e.g. ``request.user.is_authenticated``), you need to provide a fallback
that allows us to call that method. While the schema is generated, you can check for the view
attribute ``swagger_fake_view`` and simply return an empty queryset of the correct model.

.. code-block:: python

    class XViewset(viewsets.ModelViewset):
        ...

        def get_queryset(self):
            if getattr(self, 'swagger_fake_view', False):  # drf-yasg comp
                return YourModel.objects.none()
            # your usual logic


How to serve in-memory generated files or files in general outside ``FileField``
--------------------------------------------------------------------------------

DRF provides a convenient ``FileField`` for storing files persistently within a ``Model``.
``drf-spectacular`` handles these correctly by default. But to serve binary files that are
*generated in-memory*, follow the following recipe. This example uses the method
`recommended by Django <https://docs.djangoproject.com/en/4.0/ref/request-response/#telling-the-browser-to-treat-the-response-as-a-file-attachment>`_
for treating a ``Response`` as a file and sets up an appropriate ``Renderer`` that will handle the
client ``Accept`` header for this response content type. ``responses=bytes`` expresses that the
response is a binary blob without further details on its structure.

.. code-block:: python

    from django.http import HttpResponse
    from rest_framework.renderers import BaseRenderer


    class BinaryRenderer(BaseRenderer):
        media_type = "application/octet-stream"
        format = "bin"


    class FileViewSet(RetrieveModelMixin, GenericViewSet):
        ...
        renderer_classes = [BinaryRenderer]

        @extend_schema(responses=bytes)
        def retrieve(self, request, *args, **kwargs):
            export_data = b"..."
            return HttpResponse(
                export_data,
                content_type=BinaryRenderer.media_type,
                headers={
                    "Content-Disposition": "attachment; filename=out.bin",
                },
            )

My ``ViewSet`` ``list`` does not return a list, but a single object.
--------------------------------------------------------------------

Generally, it is bad practice to use a ``ViewSet.list`` method to return single object,
because DRF specifically does a list conversion in the background for this method and only
this method. Using ``ApiView`` or ``GenericAPIView`` for this use-case would be cleaner.

However, if you insist on this behavior, you can circumvent the list detection by
creating a one-off copy of your serializer and marking it as forced non-list.
It is important to create a **copy** as
:py:func:`@extend_schema_serializer <drf_spectacular.utils.extend_schema_serializer>`
modifies the given serializer.

.. code-block:: python

    from drf_spectacular.helpers import forced_singular_serializer

    class YourViewSet(viewsets.ModelViewSet):
        serializer_class = SimpleSerializer
        queryset = SimpleModel.objects.none()

        @extend_schema(responses=forced_singular_serializer(SimpleSerializer))
        def list(self):
            pass
