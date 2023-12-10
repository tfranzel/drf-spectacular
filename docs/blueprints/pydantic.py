from drf_spectacular.extensions import OpenApiSerializerExtension
from drf_spectacular.plumbing import ResolvedComponent

from pydantic.schema import model_schema


class PydanticExtension(OpenApiSerializerExtension):
    target_class = "pydantic.BaseModel"
    match_subclasses = True
    priority = 1

    def get_name(self, auto_schema, direction):
        return self.target.__name__

    def map_serializer(self, auto_schema, direction):

        # let pydantic generate a JSON schema
        schema = model_schema(self.target, ref_prefix="#/components/schemas/")

        # pull out potential sub-schemas and put them into component section
        for sub_name, sub_schema in schema.pop("definitions", {}).items():
            component = ResolvedComponent(
                name=sub_name,
                type=ResolvedComponent.SCHEMA,
                object=sub_name,
                schema=sub_schema,
            )
            auto_schema.registry.register_on_missing(component)

        return schema
