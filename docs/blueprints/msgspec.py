import inspect
from typing import Any, Literal

import msgspec
from drf_spectacular.extensions import OpenApiSerializerExtension, AutoSchema
from drf_spectacular.plumbing import ResolvedComponent
from drf_spectacular.utils import Direction
from rest_framework.serializers import Field, Serializer
import logging

logger = logging.getLogger(__name__)



class MsgspecExtension(OpenApiSerializerExtension):
    """
    Allows using msgspec models on @extend_schema(request=..., response=...) to
    describe your API.
    """

    @classmethod
    def _matches(cls, target: Any) -> bool:
        """Match based on whether Msgspec can generate a schema"""
        try:
            return bool(msgspec.schema_components((target,)))
        except Exception as e:
            if inspect.isclass(target) and not isinstance(target, (Serializer, Field)):
                logger.debug("msgspec can't make schema", target=target, exc_info=e)
            return False

    def get_name(
        self,
        auto_schema: AutoSchema,
        direction: Literal["request"] | Literal["response"],
    ) -> str | None:
        """Get a name for a component

        Msgspec builds the names for the classes, we can extract it from the schema. The name
        is used by other components with internal references, so it is important that it is predictable.

        However, if we are building the name for a type like ``list[SomeStruct]``, ``out`` will not have a ``$ref``
        key, but it will be in the shape ``{"type": "array", "items": {"$ref": "ref/to/SomeStruct"}}``.
        So in this case we need to create the name ourselves.
        """

        (out,), components = msgspec.json.schema_components((self.target,), ref_template="{name}")
        if out.get("type") == "array" and "$ref" in out.get("items", {}):
            return f"ArrayOf{out['items']['$ref']}"

        return out.get("$ref")

    def map_serializer(
        self, auto_schema: AutoSchema, direction: Direction
    ) -> dict[str, Any]:

        # let msgspec generate a JSON schema
        possible_schemas, components = msgspec.json.schema_components(
            [self.target], ref_template='#/components/schemas/{name}'
        )
        schema = possible_schemas[0]
        # Schema is the current component, but it may need other references as well
        if "$ref" in schema:
            component_name = schema["$ref"].replace("#/components/schemas/", "")
            schema = components.pop(component_name)

        # pull out potential sub-schemas and put them into component section
        for sub_name, sub_schema in components.items():
            component = ResolvedComponent(
                name=sub_name,
                type=ResolvedComponent.SCHEMA,
                object=sub_name,
                schema=sub_schema,
            )
            auto_schema.registry.register_on_missing(component)

        return schema