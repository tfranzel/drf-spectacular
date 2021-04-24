.. _client_generation:

Client generation
===============================

`drf-spectacular` aims to generate the most accurate schema possible under the constraints of OpenAPI 3.0.3.
Unfortunately, sometimes this goal conflicts with generating a good and functional client.

To serve the two main use cases, i.e. documenting the API and generating clients, we opt for getting the
most accurate schema first, and then provide settings that allow to resolve potential issues with client generation.

.. note:: TL;DR - Simply setting ``'COMPONENT_SPLIT_REQUEST': True`` will most likely yield the best
  and most accurate client.

.. note:: `drf-spectacular` generates warnings where it recognizes potential problems. Some warnings
  are important to having a correct client. Fixing all warning is highly recommended.

.. note:: For generating clients with CI, we highly recommend using
  ``./manage.py spectacular --file schema.yaml --validate --fail-on-warn`` to catch potential problems
  early on.

Component issues
----------------

Most client issues revolve around the construction of components. Some client targets have trouble with
``readOnly`` and ``required`` fields like ``id``. Even though technically correct, the generated code may not
allow creating objects with ``id`` missing for ``POST`` requests. Some fields like ``FileField`` behave very
differently on requests and responses and are simply not translatable into a single component.

The most useful setting is ``'COMPONENT_SPLIT_REQUEST': True``, where all affected components are split
into request and response components. This takes care of almost all ``required``, ``writeOnly``, ``readOnly``
issues, and generally delivers code that is easier to understand and harder to misuse.

Sometimes you may only want to fix the ``required``/``readOnly`` issue without splitting all components.
This can be explicitly addressed with ``'COMPONENT_NO_READ_ONLY_REQUIRED': True``. Because this setting waters
down the correctness of the schema, we generally recommend using ``COMPONENT_SPLIT_REQUEST`` instead.

``'COMPONENT_SPLIT_PATCH': True`` is already enabled by default as ``PATCH`` and ``POST`` requests clash
on the ``required`` property and cannot be adequately modeled with a single component.

Relevant settings:

.. code:: python

    # Split components into request and response parts where appropriate
    'COMPONENT_SPLIT_REQUEST': False,
    # Aid client generator targets that have trouble with read-only properties.
    'COMPONENT_NO_READ_ONLY_REQUIRED': False,
    # Create separate components for PATCH endpoints (without required list)
    'COMPONENT_SPLIT_PATCH': True,



Enum issues
-----------

Some generator targets choke on combined enum components or having a ``null`` choice on a ``nullable: true``
field. Even though it is the correct way (according to the specification), it sadly breaks some generator targets.
Setting ``'ENUM_ADD_EXPLICIT_BLANK_NULL_CHOICE': False`` will create a less accurate schema that tends to offend
fewer generator targets.

For more information please refer to the `official documentation <https://swagger.io/docs/specification/data-models/enums/>`_ and
more specifically the `specification proposal <https://github.com/OAI/OpenAPI-Specification/blob/master/proposals/003_Clarify-Nullable.md#if-a-schema-specifies-nullable-true-and-enum-1-2-3-does-that-schema-allow-null-values-see-1900>`_.

Relevant settings:

.. code:: python

    # Adds "blank" and "null" enum choices where appropriate. disable on client generation issues
    'ENUM_ADD_EXPLICIT_BLANK_NULL_CHOICE': True,


Type issues
-----------

Some generator targets behave differently depending on how ``additionalProperties`` is structured.
According to the specification all three variations should yield identical results, which unfortunately
is not the case in practice.

Relevant settings:

.. code:: python

    # Determines if and how free-form 'additionalProperties' should be emitted in the schema. Some
    # code generator targets are sensitive to this. None disables generic 'additionalProperties'.
    # allowed values are 'dict', 'bool', None
    'GENERIC_ADDITIONAL_PROPERTIES': 'dict',
