Changelog
=========

0.28.0 (2024-11-30)
-------------------

- Fix lazy_reverse bug in views (`#1339 <https://github.com/tfranzel/drf-spectacular/issues/1339>`_)
- Extend query params explosion of non-DRF serializer `#1315 <https://github.com/tfranzel/drf-spectacular/issues/1315>`_
- consider pk_field on PrimaryKeyRelatedField when set `#1335 <https://github.com/tfranzel/drf-spectacular/issues/1335>`_
- fix unused OAuth2 scopes override `#1319 <https://github.com/tfranzel/drf-spectacular/issues/1319>`_
- bugfix @extend_schema_field raw schema already in OAS3.1
- some minors (resolves `#1147 <https://github.com/tfranzel/drf-spectacular/issues/1147>`_)
- fix OAS3.1 validator omission `#1302 <https://github.com/tfranzel/drf-spectacular/issues/1302>`_
- guard against broken __dir__ impl `#1296 <https://github.com/tfranzel/drf-spectacular/issues/1296>`_
- Add Django 5.1 as classifier [jelmert]
- No extra items in the oneOf list [Vladimir]
- parametrize component registry identity `#1288 <https://github.com/tfranzel/drf-spectacular/issues/1288>`_
- make operation_id action position configurable `#1264 <https://github.com/tfranzel/drf-spectacular/issues/1264>`_
- Fix for incorrect ``issubclass()`` check. [Mike Moore]
- Correct the documentation of how to import extension snippets [Alan Crosswell]
- Update OpenAPI docs links [Nils Van Zuijlen]
- mitigate false positive in Django Debug Toolbar `#1159 <https://github.com/tfranzel/drf-spectacular/issues/1159>`_
- Additional testcase [Marti Raudsepp]
- Fix ChoiceField schema type with empty ``choices=[]`` [Marti Raudsepp]
- handle examples with nested properties pagination [François Rejeté]
- add choice field display method handling `#1228 <https://github.com/tfranzel/drf-spectacular/issues/1228>`_
- Add support for stateless user authentication in SimpleJWT (`#1221 <https://github.com/tfranzel/drf-spectacular/issues/1221>`_) [Willem Meints]
- fix: set pydantic json mode to serialization [Eric Butler]
- fix: extend_schema_field with dict param and oas 3.1 [Eric Butler]

Breaking changes / important additions:

- Y-stream release due to the amount of small but important changes.
- Pydantic users might see a slightly different schema due to the change in serialization method.

0.27.2 (2024-04-01)
-------------------

- fix non-translated enum override hash `#1198 <https://github.com/tfranzel/drf-spectacular/issues/1198>`_
- higher order hints for @extend_schema_field (case 2) `#1174 <https://github.com/tfranzel/drf-spectacular/issues/1174>`_ `#1212 <https://github.com/tfranzel/drf-spectacular/issues/1212>`_
- Add support for TypeAliasType (`#1214 <https://github.com/tfranzel/drf-spectacular/issues/1214>`_) [igorgaming]
- DRF 3.15 counteract new assertion for tests
- Add a specific Action Wrapper for OAuth Authorization requests `#1190 <https://github.com/tfranzel/drf-spectacular/issues/1190>`_ [Bram Esposito]
- Update SWAGGER_UI_DIST settings.rst [Alfie Day]
- fix custom http_method_names for actions `#1184 <https://github.com/tfranzel/drf-spectacular/issues/1184>`_
- Add support for direct usage of higher order hints `#1174 <https://github.com/tfranzel/drf-spectacular/issues/1174>`_
- Document ``extend_schema_view`` support for ``@action`` (`#1178 <https://github.com/tfranzel/drf-spectacular/issues/1178>`_) [johnthagen]
- remove official 3.6 support due to upstream breakage.
- Add auth extension for django-rest-knox [Callum Gare]
- fix yaml encoder for OrderedDict objects `#1158 <https://github.com/tfranzel/drf-spectacular/issues/1158>`_
- fix linter warning `#1158 <https://github.com/tfranzel/drf-spectacular/issues/1158>`_
- Update link to redoc settings [Andrey Otto]
- Add tags support to OpenApiWebhook [Federico Bond]
- set Cross-Origin-Opener-Policy on Swagger-UI view [ftsell]

Breaking changes / important additions:

- Some bugfixes and some functionality gaps closed.

0.27.1 (2024-01-18)
-------------------

- differentiate test cases for 3.1 null cases `#1139 <https://github.com/tfranzel/drf-spectacular/issues/1139>`_
- add enum suffix setting [Jonny Beaumont]
- Fix handling of metadata when using OAS 3.1 [Viicos]
- Provide all fixed field names for the components object [Sergei Maertens]
- coerse Decimal to float format explicitly `#1134 <https://github.com/tfranzel/drf-spectacular/issues/1134>`_
- bugfix test `#1133 <https://github.com/tfranzel/drf-spectacular/issues/1133>`_
- add OAS 3.1 null translation case `#1133 <https://github.com/tfranzel/drf-spectacular/issues/1133>`_
- Add OpenAPI 3.1 webhook support [Federico Bond]
- add OAS 3.1 null case

Breaking changes / important additions:

- Fixed some OAS 3.1 corner cases and added support for ``Webhooks`` (3.1) in addition to existing ``Callbacks``

0.27.0 (2023-12-12)
-------------------

- improve mypy typing `#600 <https://github.com/tfranzel/drf-spectacular/issues/600>`_
- add django 5 to test suite and adapt to changes `#1126 <https://github.com/tfranzel/drf-spectacular/issues/1126>`_
- Use correctly allowed http methods for schema generation [Jekel]
- OAS 3.1
- Fix Enum collision with same choices & varying labels `#790 <https://github.com/tfranzel/drf-spectacular/issues/790>`_ `#1104 <https://github.com/tfranzel/drf-spectacular/issues/1104>`_
- Undo adding middleware [Jelmer Draaijer]
- Set JWTTokenUserAuthentication to None when missing [Jelmer Draaijer]
- Add setuptools required for packaging [Jelmer Draaijer]
- Add allauth.account.middleware.AccountMiddleware to middleware [Jelmer Draaijer]
- Add Python 3.12 to test matrix and add classifiers [Jelmer Draaijer]
- Add official support for pydantic decoration.
- bugfix ignored OpenApiRequest case `#1106 <https://github.com/tfranzel/drf-spectacular/issues/1106>`_
- JSONField may also be a non-object/primitive `#1095 <https://github.com/tfranzel/drf-spectacular/issues/1095>`_
- add test for empty whitelist (no auth) `#1094 <https://github.com/tfranzel/drf-spectacular/issues/1094>`_
- Avoid ChoiceField duplicate enum values for allow_null, allow_blank (`#1085 <https://github.com/tfranzel/drf-spectacular/issues/1085>`_) [Marti Raudsepp]
- add test for django-filter and ListAPIView `#1086 <https://github.com/tfranzel/drf-spectacular/issues/1086>`_
- Fix the blueprint for pydantic version 2 [Carmen Alvarez]

Breaking changes / important additions:

- Biggest release in quite some time that contains a bunch of long running PR that finally found their way into master.
- We now officially support OpenAPI 3.1 and Pydantic 2
- Quite a few bug fixes (thanks to all contributors) and improved typing

0.26.5 (2023-09-23)
-------------------

- update FAQ entry on extension loading
- Fix (`#1079 <https://github.com/tfranzel/drf-spectacular/issues/1079>`_) crash when generating schema for field with UUID choices. [Pedro Borges]
- chore: fix typos [Heinz-Alexander Fuetterer]
- Use schema_url in SpectacularElementsView (`#1067 <https://github.com/tfranzel/drf-spectacular/issues/1067>`_) [q0w]
- add helper to disable viewset list detection `#1064 <https://github.com/tfranzel/drf-spectacular/issues/1064>`_
- pin django-allauth test dep due to breaking change with dj-rest-auth
- fix example building for pagination with basic list `#1055 <https://github.com/tfranzel/drf-spectacular/issues/1055>`_
- Fix discarded falsy examples values `#1049 <https://github.com/tfranzel/drf-spectacular/issues/1049>`_

