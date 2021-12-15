.. _blueprints:

Extension Blueprints
====================

Blueprints are a collection of schema fixes for Django and REST Framework apps.
Some libraries/apps do not play well with `drf-spectacular`'s automatic introspection.
With extensions you can manually provide the necessary information to generate a better schema.

There is no blueprint for the app you are looking for? No problem, you can easily write extensions
yourself. Take the blueprints here as examples and have a look at :ref:`customization`.
Feel free to contribute new ones or fixes with a `PR <https://github.com/tfranzel/drf-spectacular/pulls>`_.
Blueprint files can be found `here <https://github.com/tfranzel/drf-spectacular/tree/master/docs/blueprints>`_.

.. note:: Simply copy&paste the snippets into your codebase. The extensions register
  themselves automatically. Just be sure that the python interpreter sees them at least once.
  To that end, we suggest creating a ``PROJECT/schema.py`` file and importing it in your
  ``PROJECT/__init__.py`` (same directory as ``settings.py`` and ``urls.py``)
  with ``import PROJECT.schema``. Now you are all set.


dj-stripe
---------

Stripe Models for Django: `dj-stripe <https://github.com/dj-stripe/dj-stripe>`_

.. literalinclude:: blueprints/djstripe.py


django-oscar-api
----------------

RESTful API for django-oscar: `django-oscar-api <https://github.com/django-oscar/django-oscar-api>`_

.. literalinclude:: blueprints/oscarapi.py


djangorestframework-api-key
---------------------------

Since `djangorestframework-api-key <https://github.com/florimondmanca/djangorestframework-api-key>`_ has
no entry in ``authentication_classes``, `drf-spectacular` cannot pick up this library. To alleviate
this shortcoming, you can manually add the appropriate security scheme.

.. note:: Usage of the ``SECURITY`` setting is discouraged, unless there are special circumstances
  like here for example. For almost all cases ``OpenApiAuthenticationExtension`` is strongly preferred,
  because ``SECURITY`` will get appended to every endpoint in the schema regardless of effectiveness.

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


Polymorphic models
------------------

Using polymorphic models/serializers unfortunately yields flat serializers due to the way
the serializers are constructed. This means the polymorphic serializers have no inheritance
hierarchy that represents common functionality. These extensions retroactively build a
hierarchy by rolling up the "common denominator" fields into the base components, and
importing those into the sub-components via ``allOf``. This results in components that better
represent the structure of the underlying serializers/models from which they originated.

The components work perfectly fine without this extension, but in some cases generated
client code has a hard time with the disjunctive nature of the unmodified components.
This blueprint is designed to fix that issue.

.. literalinclude:: blueprints/rollup.py

RapiDoc
-------

`RapiDoc`__ is documentation tool that can be used as an alternate to Redoc or Swagger UI.

__ https://mrin9.github.io/RapiDoc/

.. literalinclude:: blueprints/rapidoc.py

.. literalinclude:: blueprints/rapidoc.html


drf-rw-serializers
------------------

`drf-rw-serializers`__ provides generic views, viewsets and mixins that extend the Django REST
Framework ones adding separated serializers for read and write operations.

`drf-spectacular` requires just a small ``AutoSchema`` augmentation to make it aware of
``drf-rw-serializers``. Remember to replace the ``AutoSchema`` in ``DEFAULT_SCHEMA_CLASS``.

__ https://github.com/vintasoftware/drf-rw-serializers

.. literalinclude:: blueprints/drf_rw_serializers.py

drf-extra-fields Base64FileField
--------------------------------

`drf-extra-fields`__ provides a ``Base64FileField`` and ``Base64ImageField`` that automatically
represent binary files as base64 encoded strings. This is a useful way to embed files within a
larger JSON API and keep all data within the same tree and served with a single request or
response.

Because requests to these fields require a base64 encoded string and responses can be either a
URI or base64 contents (if ``represent_as_base64=True``) custom schema generation
logic is required as this differs from the default DRF ``FileField``.

.. literalinclude:: blueprints/drf_extra_fields.py

__ https://github.com/Hipo/drf-extra-fields

django-auth-adfs
----------------

`django-auth-adfs <https://github.com/snok/django-auth-adfs>`_ provides "a Django authentication backend for Microsoft ADFS and Azure AD".
The blueprint works for the Azure AD configuration guide (see: https://django-auth-adfs.readthedocs.io/en/latest/azure_ad_config_guide.html).

.. literalinclude:: blueprints/django_auth_adfs.py
