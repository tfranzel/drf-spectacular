import importlib


def assert_schema(schema, reference_file):
    from drf_spectacular.renderers import NoAliasOpenAPIRenderer

    schema_yml = NoAliasOpenAPIRenderer().render(schema, renderer_context={})

    with open(reference_file.replace('.yml', '_out.yml'), 'wb') as fh:
        fh.write(schema_yml)

    with open(reference_file) as fh:
        assert schema_yml.decode() == fh.read()


def import_class(import_str):
    import_path = import_str.split('.')
    module, klass = '.'.join(import_path[:-1]), import_path[-1]
    return getattr(importlib.import_module(module), klass)


def lazy_serializer(path):
    class LazySerializer:
        """ simulate initiated object but actually load class and init on first usage """

        def __init__(self, *args, **kwargs):
            self.lazy_args, self.lazy_kwargs, self.lazy_obj = args, kwargs, None

        def __getattr__(self, item):
            if not self.lazy_obj:
                self.lazy_obj = import_class(path)(*self.lazy_args, **self.lazy_kwargs)
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