Breaking changes / important additions:

- Added helper function ``forced_singular_serializer`` to disable a list detection on a endpoint, that has been quite difficult to properly
  undo previously. This closes the functional gap for ``@extend_schema_serializer(many=False)`` in single-use (non-envelope) situations.
- Several small bugfixes

0.26.4 (2023-07-23)
-------------------

- fix django-polymorphic empty serializer case `#1029 <https://github.com/tfranzel/drf-spectacular/issues/1029>`_ `#542 <https://github.com/tfranzel/drf-spectacular/issues/542>`_
- Add a blueprint for pydantic 2 [Carmen Alvarez]
- bugfix exclude behavior on subclassing `#1025 <https://github.com/tfranzel/drf-spectacular/issues/1025>`_
- relax django-filter subclassing restriction `#1022 <https://github.com/tfranzel/drf-spectacular/issues/1022>`_
- factor out serializer name estimation for easier modification `#976 <https://github.com/tfranzel/drf-spectacular/issues/976>`_
- Fixing Pydantic Extension (`#1021 <https://github.com/tfranzel/drf-spectacular/issues/1021>`_) [sydney-runkle]
- add Authorization header for oauth2 Bearer token [Danial]
- allow already supported lazy string in types `#982 <https://github.com/tfranzel/drf-spectacular/issues/982>`_

Breaking changes / important additions:

- some minor bugfixes as well as improvements to ``django-filter`` and ``django-polymorphic``.
- it is now significantly easier to adapt serializer naming via ``AutoSchema`` subclassing.

0.26.3 (2023-06-22)
-------------------

- allow implicit list expansion of PolymorphicProxySerializer `#995 <https://github.com/tfranzel/drf-spectacular/issues/995>`_
- selectively distinguish real serializers from mocked ones `#1006 <https://github.com/tfranzel/drf-spectacular/issues/1006>`_
- fix functionality gap for decoration of django-filter fields `#1007 <https://github.com/tfranzel/drf-spectacular/issues/1007>`_
- add pydantic blueprint
- robustify subclass check in extensions `#1006 <https://github.com/tfranzel/drf-spectacular/issues/1006>`_
- Prevent exception for non-serializer classes targeted by SerializerExtensions `#1006 <https://github.com/tfranzel/drf-spectacular/issues/1006>`_
- add middleware support for djangorestframework_camel_case
- close functionality gap in drf dataclasses naming `#1004 <https://github.com/tfranzel/drf-spectacular/issues/1004>`_
- fix: Camelize query parameters [v.kovalchuk]
- docs(examples): Fix wrong bool value in example [schew2381]
- bugfix test `#991 <https://github.com/tfranzel/drf-spectacular/issues/991>`_
- bugfix duplicate enum list for django-filter `#991 <https://github.com/tfranzel/drf-spectacular/issues/991>`_
- dj-rest-auth test changes 3.x -> 4.x
- Add blocks to redoc template `#978 <https://github.com/tfranzel/drf-spectacular/issues/978>`_

Breaking changes / important additions:

- no major changes but a multiude of small improvements.
- we are now a lot more tolerant when it comes to writing extensions for non-standard classes (e.g. Pydantic).
- there should be no unexpected schema changes except for when ``djangorestframework_camel_case``'s Middleware is used.

0.26.2 (2023-04-15)
-------------------

- fix jwt cookie name settings not being recognised (`#972 <https://github.com/tfranzel/drf-spectacular/issues/972>`_) [Nix Siow]
- Add OpenApiRequest for encoding options `#714 <https://github.com/tfranzel/drf-spectacular/issues/714>`_ `#965 <https://github.com/tfranzel/drf-spectacular/issues/965>`_

Breaking changes / important additions:

- small bugfix release that also contains the new ``OpenApiRequest`` feature

0.26.1 (2023-03-18)
-------------------

- reorder typed polymorphic fields `#958 <https://github.com/tfranzel/drf-spectacular/issues/958>`_
- Fix test warnings [Dmitry Gribanov]
- Fix PolymorphicSerializer type field handling `#885 <https://github.com/tfranzel/drf-spectacular/issues/885>`_ `#958 <https://github.com/tfranzel/drf-spectacular/issues/958>`_
- Add PresentablePrimarKeyRelatedField schema for drf-exrta-fields blueprint [Đào Minh Hạt]
- bugfix KeyError for disabled ENUM_GENERATE_CHOICE_DESCRIPTION `#952 <https://github.com/tfranzel/drf-spectacular/issues/952>`_

Breaking changes / important additions:

- small bugfix release that addresses a issue when turning off choice description generation
- improve/bugfix ``PolymorphicSerializer`` type field handling

0.26.0 (2023-03-04)
-------------------

- honor djangorestframework_camel_case settings "ignore_keys" and "ignore_fields" `#945 <https://github.com/tfranzel/drf-spectacular/issues/945>`_
- If available, use docstrings from properties for field descriptions (`#954 <https://github.com/tfranzel/drf-spectacular/issues/954>`_)
- Don't let validators override values already set in the schema (`#911 <https://github.com/tfranzel/drf-spectacular/issues/911>`_) [StopMotionCuber]
- add test and another case to `#901 <https://github.com/tfranzel/drf-spectacular/issues/901>`_
- add enum key/value list to description string `#337 <https://github.com/tfranzel/drf-spectacular/issues/337>`_ `#403 <https://github.com/tfranzel/drf-spectacular/issues/403>`_ `#105 <https://github.com/tfranzel/drf-spectacular/issues/105>`_ `#563 <https://github.com/tfranzel/drf-spectacular/issues/563>`_
- Add option to provide a callable for PolymorphicProxySerializer.serializers [Glenn Matthews]
- consolidate sort fix for enum sorting
- add testcase to `#950 <https://github.com/tfranzel/drf-spectacular/issues/950>`_. ensure raw schema dict remains unmodified
- Don't edit the original django-filters schema. [Will Giddens]
- Fix typos and grammar errors in FAQ doc page. [Foad Lind]
- fix OpenApiResponse nested example defaults `#875 <https://github.com/tfranzel/drf-spectacular/issues/875>`_
- mitigate ``runtests.py`` fail when GDAL library is not installed `#945 <https://github.com/tfranzel/drf-spectacular/issues/945>`_ `#821 <https://github.com/tfranzel/drf-spectacular/issues/821>`_ `#775 <https://github.com/tfranzel/drf-spectacular/issues/775>`_ `#777 <https://github.com/tfranzel/drf-spectacular/issues/777>`_
- bugfix SlugRelatedField with a model property target `#943 <https://github.com/tfranzel/drf-spectacular/issues/943>`_
- suppress erroneous warning for optional extensions `#940 <https://github.com/tfranzel/drf-spectacular/issues/940>`_
- fix whitelist mechanics (enables deny all) `#923 <https://github.com/tfranzel/drf-spectacular/issues/923>`_
- mitigate many=True with default array value `#936 <https://github.com/tfranzel/drf-spectacular/issues/936>`_
- fix dj-rest-auth>=3.0.0 breaking changes `#937 <https://github.com/tfranzel/drf-spectacular/issues/937>`_
- Update plumbing.py
- add swagger UI template blocks for customization [Jan Lis]
- Add support for drf ReturnList and ReturnDict hint [zengqiu]
- add example/test for DynamicFieldsModelSerializer `#375 <https://github.com/tfranzel/drf-spectacular/issues/375>`_ `#912 <https://github.com/tfranzel/drf-spectacular/issues/912>`_
- adapt test schema for dj-rest-auth 2.2.6
- clarify docs for postproc hook mechanics `#908 <https://github.com/tfranzel/drf-spectacular/issues/908>`_
- Add test for custom serializer field pagination `#904 <https://github.com/tfranzel/drf-spectacular/issues/904>`_
- fix: let use a default value for foreignkey model field [Frederic de Zorzi]

