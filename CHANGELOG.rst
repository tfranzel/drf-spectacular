Changelog
=========


0.13.0 (2021-01-13)
-------------------

- add setting for additionalProperties handling `#238 <https://github.com/tfranzel/drf-spectacular/issues/238>`_
- bugfix path param extraction for PrimaryKeyRelatedField `#258 <https://github.com/tfranzel/drf-spectacular/issues/258>`_
- use injected django-filter help_text `#234 <https://github.com/tfranzel/drf-spectacular/issues/234>`_
- robustify normalization of tyes `#257 <https://github.com/tfranzel/drf-spectacular/issues/257>`_
- bugfix PATCH split serializer disparity `#249 <https://github.com/tfranzel/drf-spectacular/issues/249>`_
- django-filter description bugfix `#234 <https://github.com/tfranzel/drf-spectacular/issues/234>`_
- bugfix unsupported http verbs `#244 <https://github.com/tfranzel/drf-spectacular/issues/244>`_
- bugfix assert on methods in django-filter `#252 <https://github.com/tfranzel/drf-spectacular/issues/252>`_ `#234 <https://github.com/tfranzel/drf-spectacular/issues/234>`_ `#241 <https://github.com/tfranzel/drf-spectacular/issues/241>`_
- Regression: Filterset defined as method (and from a @property) are not supported [Nicolas Delaby]
- bugfix view-level AutoSchema noneffective with extend_schema `#241 <https://github.com/tfranzel/drf-spectacular/issues/241>`_
- bugfix incorrect warning on paginated actions `#233 <https://github.com/tfranzel/drf-spectacular/issues/233>`_

Breaking changes:

- several small improvements that should not have a big impact. this is a y-stream release mainly due to schema changes that may occur with ``django-filter``.


0.12.0 (2020-12-19)
-------------------

- add exclusion for discovered parameters `#212 <https://github.com/tfranzel/drf-spectacular/issues/212>`_
- bugfix incorrect collision warning `#233 <https://github.com/tfranzel/drf-spectacular/issues/233>`_
- introduce filter extensions `#234 <https://github.com/tfranzel/drf-spectacular/issues/234>`_
- revert Swagger UI view to single request and alternative `#211 <https://github.com/tfranzel/drf-spectacular/issues/211>`_ `#173 <https://github.com/tfranzel/drf-spectacular/issues/173>`_
- bugfix Simple JWT token refresh `#232 <https://github.com/tfranzel/drf-spectacular/issues/232>`_
- bugfix simple JWT serializer schema `#232 <https://github.com/tfranzel/drf-spectacular/issues/232>`_
- Fix enum postprocessor to allow 0 as possible value [Vikas]
- bugfix/restore optional default parameter value `#226 <https://github.com/tfranzel/drf-spectacular/issues/226>`_
- Include QuerySerializer in documentation [KimSoungRyoul]
- support OAS3.0 ExampleObject to @extend_schema & @extend_schema_serializer `#115 <https://github.com/tfranzel/drf-spectacular/issues/115>`_ [KimSoungRyoul]
- add explicit double and int32 types. `#214 <https://github.com/tfranzel/drf-spectacular/issues/214>`_
- added type extension for int64 format support [Peter Dreuw]
- fix TokenAuthentication handling of keyword `#205 <https://github.com/tfranzel/drf-spectacular/issues/205>`_
- Allow callable limit_value in schema [Serkan Hosca]
- @extend_schema responses param now accepts tuples with media type `#201 <https://github.com/tfranzel/drf-spectacular/issues/201>`_
- bugfix List hint extraction with non-basic sub types `#207 <https://github.com/tfranzel/drf-spectacular/issues/207>`_

Breaking changes:

- reverted back to ``0.10.0`` Swagger UI behavior as default. Users relying on stricter CSP should use ``SpectacularSwaggerSplitView``
- ``tokenAuth`` slightly changed to properly model correct ``Authorization`` header
- a lot of minor improvements that may slightly alter the schema

0.11.1 (2020-11-15)
-------------------

- bugfix hint extraction on @cached_property `#198 <https://github.com/tfranzel/drf-spectacular/issues/198>`_
- add support for basic TypedDict hints `#184 <https://github.com/tfranzel/drf-spectacular/issues/184>`_
- improve type hint resolution `#199 <https://github.com/tfranzel/drf-spectacular/issues/199>`_
- add option to disable Null/Blank enum choice feature `#185 <https://github.com/tfranzel/drf-spectacular/issues/185>`_
- bugfix return code for Viewset create methods `#196 <https://github.com/tfranzel/drf-spectacular/issues/196>`_
- honor SCHEMA_COERCE_PATH_PK on path param type resolution `#194 <https://github.com/tfranzel/drf-spectacular/issues/194>`_
- bugfix absolute schema URL to relative in UI `#193 <https://github.com/tfranzel/drf-spectacular/issues/193>`_

Breaking changes:

