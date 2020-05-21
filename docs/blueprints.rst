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
  To that end, we recommend creating a ``YOURPROJECT/schema.py`` file and importing it in your
  ``settings.py`` with ``import * from YOURPROJECT.schema``. Now you are all set.


dj-stripe
---------

Stripe Models for Django: `dj-stripe <https://github.com/dj-stripe/dj-stripe>`_

.. literalinclude:: blueprints/djstripe.py


django-oscar-api
----------------

RESTful API for django-oscar: `django-oscar-api <https://github.com/django-oscar/django-oscar-api>`_

.. literalinclude:: blueprints/oscarapi.py