Breaking changes / important additions:

- A lot of bug fixes and a few feature additions.
- We now render a descriptive ``Enum`` key/value list into the description by default. Opt-out with new setting ``ENUM_GENERATE_CHOICE_DESCRIPTION``.
- Beware that we now extract more docstrings. Check your schema diff on update whether you are now leaking unintended information.
- The ``whitelist`` mechanics changed slightly on what is considered default behavior.
- Fix a breaking change in ``dj-rest-auth>=3.0.0``
- It should not be possible to run the tests without installing system libraries like GDAL for the contrib tests

0.25.1 (2022-12-16)
-------------------

- Fix warning source line performance regression `#889 <https://github.com/tfranzel/drf-spectacular/issues/889>`_ `#897 <https://github.com/tfranzel/drf-spectacular/issues/897>`_
- improve warning for transient @api_view objects `#889 <https://github.com/tfranzel/drf-spectacular/issues/889>`_
- adapt package arg due to setuptools deprecation `#786 <https://github.com/tfranzel/drf-spectacular/issues/786>`_
- utilize queryset for SlugRelatedField `#897 <https://github.com/tfranzel/drf-spectacular/issues/897>`_

Breaking changes / important additions:

- Bugfix release that addresses a performance regression in ``SpectacularApiView`` and an oversight in the now stricter handling of ``SlugRelatedField``

0.25.0 (2022-12-13)
-------------------

- Fix missing description for ManyRelatedField and tested for SlugField (`#895 <https://github.com/tfranzel/drf-spectacular/issues/895>`_) [StopMotionCuber]
- Simplify hashable_values `#833 <https://github.com/tfranzel/drf-spectacular/issues/833>`_
- Add custom settings to CLI (view parity) `#892 <https://github.com/tfranzel/drf-spectacular/issues/892>`_
- fix function misnomer `#891 <https://github.com/tfranzel/drf-spectacular/issues/891>`_
- improve trace messages / warnings & add color `#866 <https://github.com/tfranzel/drf-spectacular/issues/866>`_
- Treat SlugRelatedField analog to PrimaryKeyRelatedField `#854 <https://github.com/tfranzel/drf-spectacular/issues/854>`_
- Include filename in call to _get_sidecar_url [Justin Spencer]
- add django-parler blueprint `#887 <https://github.com/tfranzel/drf-spectacular/issues/887>`_
- add a view to handle SwaggerUI oauth callbacks (`#882 <https://github.com/tfranzel/drf-spectacular/issues/882>`_) [Finn-Thorben Sell]
- improve documentation
- Introduce setting DEFAULT_QUERY_MANAGER to allow other managers for querset retrieval
- fix flake8 6.0.0 breaking change
- fix example list detection (symmetry with schema) `#872 <https://github.com/tfranzel/drf-spectacular/issues/872>`_
- Use direct view methods for getting serializer instances [Numerlor]
- name overrides for rest_framework_dataclasses `#839 <https://github.com/tfranzel/drf-spectacular/issues/839>`_
- decouple TypedDict class from Py version `#861 <https://github.com/tfranzel/drf-spectacular/issues/861>`_ `#654 <https://github.com/tfranzel/drf-spectacular/issues/654>`_
- bugfix djangorestframework_camel_case `#861 <https://github.com/tfranzel/drf-spectacular/issues/861>`_
- bugfix djangorestframework_camel_case nested object handling `#861 <https://github.com/tfranzel/drf-spectacular/issues/861>`_
- Utils: Replace ``List[]`` with ``Sequence[]``, because of Mypy note 'List is invariant. Consider using Sequence instead.' [Hans Aarne Liblik]
- Fixed minor typos [Conrad]
- Removing blank and null keys when generating the overridden choices hash to match the hash generation logic in the enum post processor hook [Trent Holliday]
- fix test fixture overlap `#826 <https://github.com/tfranzel/drf-spectacular/issues/826>`_
- specify min patch release for DRF (fixes `#812 <https://github.com/tfranzel/drf-spectacular/issues/812>`_)
- Preserve context in ``get_list_serializer``. [Brady Dean]
- Allow field extensions to return None from map_serializer_field [Andrew Backer]

Breaking changes / important additions:

- Officially set the lower bound for DRF version to ``3.10.3``
- Refactored the CLI warning system for better code navigation / orientation, GUI support and color!
- Some minor mechanics changes, several overall improvements, feature additions, and a few bugfixes.

0.24.2 (2022-09-26)
-------------------

- robustify extension class loading `#821 <https://github.com/tfranzel/drf-spectacular/issues/821>`_
- fix regression due to GIS import for django-filter `#821 <https://github.com/tfranzel/drf-spectacular/issues/821>`_

Breaking changes / important additions:

- Hotfix release to mitigate optional GDAL import errors for django-filter.

0.24.1 (2022-09-23)
-------------------

- bugfix GeometryFilter for GIS and django-filter `#814 <https://github.com/tfranzel/drf-spectacular/issues/814>`_
- NullBooleanField comment and add 3.14.0 to test suite `#818 <https://github.com/tfranzel/drf-spectacular/issues/818>`_
- fix:  `#816 <https://github.com/tfranzel/drf-spectacular/issues/816>`_ NullBooleanField does not exist in DRF >= 3.14.0 [Laurent Tramoy]
- fix GIS source lookup with hops `#813 <https://github.com/tfranzel/drf-spectacular/issues/813>`_
- Add blueprint for Stoplight Elements docs UI [Alex Burgel]
- fix OpenApiParameter enum and pattern for many=True `#808 <https://github.com/tfranzel/drf-spectacular/issues/808>`_

Breaking changes / important additions:

- Hotfix release to mitigate removal of ``NullBooleanField`` in DRF 3.14.0
- Small fixes to OpenApiParameter and ``django-filter``

0.24.0 (2022-09-14)
-------------------

- fix yaml serialization error on Django SafeString `#802 <https://github.com/tfranzel/drf-spectacular/issues/802>`_
- mitigate DRF bug in ObtainAuthToken < 3.12.0 `#796 <https://github.com/tfranzel/drf-spectacular/issues/796>`_
- add FAQ entry for django-csp errors `#173 <https://github.com/tfranzel/drf-spectacular/issues/173>`_ `#797 <https://github.com/tfranzel/drf-spectacular/issues/797>`_
- bugfix TokenMatchesOASRequirements `#469 <https://github.com/tfranzel/drf-spectacular/issues/469>`_ and JWTCookieAuthentication `#626 <https://github.com/tfranzel/drf-spectacular/issues/626>`_
- add custom redoc settings option
- fix error with PrimaryKeyRelatedField on non-ModelSerializer `#353 <https://github.com/tfranzel/drf-spectacular/issues/353>`_
- provide context to serializer for @extend_schema use-cases `#699 <https://github.com/tfranzel/drf-spectacular/issues/699>`_
- add example value hint to doc `#788 <https://github.com/tfranzel/drf-spectacular/issues/788>`_
- fix packages= so top_level.txt is correct [anthony sottile]
- Adding documentation for the OpenApiParameter 'many' argument [Paul Wayper]
- Extend OpenApiSerializerExtension interface. `#392 <https://github.com/tfranzel/drf-spectacular/issues/392>`_ `#705 <https://github.com/tfranzel/drf-spectacular/issues/705>`_
- Include context with request when instantiating serializers [Mike Hansen]

