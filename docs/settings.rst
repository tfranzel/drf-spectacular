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