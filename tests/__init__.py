from django.utils.module_loading import import_string


def assert_schema(schema, reference_file):
    from drf_spectacular.renderers import NoAliasOpenAPIRenderer

    schema_yml = NoAliasOpenAPIRenderer().render(schema, renderer_context={})

    with open(reference_file.replace('.yml', '_out.yml'), 'wb') as fh:
        fh.write(schema_yml)

    with open(reference_file) as fh:
        assert schema_yml.decode() == fh.read()


def generate_schema(route, viewset):
    from rest_framework import routers
    from drf_spectacular.openapi import SchemaGenerator

    router = routers.SimpleRouter()
    router.register(route, viewset, basename=route)
    generator = SchemaGenerator(patterns=router.urls)
    return generator.get_schema(request=None, public=True)


def lazy_serializer(path):
    class LazySerializer:
        """ simulate initiated object but actually load class and init on first usage """

        def __init__(self, *args, **kwargs):
            self.lazy_args, self.lazy_kwargs, self.lazy_obj = args, kwargs, None

        def __getattr__(self, item):
            if not self.lazy_obj:
                self.lazy_obj = import_string(path)(*self.lazy_args, **self.lazy_kwargs)
            return getattr(self.lazy_obj, item)

        @property
        def __class__(self):
            return self.__getattr__('__class__')

        @property
        def __dict__(self):
            return self.__getattr__('__dict__')

        def __str__(self):
            return self.__getattr__('__str__')()

        def __repr__(self):
            return self.__getattr__('__repr__')()

    return LazySerializer