Breaking changes / important additions:

- Some minor gaps closed in the extension interface and serializer context initialization. It is a y-stream release,
  because there remains a small chance of change for users that sport non-standard customizations.

0.23.1 (2022-07-26)
-------------------

- improve CAMELIZE_NAMES doc `#774 <https://github.com/tfranzel/drf-spectacular/issues/774>`_
- move import into build_geo_schema function [bidaya0]

Breaking changes / important additions:

- Hotfix release to mitigate unwanted import of optional GIS features that depend on GDAL. GDAL is **not** a new requirement.

0.23.0 (2022-07-25)
-------------------

- fix infinite recursion when accessing missing attributes in generator stats [Oleg Hoefling]
- fix list pagination when examples are provided [topher235]
- accept integer status codes in OpenApiExample [Nicholas Guriev]
- Missing ":" in example documentation [Josué Millán Zamora]
- Flip direction for callbacks serializers [Justas]
- grammar fix [Kojo Idrissa]
- fix sidecar for alternate staticfile storages `#718 <https://github.com/tfranzel/drf-spectacular/issues/718>`_
- add support for ``rest_framework_gis``
- add mechanism to handle custom ListSerializers with extensions
- Update based on review [johnthagen]
- Hyphenate in-memory [johnthagen]
- Add FAQ entry for how to serve in-memory generated files [johnthagen]
- add pattern to OpenApiParameter `#738 <https://github.com/tfranzel/drf-spectacular/issues/738>`_
- Add test that extend_schema_field on django-filter is not modified [Take Weiland]
- Do not forcefully overwrite enum setting on custom django-filter schema [Take Weiland]
- django-filter: Enable type extraction fallback for MultipleChoiceFilter as well [Take Weiland]
- Add examples camelization note to settings.py [Zac Miller]
- fix codecov badge url issue on github `#713 <https://github.com/tfranzel/drf-spectacular/issues/713>`_

Breaking changes / important additions:

- A whole bunch of smaller bug fixes.
- OpenAPI Callbacks should now be production ready
- Introduction of ``rest_framework_gis`` support. This might impact APIs that are using GIS so this is a y-stream release.

0.22.1 (2022-04-25)
-------------------

- Update customization.rst [Lane Zhang]
- Remove invalid example in drf-yasg migration documentation. [Nick Pope]
- Avoid using default role in documentation. [Nick Pope]
- Small documentation fixes. [Nick Pope]
- improve parameter many handling and warnings `#703 <https://github.com/tfranzel/drf-spectacular/issues/703>`_
- bugfix unconsidered warnings/errors for return code `#706 <https://github.com/tfranzel/drf-spectacular/issues/706>`_ `#702 <https://github.com/tfranzel/drf-spectacular/issues/702>`_
- Include a list of applications urls as a parameter for SERVE_URLCONF  `#709 <https://github.com/tfranzel/drf-spectacular/issues/709>`_ [anoirak]
- bugfix/improve analyze_named_regex_pattern(path) `#697 <https://github.com/tfranzel/drf-spectacular/issues/697>`_ [Jon Iturmendi]
- django-filter: added type extraction fallback for ChoiceFields `#690 <https://github.com/tfranzel/drf-spectacular/issues/690>`_
- fix test, more precise naming, also wrap validation `#693 <https://github.com/tfranzel/drf-spectacular/issues/693>`_
- bugfix PolymorphicProxySerializer many handling and add manual mode `#692 <https://github.com/tfranzel/drf-spectacular/issues/692>`_
- Use Django management CommandError to eliminate the traceback on error [Brandon W Maister]
- add ``swagger_fake_view`` FAQ entry `#321 <https://github.com/tfranzel/drf-spectacular/issues/321>`_
- Fix `#688 <https://github.com/tfranzel/drf-spectacular/issues/688>`_ - avoid a TypeError when ChoiceFilter choices are a callable [Glenn Matthews]
- map explicit float hints/decoration to double `#687 <https://github.com/tfranzel/drf-spectacular/issues/687>`_ `#674 <https://github.com/tfranzel/drf-spectacular/issues/674>`_

Breaking changes / important additions:

- Small release consisting of minor bug fixes, improved ``PolymorphicProxySerializer``, cleaned up documentation, and some improvements to **django-filter**

0.22.0 (2022-03-21)
-------------------

- Added ``detype_patterns()`` with ``@cache``. [Nick Pope]
- add "externalDocs" to operation via extend_schema `#681 <https://github.com/tfranzel/drf-spectacular/issues/681>`_
- warn on invalid components names `#685 <https://github.com/tfranzel/drf-spectacular/issues/685>`_
- wrap examples in list/pagination when serializer is many=True `#641 <https://github.com/tfranzel/drf-spectacular/issues/641>`_ `#640 <https://github.com/tfranzel/drf-spectacular/issues/640>`_ `#595 <https://github.com/tfranzel/drf-spectacular/issues/595>`_
- python's and django's float is really "double precision" `#674 <https://github.com/tfranzel/drf-spectacular/issues/674>`_
- Support negative numbers in pattern regex for coerced decimal fields [Mike Hansen]
- add OpenAPI callback operations `#665 <https://github.com/tfranzel/drf-spectacular/issues/665>`_
- Keep the urlpatterns in the apiview and pass it to the generator [Jorge Cardona]
- django-filter: raise priority of explicitly given filter method type hints `#660 <https://github.com/tfranzel/drf-spectacular/issues/660>`_
- also allow @extend_schema_field on django-filter filter method `#660 <https://github.com/tfranzel/drf-spectacular/issues/660>`_
- accommodate pyright limitations `#657 <https://github.com/tfranzel/drf-spectacular/issues/657>`_
- fix doc extraction for built-in types `#654 <https://github.com/tfranzel/drf-spectacular/issues/654>`_
- use get_doc for description [Josh Ferge]
- add more information to resolved TypedDicts [Josh Ferge]
- fix url escaping bug introduced in `#556 <https://github.com/tfranzel/drf-spectacular/issues/556>`_ (`#650 <https://github.com/tfranzel/drf-spectacular/issues/650>`_)
- pass through version from UI to schema endpoint `#650 <https://github.com/tfranzel/drf-spectacular/issues/650>`_
- factor out schema_url generation `#650 <https://github.com/tfranzel/drf-spectacular/issues/650>`_
- relax AcceptHeaderVersioning constraint for modification `#650 <https://github.com/tfranzel/drf-spectacular/issues/650>`_
- Enable the use of lists in extend_schema_view() [François Travais]

Breaking changes / important additions:

- This is a y-stream release with a lot of bugfixes, some new features and potentially small schema changes (if affected features are used).
- Examples are now wrapped in pagination/lists when endpoint/serializer is ``many=True``
- django-filter had some internal restructuring and thus overrides are now always honored.
- added callback functionality (EXPERIMENTAL and subject to change due to pending issue)
- Many thanks to all the contributors!

0.21.2 (2022-02-01)
-------------------

- Add support for djangorestframework-dataclasses [Oxan van Leeuwen]
- add version to schema for AcceptHeaderVersioning `#637 <https://github.com/tfranzel/drf-spectacular/issues/637>`_
- FAQ for @api_view `#635 <https://github.com/tfranzel/drf-spectacular/issues/635>`_
- add extensions for dj_rest_auth's JWTCookieAuthentication `#626 <https://github.com/tfranzel/drf-spectacular/issues/626>`_

Breaking changes / important additions:

- Some minor bugfixes and feature additions. Schemas using AcceptHeaderVersioning contain a small change.

0.21.1 (2021-12-20)
-------------------

