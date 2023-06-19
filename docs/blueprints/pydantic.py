from drf_spectacular.extensions import OpenApiSerializerExtension
from drf_spectacular.plumbing import ResolvedComponent


class PydanticExtension(OpenApiSerializerExtension):
    target_class = 'pydantic.BaseModel'
    match_subclasses = True

    def get_name(self, auto_schema, direction):
        return self.target.__name__

    def map_serializer(self, auto_schema, direction):
        def translate_refs(obj, key=None):
            if isinstance(obj, dict):
                return {k: translate_refs(v, k) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [translate_refs(i) for i in obj]
            elif key == '$ref':
                return obj.replace('#/definitions/', '#/components/schemas/')
            else:
                return obj

        # let pydantic generate a JSON schema
        schema = self.target.schema()

        # pull out potential sub-schemas and put them into component section
        for sub_name, sub_schema in schema.pop('definitions', {}).items():
            component = ResolvedComponent(
                name=sub_name,
                type=ResolvedComponent.SCHEMA,
                object=sub_name,
                schema=translate_refs(sub_schema),
            )
            auto_schema.registry.register_on_missing(component)

        return translate_refs(schema)