- return code for ``create`` on ``ViewSet`` changed from ``200`` to ``201``. Some generator targets are picky, others don't care.

0.11.0 (2020-11-06)
-------------------

- Remove unnecessary view permission from action [Vikas]
- Fix security definition for IsAuthenticatedOrReadOnly permission [Vikas]
- introduce convenience decorator @schema_extend_view `#182 <https://github.com/tfranzel/drf-spectacular/issues/182>`_
- bugfix override behaviour of extend_schema with methods and views
- move some plumbing to drainage to make importable without cirular import issues
- bugfix naming for ListSerializer with pagination `#183 <https://github.com/tfranzel/drf-spectacular/issues/183>`_
- cleanup trailing whitespace in docstrings
- normalize regex in pattern, remove ECMA-incompatible URL pattern `#175 <https://github.com/tfranzel/drf-spectacular/issues/175>`_
- remove Swagger UI inline script for stricter CSP `#173 <https://github.com/tfranzel/drf-spectacular/issues/173>`_
- fixed typo [Sebastian Pabst]
- add the PASSWORD format to types.py [Sebastian Pabst]
- docs(settings): fix favicon example [Max Wittig]

Breaking changes:

- ``@extend_schema`` override mechanics are now consistent. may affect schema only if used on both view and view method
- otherwise mainly small improvement/fixes that should have minimal impact on the schema.

0.10.0 (2020-10-20)
-------------------

- bugfix non-effective multi-usage of view extension.
- improve resolvable enum collisions with split components
- Update README.rst [Jose Luis da Cruz Junior]
- fix regular expression in detype_pattern [Ruslan Ibragimov]
- improve enum naming with resolvable collisions
- improve handling of discouraged SECURITY setting (fixes `#48 <https://github.com/tfranzel/drf-spectacular/issues/48>`_ fixes `#136 <https://github.com/tfranzel/drf-spectacular/issues/136>`_)
- instance check with ViewSetMixin instead of GenericViewSet [SoungRyoul Kim]
- support swagger-ui-settings [SoungRyoul Kim]
- Change Settings variable, allow override of default swagger settings and remove unnecessary line [Nix]
- Fix whitspace issues in code [Nix]
- Allow Swagger-UI configuration through settings Closes `#162 <https://github.com/tfranzel/drf-spectacular/issues/162>`_ [Nix]
- extend django_filters test case `#155 <https://github.com/tfranzel/drf-spectacular/issues/155>`_
- add enum postprocessing handling of blank and null `#135 <https://github.com/tfranzel/drf-spectacular/issues/135>`_
- rest-auth improvements
- test_rest_auth: Add test schema transforms [John Vandenberg]
- tests: Allow transformers on expected schemas [John Vandenberg]
- Improve schema difference test harness [John Vandenberg]
- Add rest-auth tests [John Vandenberg]
- contrib: Add rest-auth support [John Vandenberg]

Breaking changes:

- enum naming collision resolution changed in cleanly resolvable situations.
- enums gained ``null`` and ``blank`` cases, which are modeled through ``oneOf`` for deduplication
- SECURITY setting is now additive instead of being the mostly overridden default

0.9.14 (2020-10-04)
-------------------

- improve client generation for paginated listings
- update pinned swagger-ui version `#160 <https://github.com/tfranzel/drf-spectacular/issues/160>`_
- Hot fix for AcceptVersioningHeader support [Nicolas Delaby]
- bugfix module string includes with urlpatterns `#157 <https://github.com/tfranzel/drf-spectacular/issues/157>`_
- add expressive error in case of misconfiguration `#156 <https://github.com/tfranzel/drf-spectacular/issues/156>`_
- fix django-filter related resolution. improve test `#150 <https://github.com/tfranzel/drf-spectacular/issues/150>`_ `#151 <https://github.com/tfranzel/drf-spectacular/issues/151>`_
- improve follow_field_source for reverse resolution and model leafs `#150 <https://github.com/tfranzel/drf-spectacular/issues/150>`_
- add ref if list field child is serializer [Matt Shirley]
- add customization option for mock request generation `#135 <https://github.com/tfranzel/drf-spectacular/issues/135>`_

Breaking changes:

- paginated list response is now wrapped in its own component

0.9.13 (2020-09-13)
-------------------