- add root level extension setting `#619 <https://github.com/tfranzel/drf-spectacular/issues/619>`_
- ease schema browser handling with "Content-Disposition" `#607 <https://github.com/tfranzel/drf-spectacular/issues/607>`_
- custom settings per SpectacularAPIView instance `#365 <https://github.com/tfranzel/drf-spectacular/issues/365>`_
- Support new X | Y union syntax in Python 3.10 (PEP 604) [Marti Raudsepp]
- upstream release updates, compat test fix for jwt, consistency fix
- add blueprint for django-auth-adfs [1110sillabo]
- use is_list_serializer instead of isinstance() [Roman Sichnyi]
- Fix schema generation for RecursiveField(many=True) [Roman Sichnyi]
- enable clearing auth methods with empty list `#99 <https://github.com/tfranzel/drf-spectacular/issues/99>`_
- Fix typos in the code example [Marcin Kurczewski]

Breaking changes / important additions:

- Some minor bugfixes and small feature additions. No large schema changes are expected

0.21.0 (2021-11-10)
-------------------

- add renderer & parser whitelist setting `#598 <https://github.com/tfranzel/drf-spectacular/issues/598>`_
- catch attr exception for invalid SerializerMethodField `#592 <https://github.com/tfranzel/drf-spectacular/issues/592>`_
- add regression test for catch-all status codes `#573 <https://github.com/tfranzel/drf-spectacular/issues/573>`_
- bugfix OpenApiResponse without description argument `#591 <https://github.com/tfranzel/drf-spectacular/issues/591>`_
- introduce direction literal / import consolidation `#582 <https://github.com/tfranzel/drf-spectacular/issues/582>`_
- mitigate CORS issues for external requests in Swagger UI `#588 <https://github.com/tfranzel/drf-spectacular/issues/588>`_
- Swagger UI authorized schema retrieval `#342 <https://github.com/tfranzel/drf-spectacular/issues/342>`_ `#458 <https://github.com/tfranzel/drf-spectacular/issues/458>`_
- remove cyclic import warning as fixes haves mitigated the issue. `#581 <https://github.com/tfranzel/drf-spectacular/issues/581>`_
- bugfix: anchor parameter patterns with ^$
- bugfix isolation of derivatives for @extend_schema_serializer/@extend_schema_field `#585 <https://github.com/tfranzel/drf-spectacular/issues/585>`_
- add support for djangorestframework-recursive `#586 <https://github.com/tfranzel/drf-spectacular/issues/586>`_
- Add blueprint for drf-extra-fields Base64FileField [johnthagen]
- Add note about extensions registering themselves [johnthagen]
- Document alternative to drf-yasg swagger_schema_field [johnthagen]
- allow to bypass list detection for filter discovery `#407 <https://github.com/tfranzel/drf-spectacular/issues/407>`_
- add blueprint (closes `#448 <https://github.com/tfranzel/drf-spectacular/issues/448>`_), fix test misnomer
- non-blank string enforcement for parameters `#282 <https://github.com/tfranzel/drf-spectacular/issues/282>`_
- add setting ENFORCE_NON_BLANK_FIELDS to enable blank checks `#186 <https://github.com/tfranzel/drf-spectacular/issues/186>`_

Breaking changes / important additions:

- Fixed two more decorator isolation issues.
- Added Swagger UI plugin to handle reloading the schema on authentication changes (``'SERVE_PUBLIC': False``).
- Added ``minLength`` where a blank value is not allowed. Apart the dedicated setting, it is implicitly enabled by ``COMPONENT_SPLIT_REQUEST``.
- Several other small fixes and additional settings for corner cases. This is mainly a y-steam release due to the potential impact
  on the Swagger UI and ``minLength`` changes.

0.20.2 (2021-10-15)
-------------------

- add setting for manual path prefix: SCHEMA_PATH_PREFIX_INSERT `#567 <https://github.com/tfranzel/drf-spectacular/issues/567>`_
- improve type hint for @extend_schema_field `#569 <https://github.com/tfranzel/drf-spectacular/issues/569>`_
- bugfix COMPONENT_SPLIT_REQUEST for empty req/resp serializers `#572 <https://github.com/tfranzel/drf-spectacular/issues/572>`_
- Make it cleared that ENUM_NAME_OVERRIDES is a key within SPECTACULAR_SETTINGS [johnthagen]
- Improve formatting in customization docs [johnthagen]
- bugfix @extend_schema_view on @api_view `#554 <https://github.com/tfranzel/drf-spectacular/issues/554>`_
- bugfix isolation for @extend_schema/@extend_schema_view reorg `#554 <https://github.com/tfranzel/drf-spectacular/issues/554>`_
- Fix inheritance bugs with @extend_schema_view(). [Nick Pope]
- Allow methods in @extend_schema to be case insensitive. [Nick Pope]
- Added a documentation blueprint for RapiDoc. [Nick Pope]
- Tidy templates for documentation views. [Nick Pope]
- Use latest version for CDN packages. [Nick Pope]

Breaking changes / important additions:

- Mainly a bugfix release that solves several longstanding issues with ``@extend_schema_view``/``@extend_schema``
  annotation isolation. There should be no more side effects from arbitrarily mixing and matching the decorators.
- Improved handling of completely empty serializers with COMPONENT_SPLIT_REQUEST.

0.20.1 (2021-10-03)
-------------------

- move swagger CDN to jsdelivr (unpkg has been flaky)
- bugfix wrong DIST setting in Redoc `#546 <https://github.com/tfranzel/drf-spectacular/issues/546>`_
- Allow paginated_name customization [Georgy Komarov]

Breaking changes / important additions:

- Hotfix release due to regression in the Redoc template

0.20.0 (2021-10-01)
-------------------

- Add support for specification extensions. [Nick Pope]
- add example injection for (discovered) parameters `#414 <https://github.com/tfranzel/drf-spectacular/issues/414>`_
- Fix crash with read-only polymorphic sub-serializer. [Nick Pope]
- Add arbitrarily deep ListSerializer nesting `#539 <https://github.com/tfranzel/drf-spectacular/issues/539>`_
- tighten serializer assumptions `#539 <https://github.com/tfranzel/drf-spectacular/issues/539>`_
- fix whitespace stripping on methods
- Rename ``AutoSchema._map_field_validators()`` → ``.insert_field_validators()``. [Nick Pope]
- Rename ``AutoSchema._map_min_max()`` → ``.insert_min_max()``. [Nick Pope]
- Fix detection of int64 from min/max values. [Nick Pope]
- Fix zero handling in _map_min_max(). [Nick Pope]
- Add support for introspection of nested validators. [Nick Pope]
- Fix invalid schemas caused by validator introspection. [Nick Pope]
- Overhaul validator logic. [Nick Pope]
- support multiple headers in OpenApiAuthenticationExtension `#537 <https://github.com/tfranzel/drf-spectacular/issues/537>`_
- docs: Missing end quote for INSTALLED_APPS [Prayash Mohapatra]
- update doc `#530 <https://github.com/tfranzel/drf-spectacular/issues/530>`_
- introducing the spectacular sidecar
- fallback improvements to typing system with typing_extensions

Breaking changes / important additions:

- Added vendor specification extensions
- Completely overhauled validator logic and bugfixes
- Offline UI assets with optional *drf-spectacular-sidecar* package
- several internal logic improvements and stricter assumptions

0.19.0 (2021-09-21)
-------------------

