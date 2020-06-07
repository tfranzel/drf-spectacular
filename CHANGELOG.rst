Changelog
=========

0.9.8 (2020-06-07)
------------------

- bugfix read-only many2many relation processing `#79 <https://github.com/tfranzel/drf-spectacular/issues/79>`_
- Implement OrderedDict representer for yaml dumper [Jair Henrique]
- bugfix UI permissions `#84 <https://github.com/tfranzel/drf-spectacular/issues/84>`_
- fix abc import `#82 <https://github.com/tfranzel/drf-spectacular/issues/82>`_
- add duration field `#78 <https://github.com/tfranzel/drf-spectacular/issues/78>`_

0.9.7 (2020-06-05)
------------------

- put contrib code in packages named files
- improve djangorestframework-camel-case support `#73 <https://github.com/tfranzel/drf-spectacular/issues/73>`_
- Add support to djangorestframework-camel-case [Jair Henrique]
- ENUM_NAME_OVERRIDES accepts import string for easier handling `#70 <https://github.com/tfranzel/drf-spectacular/issues/70>`_
- honor versioning on schema UIs `#71 <https://github.com/tfranzel/drf-spectacular/issues/71>`_
- improve enum naming mechanism. `#63 <https://github.com/tfranzel/drf-spectacular/issues/63>`_ `#70 <https://github.com/tfranzel/drf-spectacular/issues/70>`_
- provide global enum naming. `#70 <https://github.com/tfranzel/drf-spectacular/issues/70>`_
- refactor choice field
- remove unused sorter setting
- improve FileField, add test and documentation. `#69 <https://github.com/tfranzel/drf-spectacular/issues/69>`_
- Fix file fields [John Vandenberg]
- allow for functions on models beside properties. `#68 <https://github.com/tfranzel/drf-spectacular/issues/68>`_
- replace removed DRF compat function

Breaking changes:

- Enum naming conflicts are now resolved explicitly. `how to resolve conflicts <https://drf-spectacular.readthedocs.io/en/latest/faq.html#i-get-warnings-regarding-my-enum-or-my-enum-names-have-a-weird-suffix>`_
- Choice fields may be rendered slightly different
- Swagger UI and Redoc views now honor versioned requests
- Contrib package code moved. each package has its own file now

0.9.6 (2020-05-23)
------------------

- overhaul documentation `#52 <https://github.com/tfranzel/drf-spectacular/issues/52>`_
- improve serializer field mapping (nullbool & time)
- remove duplicate and misplaced description. `#61 <https://github.com/tfranzel/drf-spectacular/issues/61>`_
- extract serializer docstring
- Recognise ListModelMixin as a list [John Vandenberg]
- bugfix component sorting to include enums. `#60 <https://github.com/tfranzel/drf-spectacular/issues/60>`_
- bugfix fail on missing readOnly flag
- Fix incorrect parameter cutting [p.alekseev]

0.9.5 (2020-05-20)
------------------

- add optional serializer component split
- improve SerializerField meta extraction
- improve serializer directionality
- add mypy static analysis
- make all readonly fields required for output. `#54 <https://github.com/tfranzel/drf-spectacular/issues/54>`_
- make yaml multi-line strings nicer
- alphanumeric component sorting.
- generalize postprocessing hooks
- extension override through priority attr

Breaking changes:

- Schemas are funtionally identical, but component sorting changed slightly.
- All ``read_only`` fields are required by default
- ``SerializerFieldExtension`` gained direction parameter

0.9.4 (2020-05-13)
------------------

- robustify serializer resolution & enum postprocessing 
- expose api_version to command. robustify version matching. `#22 <https://github.com/tfranzel/drf-spectacular/issues/22>`_ 
- add versioning support `#22 <https://github.com/tfranzel/drf-spectacular/issues/22>`_ 
- robustify urlconf wrapping. resolver does not like lists 
- explicit override for non-list serializers on ViewSet list `#49 <https://github.com/tfranzel/drf-spectacular/issues/49>`_ 
- improve model field mapping via DRF init logic 
- bugfix enum substitution with additional field parameters. 
- Fix getting default parameter for `MultipleChoiceField` [p.alekseev]
- bugfix model path traversal via intermediate property 
- try to be more graceful with unknown custom model fields. `#33 <https://github.com/tfranzel/drf-spectacular/issues/33>`_ 

Breaking changes:

- If URL or namespace versioning is set in views, it is automatically used for generation. 
  Schemas might shrink because of that. Explicit usage of ``--api-version="XXX"`` should yield the old result.
- Some warnings might change, as the field/view introspection tries to go deeper.

0.9.3 (2020-05-07)
------------------

- Add (partial) support for drf-yasg's serializer ref_name `#27 <https://github.com/tfranzel/drf-spectacular/issues/27>`_ 
- Add thin wrappers for redoc and swagger-ui. `#19 <https://github.com/tfranzel/drf-spectacular/issues/19>`_ 
- Simplify serializer naming override `#27 <https://github.com/tfranzel/drf-spectacular/issues/27>`_ 
- Handle drf type error for yaml. `#41 <https://github.com/tfranzel/drf-spectacular/issues/41>`_ 
- Tox.ini: Add {posargs} [John Vandenberg]
- add djangorestframework-jwt auth handler [John Vandenberg]
- Docs: example of a manual configuration to use a apiKey in securitySchemes [Jelmer Draaijer]
- Introduce view override extension 
- Consolidate extensions 
- Parse path parameter type hints from url. closes `#34 <https://github.com/tfranzel/drf-spectacular/issues/34>`_ 
- Consolidate duplicate warnings/add error `#28 <https://github.com/tfranzel/drf-spectacular/issues/28>`_ 
- Prevent warning for DRF format suffix param 
- Improve ACCEPT header handling `#42 <https://github.com/tfranzel/drf-spectacular/issues/42>`_ 

