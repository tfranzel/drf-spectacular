Settings
========


Settings are configurable in ``settings.py`` in the scope ``SPECTACULAR_SETTINGS``.
You can override any setting, otherwise the defaults below are used.


.. literalinclude:: ../drf_spectacular/settings.py
   :start-after: APISettings
   :end-before: IMPORT_STRINGS

Example: API Key securitySchemes & security setting
---------------------------------------------------------------------

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
    }

Django Rest Framework settings
------------------------------

Some of the `Django Rest Framework settings <https://www.django-rest-framework.org/api-guide/settings/>`_
also impact the schema generation.  Refer to the documentation for the version that you are using.

Settings which effect the processing of requests and data types of responses will usually be effective.

There is explicit use of these settings:

- `COERCE_DECIMAL_TO_STRING`
- `UPLOADED_FILES_USE_URL`

The following settings are ignored:

- `SCHEMA_COERCE_METHOD_NAMES`

The following are known to be effective:

- `SCHEMA_COERCE_PATH_PK`
- `FORMAT_SUFFIX_KWARG`
- `URL_FORMAT_OVERRIDE`