- fix/cleanup suffixed path variable coercion `#516 <https://github.com/tfranzel/drf-spectacular/issues/516>`_
- remove superseded Request mock from oauth_toolkit
- be gracious on Enums that are not recognized by DRF `#500 <https://github.com/tfranzel/drf-spectacular/issues/500>`_
- remove non-required empty descriptions
- added test case for lookup_field `#524 <https://github.com/tfranzel/drf-spectacular/issues/524>`_
- Fix grammatical typo [johnthagen]
- remove mapping for re.Pattern (no 3.6 and mypy issues) `#526 <https://github.com/tfranzel/drf-spectacular/issues/526>`_
- Add missing types defined in specification. [Nick Pope]
- Add type mappings for IP4, IP6, TIME & DURATION. [Nick Pope]
- add support for custom converters and converter override `#502 <https://github.com/tfranzel/drf-spectacular/issues/502>`_
- cache static loading function calls
- prevent settings loading in types, lazy load in plumbing instead
- lazy settings loading in drainage
- Improve guide for migration from drf-yasg. [Nick Pope]
- handle default value for SerializerMethodField `#422 <https://github.com/tfranzel/drf-spectacular/issues/422>`_
- consolidate bearer scheme generation & bugfix `#515 <https://github.com/tfranzel/drf-spectacular/issues/515>`_
- prevent uncaught exception on modified django-filter `#519 <https://github.com/tfranzel/drf-spectacular/issues/519>`_
- add decoupled model docstrings `#522 <https://github.com/tfranzel/drf-spectacular/issues/522>`_
- Fix warnings raised during testing. [Nick Pope]
- add name override to @extend_schema_serializer `#517 <https://github.com/tfranzel/drf-spectacular/issues/517>`_
- Fix deprecation warning about default_app_config from Django 3.2+ [Janne Rönkkö]
- Remove obsolete value from IMPORT_STRINGS. [Nick Pope]
- Add extension for TokenVerifySerializer. [Nick Pope]
- Use SESSION_COOKIE_NAME in SessionScheme. [Nick Pope]
- add regex path parameter extraction for explicit cases `#510 <https://github.com/tfranzel/drf-spectacular/issues/510>`_
- honor lookup_url_kwarg name customization `#509 <https://github.com/tfranzel/drf-spectacular/issues/509>`_
- add contrib compat tests for drf-nested-routers
- improve path coersion model resolution
- add test_fields API response test `#501 <https://github.com/tfranzel/drf-spectacular/issues/501>`_
- Handle 'lookup_field' containing relationships for path parameters [Luke Plant]
- add BinaryField case to tests `#506 <https://github.com/tfranzel/drf-spectacular/issues/506>`_
- fix: BinaryField's schema type should be string `#505 <https://github.com/tfranzel/drf-spectacular/issues/505>`_ (`#506 <https://github.com/tfranzel/drf-spectacular/issues/506>`_) [jtamm-red]
- bugfix incomplete regex stripping for literal dots `#507 <https://github.com/tfranzel/drf-spectacular/issues/507>`_
- Fix tests [Jameel Al-Aziz]
- Fix type hint support for functools cached_property wrapped funcs [Jameel Al-Aziz]
- Extend enum type hint support to more Enum subclasses [Jameel Al-Aziz]

Breaking changes / important additions:

- Severely improved path parameter detection for Django-style parameters, RE parameters, and custom converters
- Significantly more defensive settings loading for safer project imports (less prone to import loops)
- Improved type hint support for ``Enum`` and other native types
- Explicit support for *drf-nested-routers*
- A lot more small improvements

0.18.2 (2021-09-04)
-------------------

- fix default value handling for custom ModelField `#422 <https://github.com/tfranzel/drf-spectacular/issues/422>`_
- fill html title with title from settings `#491 <https://github.com/tfranzel/drf-spectacular/issues/491>`_
- add Enum support in type hints `#492 <https://github.com/tfranzel/drf-spectacular/issues/492>`_
- Move system check registration to AppConfig [Jameel Al-Aziz]

Breaking changes / important additions:

- Primarily ironing out another issue with the Django check and some minor improvements

0.18.1 (2021-08-31)
-------------------

- Improved docs regarding how ENUM_NAME_OVERRIDES works [Luke Plant]
- bugfix raw schema handling for @extend_schema_field on SerializerMethodField method 481
- load common SwaggerUI dep SwaggerUIStandalonePreset `#483 <https://github.com/tfranzel/drf-spectacular/issues/483>`_
- allow versioning of SpectacularAPIView via query `#483 <https://github.com/tfranzel/drf-spectacular/issues/483>`_
- update swagger UI
- move checks to "--deploy" section, bugfix public=True `#487 <https://github.com/tfranzel/drf-spectacular/issues/487>`_

Breaking changes / important additions:

- This is a hotfix release as the newly introduced Django check was executing the wrong code path.
- Check also moved into the ``--deploy`` section to prevent double execution. This can be disabled with ``ENABLE_DJANGO_DEPLOY_CHECK``
- Facitities added to utilize SwaggerUI Topbar for versioning.

0.18.0 (2021-08-25)
-------------------

- prevent exception and warn when ReadOnlyField is used with non-ModelSerializer `#432 <https://github.com/tfranzel/drf-spectacular/issues/432>`_
- allow raw JS in Swagger settings `#457 <https://github.com/tfranzel/drf-spectacular/issues/457>`_
- add support for check framework `#477 <https://github.com/tfranzel/drf-spectacular/issues/477>`_
- improve common FAQ @action question `#399 <https://github.com/tfranzel/drf-spectacular/issues/399>`_
- update @extend_schema doc `#476 <https://github.com/tfranzel/drf-spectacular/issues/476>`_
- adapt to changes in iMerica/dj-rest-auth 2.1.10 (ResendEmailVerification)
- add raw schema to @extend_schema(request={MIME: RAW}) `#476 <https://github.com/tfranzel/drf-spectacular/issues/476>`_
- bugfix test case for 3.6 `#474 <https://github.com/tfranzel/drf-spectacular/issues/474>`_
- bugfix header underscore handling for simplejwt `#474 <https://github.com/tfranzel/drf-spectacular/issues/474>`_
- properly parse TokenMatchesOASRequirements (oauth toolkit) `#469 <https://github.com/tfranzel/drf-spectacular/issues/469>`_
- add whitelist setting to manage auth method exposure `#326 <https://github.com/tfranzel/drf-spectacular/issues/326>`_ `#471 <https://github.com/tfranzel/drf-spectacular/issues/471>`_
- Update set_password instead of list [Greg Campion]
- Update documentation to illustrate how to override a specific method [Greg Campion]

Breaking changes / important additions:

- This is a y-stream release because we added `Django checks <https://docs.djangoproject.com/en/3.2/topics/checks/>`_
  which might emit warnings and subsequently break CI. This can be easily suppressed with Django's ``SILENCED_SYSTEM_CHECKS``.
- Several small fixes and features that should not have a big impact.

0.17.3 (2021-07-26)
-------------------

- port custom "Bearer" bugfix/workaround to simplejwt `#467 <https://github.com/tfranzel/drf-spectacular/issues/467>`_
- add setting for listing/paginating/filtering on non-2XX `#402 <https://github.com/tfranzel/drf-spectacular/issues/402>`_ `#277 <https://github.com/tfranzel/drf-spectacular/issues/277>`_
- fix Typo [Eunsub LEE]
- nit typofix [adamsteele-city]
- Add a few return type annotations [Nikhil Benesch]
- add django-filter queryset annotation and ``extend_schema_field`` support
- account for functools.partial wrapped type hints `#451 <https://github.com/tfranzel/drf-spectacular/issues/451>`_
- Update swagger_ui.js [Jordan Facibene]
- Update customization.rst to fix example typo [Atsuo Shiraki]
- update swagger-ui version
- add oauth2 config for swagger ui `#438 <https://github.com/tfranzel/drf-spectacular/issues/438>`_

Breaking changes / important additions:

- Just a few bugfixes and some small features with minimal impact on existing schema

0.17.2 (2021-06-15)
-------------------

- prevent endless loop in extensions when augmenting schema `#426 <https://github.com/tfranzel/drf-spectacular/issues/426>`_
- bugfix secondary import cycle (generics.APIView) `#430 <https://github.com/tfranzel/drf-spectacular/issues/430>`_
- fix: avoid circular import of/via rest_framework's APIView [Daniel Hahler]

