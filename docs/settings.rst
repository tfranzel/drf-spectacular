Settings
========


Settings are configurable in ``settings.py`` in the scope ``SPECTACULAR_SETTINGS``.
You can override any setting, otherwise the defaults below are used.


.. literalinclude:: ../drf_spectacular/settings.py
   :start-after: APISettings
   :end-before: IMPORT_STRINGS


Django Rest Framework settings
------------------------------

Some of the `Django Rest Framework settings <https://www.django-rest-framework.org/api-guide/settings/>`_
also impact the schema generation.  Refer to the documentation for the version that you are using.

Settings which effect the processing of requests and data types of responses will usually be effective.

There is explicit use of these settings:

- ``DEFAULT_SCHEMA_CLASS``
- ``COERCE_DECIMAL_TO_STRING``
- ``UPLOADED_FILES_USE_URL``
- ``URL_FORMAT_OVERRIDE``
- ``FORMAT_SUFFIX_KWARG``

The following settings are ignored:

- ``SCHEMA_COERCE_METHOD_NAMES``

The following are known to be effective:

- ``SCHEMA_COERCE_PATH_PK``


Example: API Key securitySchemes & security setting
----------------------------------------------------

When using djangorestframework-api-key_ for example, the `specs
<https://swagger.io/docs/specification/authentication/>`_  tell you you need to add an entry to the securitySchemes component and set it to the global security section.

This can be done in the following way:


.. _djangorestframework-api-key: https://github.com/florimondmanca/djangorestframework-api-key/

.. code:: python

    SPECTACULAR_SETTINGS = {
        "APPEND_COMPONENTS": {
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "Authorization"
                }
            }
        },
        "SECURITY": [{"ApiKeyAuth": [], }],
         ...
    }



Example: SwaggerUI settings
----------------------------

We does not support SwaggerUI Config Param at the settings.py which is based JS Function

If you want, override swagger_ui.html & SpectacularSwaggerView.

.. code:: python

    SPECTACULAR_SETTINGS = {
        ...
        # configuration param should correspond to the documents below.
        # https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/
        "SWAGGER_UI_SETTINGS": {
            "dom_id": "#swagger-ui", # default
            "layout": "BaseLayout",  # requried(default)
            "deepLinking": True,
            "persistAuthorization": True,
            "displayOperationId": True,
            # ...
        },

        # check SwaggerUI Version what you want, https://github.com/swagger-api/swagger-ui/releases
        "SWAGGER_UI_DIST": "//unpkg.com/swagger-ui-dist@3.35.1", # default
        "FAVICON_HREF": settings.STATIC_URL + "your_company_favicon.png", # default is swagger favicon
        ...
    }