Breaking changes:

- all extension base classes moved to ``drf_spectacular.extensions``


0.9.2 (2020-04-27)
------------------

- Fix incorrect PK access through id. `#25 <https://github.com/tfranzel/drf-spectacular/issues/25>`_.
- Enable attr settings on SpectacularAPIView `#35 <https://github.com/tfranzel/drf-spectacular/issues/35>`_.
- Bugfix @api_view annotation and tests.
- Fix exception/add support for explicit ListSerializer `#29 <https://github.com/tfranzel/drf-spectacular/issues/29>`_.
- Introduce custom serializer field extension mechanic. enables tackling `#31 <https://github.com/tfranzel/drf-spectacular/issues/31>`_
- Improve serializer estimation with educated guesses. `#28 <https://github.com/tfranzel/drf-spectacular/issues/28>`_.
- Bugfix import error and incorrect warning `#26 <https://github.com/tfranzel/drf-spectacular/issues/26>`_.
- Improve scope parsing for oauth2. `#26 <https://github.com/tfranzel/drf-spectacular/issues/26>`_.
- Postprocessing enums to components
- Handle decimal coersion. closes `#24 <https://github.com/tfranzel/drf-spectacular/issues/24>`_.
- Improvement: patched serializer variation only on request.
- Add serializer directionality.
- End the bucket brigade / cleaner interface.
- Add poly serializer warning.
- Bugfix: add serialization for default values.
- Bugfix reverse access collision from schema to view.

Breaking changes:

- internal interface changed (method & path removed)
- fewer PatchedSerializers emitted
- Enums are no longer inlined

0.9.1 (2020-04-09)
------------------

- Bugfix missing openapi schema spec json in package
- Add multi-method action decoration support.
- rest-polymorphic str loading prep.
- Improve list view detection.
- Bugfix: response codes must be string. closes `#17 <https://github.com/tfranzel/drf-spectacular/issues/17>`_.

0.9.0 (2020-03-29)
------------------

- Add missing related serializer fields `#15 <https://github.com/tfranzel/drf-spectacular/issues/15>`_.
- Bugfix properties with $ref component. closes `#16 <https://github.com/tfranzel/drf-spectacular/issues/16>`_.
- Bugfix polymorphic resource_type lookup. closes `#14 <https://github.com/tfranzel/drf-spectacular/issues/14>`_.
- Generalize plugin system.
- Support ``required`` parameter for body. [p.alekseev]
- Improve serializer retrieval.
- Add query serializer support `#10 <https://github.com/tfranzel/drf-spectacular/issues/10>`_.
- Custom serializer parsing with plugins.
- Refactor auth plugin system. support for DjangoOAuthToolkit & SimpleJWT.
- Bugfix extra components.

Breaking changes:

- removed `to_schema()` from `OpenApiParameter`. Handled in ``AutoSchema`` now.

0.8.8 (2020-03-21)
------------------
- Documentation. 
- Schema serving with ``SpectacularAPIView``  (configureable)
- Add generator stats and ``--fail-on-warn`` command option. 
- Schema validation with ``--validation`` against OpenAPI JSON specification
- Added various settings.
- Bugfix/add support for basic type responses (parity with requests)
- Bugfix required in parameters. failed schema validation. 
- Add validation against OpenAPI schema specification. 
- Improve parameter resolution, warnings and tests. 
- Allow default parameter override. (e.g. ``id``)
- Fix queryset function call. [p.g.alekseev]
- Supporting enum values in params. [p.g.alekseev]
- Allow ``@extend_schema`` request basic type annotation.
- Add support for typing Optional[*] 
- Bugfix: handle proxy models where pk is a OnetoOne relation.
- Warn on duplicate serializer names. 
- Added explicit exclude flag for operation. 
- Bugfix: PrimaryKeyRelatedField(read_only=True) failing to find type.
- Change operation sorting to alphanumeric with option (`#6 <https://github.com/tfranzel/drf-spectacular/issues/6>`_) 
- Robustify serializer field support for ``@extend_schema_field``.
- Enable field serializers support. [p.g.alekseev]
- Adding custom tags support [p.g.alekseev]
- Document extend_schema. 
- Allow operation hiding. 
- Catch unknown model traversals. custom fields can be tricky. 
- Improve model field mapping. extend field tests. 
- Add deprecated method to extend_schema decorator. [p.g.alekseev]

Breaking changes: 

- ``@extend_schema`` renamed ``extra_parameters`` -> ``parameters``
- ``ExtraParameter`` renamed to ``OpenApiParameter``

0.8.5 (2020-03-08)
------------------
- Generalize ``PolymorphicResponse`` into ``PolymorphicProxySerializer``.
- Type dict is resolved as object. 
- Simplify hint resolution. 
- Allow ``@extend_schema_field`` for custom serializer fields.


0.8.4 (2020-03-06)
------------------
- ``@extend_schema_field`` accepts Serializers and OpenApiTypes
- Generalize query parameter. 
- Bugfix serializer init.
- Fix unused get_request_serializer.
- Refactor and robustify typing system. 
- Helper scripts for swagger and generator. 
- Fix license. 


0.8.3 (2020-03-02)
------------------
- Fix parameter type resolution. 
- Remove empty parameters. 
- Improved assert message. 


0.8.2 (2020-03-02)
------------------
- Working release. 
- Bugfix wrong call & remove yaml aliases. 


0.8.1 (2020-03-01)
------------------
- Initial published version. 