Breaking changes / important additions:

- Hotfix release that addresses a carelessly added import in 0.17.1. In certain use-cases,
  this may have led to an import cycle inside DRF.

0.17.1 (2021-06-12)
-------------------

- bugfix 201 response for (List)CreateAPIVIew `#428 <https://github.com/tfranzel/drf-spectacular/issues/428>`_
- support paginated ListSerializer with field child `#413 <https://github.com/tfranzel/drf-spectacular/issues/413>`_
- fix django-filter.BooleanFilter subclass issue `#317 <https://github.com/tfranzel/drf-spectacular/issues/317>`_
- serializer field deprecation `#415 <https://github.com/tfranzel/drf-spectacular/issues/415>`_
- improve extension documentation `#426 <https://github.com/tfranzel/drf-spectacular/issues/426>`_
- improve type hints and fix mypy issues on tests.
- add missing usage case to type hints `#418 <https://github.com/tfranzel/drf-spectacular/issues/418>`_
- Typo(?) README fix [Jan Jurec]

Breaking changes / important additions:

- This release is mainly for fixing incomplete type hints which mypy will potentially complain about.
- A few small fixes that should either have no or a very small impact in schemas.

0.17.0 (2021-06-01)
-------------------

- improve type hint detection for Iterable and NamedTuple `#404 <https://github.com/tfranzel/drf-spectacular/issues/404>`_
- bugfix ReadOnlyField when used as ListSerlializer child `#404 <https://github.com/tfranzel/drf-spectacular/issues/404>`_
- improve component discard logic `#395 <https://github.com/tfranzel/drf-spectacular/issues/395>`_
- allow disabling operation sorting for sorting in PREPROCESSIN_HOOKS `#410 <https://github.com/tfranzel/drf-spectacular/issues/410>`_
- add regression test for `#407 <https://github.com/tfranzel/drf-spectacular/issues/407>`_
- fix error on read-only serializer [Matthieu Treussart]
- invert component exclusion logic (OpenApiSerializerExtension) `#351 <https://github.com/tfranzel/drf-spectacular/issues/351>`_ `#391 <https://github.com/tfranzel/drf-spectacular/issues/391>`_
- add many=True support to PolymorphicProxySerializer `#382 <https://github.com/tfranzel/drf-spectacular/issues/382>`_
- improve documentation, remove py2 wheel tag, mark as mypy-enabled
- bugfix YAML serialization errors that are ok with JSON `#388 <https://github.com/tfranzel/drf-spectacular/issues/388>`_
- bugfix missing auth extension for JWTTokenUserAuthentication `#387 <https://github.com/tfranzel/drf-spectacular/issues/387>`_
- Rename MethodSerializerField -> SerializerMethodField in README [Christoph Krybus]

Breaking changes / important additions:

- Quite a few small improvements. The biggest change is the inversion of the component discard logic.
  This should have no negative impact, but to be on the safe side we'll opt for a y-stream release.
- The package is now marked as being typed, which should get picked up natively by mypy

0.16.0 (2021-05-10)
-------------------

- add redoc dist setting
- bugfix mock request asymmetry `#370 <https://github.com/tfranzel/drf-spectacular/issues/370>`_ `#250 <https://github.com/tfranzel/drf-spectacular/issues/250>`_
- refactor urlpattern simplification `#373 <https://github.com/tfranzel/drf-spectacular/issues/373>`_ `#168 <https://github.com/tfranzel/drf-spectacular/issues/168>`_
- include relation PKs into SCHEMA_COERCE_PATH_PK handling `#251 <https://github.com/tfranzel/drf-spectacular/issues/251>`_
- allow PolymorphicProxySerializer to be simple 'oneOf'
- bugfix incorrect PolymorphicProxySerializer warning on extend_schema_field `#263 <https://github.com/tfranzel/drf-spectacular/issues/263>`_
- add break-out option for SerializerFieldExtension
- Modify urls for nested routers [Matthias Erll]

Breaking changes / important additions:

- Revamped handling of mocked requests. Now ``GET_MOCK_REQUEST`` is always called, not just for offline schema generation.
  In case there is a real request available, we carry over headers and authentication. If you use your own implementation,
  you may want to inspect the new default implementation.
- NamespaceVersioning: switched path variable substitution from regex to custom state machine due to parethesis counting issue.
- Improved implicit support for `drf-nested-routers <https://github.com/alanjds/drf-nested-routers>`_
- Added some convenience options for plain ``oneOf`` to PolymorphicProxySerializer
- This release should have minimal impact on the generated schema. We opt for a y-stream release due to potentially breaking changes when a user-provided ``GET_MOCK_REQUEST`` is used.

0.15.1 (2021-04-08)
-------------------

- bugfix prefix estimation with RE special char literals in path `#358 <https://github.com/tfranzel/drf-spectacular/issues/358>`_

Breaking changes / important additions:

- minor release to fix newly introduced default prefix estimation.

0.15.0 (2021-04-03)
-------------------

- fix boundaries for decimals coerced to strings `#335 <https://github.com/tfranzel/drf-spectacular/issues/335>`_
- improve util type hints
- add convenience response wrapper OpenApiResponse `#345 <https://github.com/tfranzel/drf-spectacular/issues/345>`_ `#272 <https://github.com/tfranzel/drf-spectacular/issues/272>`_ `#116 <https://github.com/tfranzel/drf-spectacular/issues/116>`_
- adapt for dj-rest-auth upstream changes in iMerica/dj-rest-auth#227
- Fixed traversing of 'Optional' type annotations [Luke Plant]
- prevent pagination on error responses. `#277 <https://github.com/tfranzel/drf-spectacular/issues/277>`_
- fix SCHEMA_PATH_PREFIX_TRIM ^/ pitfall & remove unused old URL mounting
- slightly improve `#332 <https://github.com/tfranzel/drf-spectacular/issues/332>`_ for django-filter range filters
- introduce non-redundant title field. `#191 <https://github.com/tfranzel/drf-spectacular/issues/191>`_ `#286 <https://github.com/tfranzel/drf-spectacular/issues/286>`_
- improve schema version string handling including variations `#303 <https://github.com/tfranzel/drf-spectacular/issues/303>`_
- bugfix ENUM_NAME_OVERRIDES for categorized choices `#339 <https://github.com/tfranzel/drf-spectacular/issues/339>`_
- improve SCHEMA_PATH_PREFIX handling, add auto-detect default, introduce prefix trimming `#336 <https://github.com/tfranzel/drf-spectacular/issues/336>`_
- add support for all django-filters RangeFilter [Jules Waldhart]
- Added default value for missing attribute [Matthias Erll]
- Fix map_renderers where format is None [Matthias Erll]

Breaking changes / important additions:

- explicitly set responses via ``@extend_schema`` will not get paginated/listed anymore for non ``2XX`` status codes.
- New default ``None`` for ``SCHEMA_PATH_PREFIX`` will attempt to determine a reasonable prefix. Previous behavior is restored with ``''``
- Added ``OpenApiResponses`` to gain access to response object descriptions.

0.14.0 (2021-03-09)
-------------------

