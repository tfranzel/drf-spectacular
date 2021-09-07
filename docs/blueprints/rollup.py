from drf_spectacular.contrib.rest_polymorphic import PolymorphicSerializerExtension
from drf_spectacular.plumbing import ResolvedComponent
from drf_spectacular.serializers import PolymorphicProxySerializerExtension
from drf_spectacular.settings import spectacular_settings


class RollupMixin:
    """
    This is a schema helper that pulls the "common denominator" fields from child
    components into their parent component. It only applies to PolymorphicSerializer
    as well as PolymorphicProxySerializer, where there is an (implicit) inheritance hierarchy.

    The actual functionality is realized via extensions defined below.
    """
    def map_serializer(self, auto_schema, direction):
        schema = super().map_serializer(auto_schema, direction)

        if isinstance(self, PolymorphicProxySerializerExtension):
            sub_serializers = self.target.serializers
        else:
            sub_serializers = [
                self.target._get_serializer_from_model_or_instance(sub_model)
                for sub_model in self.target.model_serializer_mapping
            ]

        resolved_sub_serializers = [
            auto_schema.resolve_serializer(sub, direction) for sub in sub_serializers
        ]
        # this will only be generated on return of map_serializer so mock it for now
        mocked_component = ResolvedComponent(
            name=auto_schema._get_serializer_name(self.target, direction),
            type=ResolvedComponent.SCHEMA,
            object=self.target,
            schema=schema
        )

        # hack for recursive models. at the time of extension execution, not all sub
        # serializer schema have been generated, so no rollup is possible.
        # by registering a local variable scoped postproc hook, we delay this
        # execution to the end where all schemas are present.
        def postprocessing_rollup_hook(generator, result, **kwargs):
            rollup_properties(mocked_component, resolved_sub_serializers)
            result['components'] = generator.registry.build({})
            return result

        # register postproc hook. must run before enum postproc due to rebuilding the registry
        spectacular_settings.POSTPROCESSING_HOOKS.insert(0, postprocessing_rollup_hook)
        # and do nothing for now
        return schema


def rollup_properties(component, resolved_sub_serializers):
    # rollup already happened (spectacular bug and normally not needed)
    if any('allOf' in r.schema for r in resolved_sub_serializers):
        return

    all_field_sets = [
        set(list(r.schema['properties'])) for r in resolved_sub_serializers
    ]
    common_fields = all_field_sets[0].intersection(*all_field_sets[1:])
    common_schema = {
        'properties': {},
        'required': set(),
    }

    # substitute sub serializers' common fields with base class
    for r in resolved_sub_serializers:
        for cf in sorted(common_fields):
            if cf in r.schema['properties']:
                common_schema['properties'][cf] = r.schema['properties'][cf]
                del r.schema['properties'][cf]
                if cf in r.schema.get('required', []):
                    common_schema['required'].add(cf)
        r.schema = {'allOf': [component.ref, r.schema]}

    # modify regular schema for field rollup
    del component.schema['oneOf']
    component.schema['properties'] = common_schema['properties']
    if common_schema['required']:
        component.schema['required'] = sorted(common_schema['required'])


class PolymorphicRollupSerializerExtension(RollupMixin, PolymorphicSerializerExtension):
    priority = 1


class PolymorphicProxyRollupSerializerExtension(RollupMixin, PolymorphicProxySerializerExtension):
    priority = 1
