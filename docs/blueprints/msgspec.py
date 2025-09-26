import inspect
from typing import Any

import msgspec
from drf_spectacular.extensions import OpenApiSerializerExtension
from drf_spectacular.plumbing import ResolvedComponent


def get_iterable_class(obj):
    """Return the underlying class, and if it was in a list."""
    if inspect.isclass(obj):
        return obj, False
    else:
        if getattr(obj, '__name__', 'none').lower() == 'list':
            return obj.__args__[0], True
        class_val = obj.__class__
        return class_val, False


class MsgspecExtension(OpenApiSerializerExtension):
    """
    Allows using msgspec models on @extend_schema(request=..., response=...) to
    describe your API.

    The outermost class (the @extend_schema argument) has to be a subclass
    of msgspec.Struct or a type annotation of list[Struct].
    """
    target_class = "msgspec.Struct"
    match_subclasses = True

    @classmethod
    def _matches(cls, target: Any) -> bool:
        """A customized match method to allow parsing list[Struct]"""
        if isinstance(cls.target_class, str):
            cls._load_class()

        if cls.target_class is None:
            return False  # app not installed
        elif cls.match_subclasses:
            try:
                class_val, _ = get_iterable_class(target)
                return issubclass(class_val, cls.target_class)  # type: ignore
            except TypeError:
                return False
        else:
            class_val, _ = get_iterable_class(target)
            return class_val == cls.target_class

    def get_name(self, auto_schema, direction):
        """Use the custom get_iterable_class to return the target Struct
        If part of a list, set the class name to be ArrayOf<Struct> to avoid
        overwriting the schema
        """
        class_val, is_iterable = get_iterable_class(self.target)
        class_name = class_val.__name__
        if is_iterable:
            class_name = f"ArrayOf{class_name}"
        return class_name

    def map_serializer(self, auto_schema, direction):

        # let msgspec generate a JSON schema
        possible_schemas, components = msgspec.json.schema_components(
            [self.target], ref_template='#/components/schemas/{name}'
        )
        possible_schema = possible_schemas[0]
        # If the outer schema has 'type' it means it is likely an array, so use that
        # as the schema. Otherwise, use the matching item from the components
        if 'type' in possible_schema:
            schema = possible_schema
        else:
            schema = components.pop(self.target.__name__)

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