- Fixed bug with ``cached_property`` non-Model objects not being traversed [Luke Plant]
- Fixed issue `#314 <https://github.com/tfranzel/drf-spectacular/issues/314>`_ - include information about view/serializer in warnings. [Luke Plant]
- bugfix forward/reverse model traversal `#323 <https://github.com/tfranzel/drf-spectacular/issues/323>`_
- fix nested serializer detection & smarter metadata extraction `#319 <https://github.com/tfranzel/drf-spectacular/issues/319>`_
- add drf-yasg compatibility feature 'swagger_fake_view' `#321 <https://github.com/tfranzel/drf-spectacular/issues/321>`_
- fix django-filter through model edge case & catch exceptions `#320 <https://github.com/tfranzel/drf-spectacular/issues/320>`_
- refactor/bugfix PATCH & Serializer(partial=True) behaviour.
- bugfix django-filter custom filter class resolution `#317 <https://github.com/tfranzel/drf-spectacular/issues/317>`_
- bugfix django-filter for Django 2.2 AutoField
- improved/restructured resolution priority in django-filter extension `#317 <https://github.com/tfranzel/drf-spectacular/issues/317>`_ `#234 <https://github.com/tfranzel/drf-spectacular/issues/234>`_
- handle Decimals for YAML `#316 <https://github.com/tfranzel/drf-spectacular/issues/316>`_
- remove deprecated django-filter backend solution
- update swagger-ui version
- bugfix [] case and lint `#312 <https://github.com/tfranzel/drf-spectacular/issues/312>`_
- discriminate None and typing.Any usage `#315 <https://github.com/tfranzel/drf-spectacular/issues/315>`_
- fix multi-step source relation field resolution, again. `#274 <https://github.com/tfranzel/drf-spectacular/issues/274>`_ `#296 <https://github.com/tfranzel/drf-spectacular/issues/296>`_
- Add any type for OpenApiTypes [André da Silva]
- improve Extension usage documentation `#307 <https://github.com/tfranzel/drf-spectacular/issues/307>`_
- restructure request body for extend_schema `#266 <https://github.com/tfranzel/drf-spectacular/issues/266>`_ `#279 <https://github.com/tfranzel/drf-spectacular/issues/279>`_
- bugfix multipart boundary showing up in Accept header
- bugfix: use get_parsers() and get_renderers() `#266 <https://github.com/tfranzel/drf-spectacular/issues/266>`_
- Fix for better support of PEP 563 compatible annotations. [Luke Plant]
- Add document authentication [gongul]
- Do not override query params [Fabricio Aguiar]
- New setting for enabling/disabling error/warn messages [Fabricio Aguiar]
- bugfix response headers without body `#297 <https://github.com/tfranzel/drf-spectacular/issues/297>`_
- issue `#296 <https://github.com/tfranzel/drf-spectacular/issues/296>`_ [Luis Saavedra]
- Fixes `#283 <https://github.com/tfranzel/drf-spectacular/issues/283>`_ -- implement response header parameters [Sergei Maertens]
- Added feature test for response headers [Sergei Maertens]
- robustify django-filter enum sorting `#295 <https://github.com/tfranzel/drf-spectacular/issues/295>`_

Breaking changes / important additions:

- *drf-spectacular*'s custom ``DjangoFilterBackend`` removed after previous deprecation. Just use the original class again.
- *django-filter* extension received a significant refactoring so your schema may have several changes, hopefully positive ones.
- Added response headers feature
- Extended ``@extend_schema(request=X)``, where ``X`` may now also be a ``Dict[content_type, serializer_etc]``
- Updated Swagger UI version
- Fixed several model traversal issues that may lead to PK changes in the schema
- Added *drf-yasg*'s ``swagger_fake_view``

0.13.2 (2021-02-11)
-------------------

- add setting for operation parameter sorting `#281 <https://github.com/tfranzel/drf-spectacular/issues/281>`_
- bugfix/generalize Union hint extraction `#284 <https://github.com/tfranzel/drf-spectacular/issues/284>`_
- bugfix functools.partial methods in django-filters `#290 <https://github.com/tfranzel/drf-spectacular/issues/290>`_
- bugfix django-filter method filter `#290 <https://github.com/tfranzel/drf-spectacular/issues/290>`_
- Check serialzer help_text field is passed to the query description [Jorge Rodríguez-Flores Esparza]
- QUERY Parameters from serializer ignore description in SwaggerUI [Jorge Rodríguez-Flores Esparza]
- README.rst encoding change [gongul]
- Add support for SCOPES_BACKEND_CLASS setting from django-oauth-toolkit [diesieben07]
- use source instead of field_name for model field detection `#274 <https://github.com/tfranzel/drf-spectacular/issues/274>`_ [diesieben07]
- bugfix parameter removal from custom AutoSchema `#212 <https://github.com/tfranzel/drf-spectacular/issues/212>`_
- add specification extension option to info section `#165 <https://github.com/tfranzel/drf-spectacular/issues/165>`_
- add default to OpenApiParameter `#271 <https://github.com/tfranzel/drf-spectacular/issues/271>`_
- show violating view for easier fixing `#278 <https://github.com/tfranzel/drf-spectacular/issues/278>`_
- fix readonly related fields generating incorrect schema `#274 <https://github.com/tfranzel/drf-spectacular/issues/274>`_ [diesieben07]
- bugfix save parameter removal `#212 <https://github.com/tfranzel/drf-spectacular/issues/212>`_

0.13.1 (2021-01-21)
-------------------

- bugfix/handle more django-filter cases `#263 <https://github.com/tfranzel/drf-spectacular/issues/263>`_
- bugfix missing meta on extend_serializer_field, raw schema, and breakout
- expose explode and style for OpenApiParameter `#267 <https://github.com/tfranzel/drf-spectacular/issues/267>`_
- Only generate mock request if there is no actual request [Matthias Erll]
- Update blueprints.rst [takizuka]
- bugfix enum substitution for enumed arrays (multiple choice)
- Update README.rst [Chad Ramos]
- Create new mock request on each operation [Matthias Erll]

0.13.0 (2021-01-13)
-------------------

- add setting for additionalProperties handling `#238 <https://github.com/tfranzel/drf-spectacular/issues/238>`_
- bugfix path param extraction for PrimaryKeyRelatedField `#258 <https://github.com/tfranzel/drf-spectacular/issues/258>`_
- use injected django-filter help_text `#234 <https://github.com/tfranzel/drf-spectacular/issues/234>`_
- robustify normalization of types `#257 <https://github.com/tfranzel/drf-spectacular/issues/257>`_
- bugfix PATCH split serializer disparity `#249 <https://github.com/tfranzel/drf-spectacular/issues/249>`_
- django-filter description bugfix `#234 <https://github.com/tfranzel/drf-spectacular/issues/234>`_
- bugfix unsupported http verbs `#244 <https://github.com/tfranzel/drf-spectacular/issues/244>`_
- bugfix assert on methods in django-filter `#252 <https://github.com/tfranzel/drf-spectacular/issues/252>`_ `#234 <https://github.com/tfranzel/drf-spectacular/issues/234>`_ `#241 <https://github.com/tfranzel/drf-spectacular/issues/241>`_
- Regression: Filterset defined as method (and from a @property) are not supported [Nicolas Delaby]
- bugfix view-level AutoSchema noneffective with extend_schema `#241 <https://github.com/tfranzel/drf-spectacular/issues/241>`_
- bugfix incorrect warning on paginated actions `#233 <https://github.com/tfranzel/drf-spectacular/issues/233>`_

Breaking changes:

- several small improvements that should not have a big impact. this is a y-stream release mainly due to schema changes that may occur with *django-filter*.

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

- reverted back to *0.10.0* Swagger UI behavior as default. Users relying on stricter CSP should use ``SpectacularSwaggerSplitView``
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
- Fix whitespace issues in code [Nix]
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
- Add ``deepLinking`` parameter [p.alekseev]
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

- Schemas are functionally identical, but component sorting changed slightly.
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
- Fix getting default parameter for ``MultipleChoiceField`` [p.alekseev]
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

- removed ``to_schema()`` from ``OpenApiParameter``. Handled in ``AutoSchema`` now.

0.8.8 (2020-03-21)
------------------
- Documentation. 
- Schema serving with ``SpectacularAPIView``  (configurable)
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
