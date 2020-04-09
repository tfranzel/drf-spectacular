Changelog
=========

0.9.1 (2020-04-09)
------------------

- Bugfix missing openapi schema spec json in package
- Add multi-method action decoration support.
- rest-polymorphic str loading prep.
- Improve list view detection.
- Bugfix: response codes must be string. closes #17.

0.9.0 (2020-03-29)
------------------

- Add missing related serializer fields #15.
- Bugfix properties with $ref component. closes #16.
- Bugfix polymorphic resource_type lookup. closes #14.
- Generalize plugin system.
- Support ``required`` parameter for body. [p.alekseev]
- Improve serializer retrieval.
- Add query serializer support #10.
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
- Change operation sorting to alphanumeric with option (#6) 
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