- bugfix filter parameter application on non-list views `#147 <https://github.com/tfranzel/drf-spectacular/issues/147>`_
- improved support for django-filter
- add mocked request for view processing. `#81 <https://github.com/tfranzel/drf-spectacular/issues/81>`_ `#141 <https://github.com/tfranzel/drf-spectacular/issues/141>`_
- Use sha256 to hash lists [David Davis]
- change empty operation name on API prefix-cut to "root"
- bugfix lost "missing hint" warning and incorrect empty fallback
- add operationId collision resolution `#137 <https://github.com/tfranzel/drf-spectacular/issues/137>`_
- bugfix leaking path var names in operationId `#137 <https://github.com/tfranzel/drf-spectacular/issues/137>`_
- add config for camelizing names `#138 <https://github.com/tfranzel/drf-spectacular/issues/138>`_
- bugfix parameterized patterns for namespace versioning `#145 <https://github.com/tfranzel/drf-spectacular/issues/145>`_
- Add support for Accept header versioning [Krzysztof Socha]
- support for DictField child type (`#142 <https://github.com/tfranzel/drf-spectacular/issues/142>`_) and models.JSONField (Django>=3.1)
- add convenience inline_serializer for extend_schema `#139 <https://github.com/tfranzel/drf-spectacular/issues/139>`_
- remove multipleOf due to schema violation `#131 <https://github.com/tfranzel/drf-spectacular/issues/131>`_

Breaking changes:

- ``operationId`` changed for endpoints using the DRF's ``FORMAT`` path feature.
- ``operationId`` changed where there were path variables leaking into the name.

0.9.12 (2020-07-22)
-------------------

- Temporarily pin the swagger-ui unpkg URL to 3.30.0 [Mohamed Abdulaziz]
- Add `deepLinking` parameter [p.alekseev]
- added preprocessing hooks for operation list modification/filtering `#93 <https://github.com/tfranzel/drf-spectacular/issues/93>`_
- Document effective DRF settings [John Vandenberg]
- add format query parameter `#110 <https://github.com/tfranzel/drf-spectacular/issues/110>`_
- improve assert messages `#126 <https://github.com/tfranzel/drf-spectacular/issues/126>`_
- more graceful handling of magic fields `#126 <https://github.com/tfranzel/drf-spectacular/issues/126>`_
- allow for field child on ListSerializer. `#120 <https://github.com/tfranzel/drf-spectacular/issues/120>`_
- Fix sorting of endpoints with params [John Vandenberg]
- Emit enum of possible format suffixes [John Vandenberg]
- i18n `#109 <https://github.com/tfranzel/drf-spectacular/issues/109>`_
- bugfix INSTALLED_APP retrieval `#114 <https://github.com/tfranzel/drf-spectacular/issues/114>`_
- emit import warning for extensions with installed apps `#114 <https://github.com/tfranzel/drf-spectacular/issues/114>`_

Breaking changes:

- ``drf_spectacular.hooks.postprocess_schema_enums`` moved from ``blumbing`` to ``hooks`` for consistency. Only relevant if ``POSTPROCESSING_HOOKS`` is explicitly set by user.
- preprocessing hooks are currently experimental and may change on the next release.

0.9.11 (2020-07-08)
-------------------

- extend instead of replace extra parameters `#111 <https://github.com/tfranzel/drf-spectacular/issues/111>`_
- add client generator helper settings for readOnly
- bugfix format param: path params must be required=True
- bugfix DRF docstring excludes and configuration `#107 <https://github.com/tfranzel/drf-spectacular/issues/107>`_
- bugfix operations with urlpattern override `#92 <https://github.com/tfranzel/drf-spectacular/issues/92>`_
- decrease built-in extension priority and improve doc `#106 <https://github.com/tfranzel/drf-spectacular/issues/106>`_
- add option to hide serializer fields `#100 <https://github.com/tfranzel/drf-spectacular/issues/100>`_
- allow None on @extend_schema request/response
- bugfix json spec violation on "required :[]" for COMPONENT_SPLIT_REQUEST

Breaking changes:

- ``@extend_schema(parameters=...)`` is extending instead of replacing for custom ``AutoSchema``
- path parameter are now always ``required=True`` as required by specification

0.9.10 (2020-06-23)
-------------------

- bugfix cyclic import in plumbing. `#104 <https://github.com/tfranzel/drf-spectacular/issues/104>`_
- add upstream test target with contrib allowed to fail
- preparations for django 3.1 and DRF 3.12
- improve tox targets for unreleased upstream

0.9.9 (2020-06-20)
------------------

- added explicit URL option to UI views. `#103 <https://github.com/tfranzel/drf-spectacular/issues/103>`_
- improve auth extension doc `#99 <https://github.com/tfranzel/drf-spectacular/issues/99>`_
- bugfix attr typo with Token auth extension `#99 <https://github.com/tfranzel/drf-spectacular/issues/99>`_
- improve docstring extraction `#96 <https://github.com/tfranzel/drf-spectacular/issues/96>`_
- Manual polymorphic [Jair Henrique]
- Add summary field to extend_schema `#97 <https://github.com/tfranzel/drf-spectacular/issues/97>`_ [lilisha100]
- reduce minimal package requirements
- extend sdist with tests & doc
- bugfix nested RO/WO serializer on COMPONENT_SPLIT_REQUEST
- add pytest option --skip-missing-contrib `#87 <https://github.com/tfranzel/drf-spectacular/issues/87>`_
- Save test files in temporary folder [Jair Henrique]
- Setup isort library [Jair Henrique]

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

