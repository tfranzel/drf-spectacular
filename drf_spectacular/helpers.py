from django.utils.module_loading import import_string


def lazy_serializer(path):
    """ simulate initiated object but actually load class and init on first usage """

    class LazySerializer:
        def __init__(self, *args, **kwargs):
            self.lazy_args, self.lazy_kwargs, self.lazy_obj = args, kwargs, None

        def __getattr__(self, item):
            if not self.lazy_obj:
                self.lazy_obj = import_string(path)(*self.lazy_args, **self.lazy_kwargs)
            return getattr(self.lazy_obj, item)

        @property  # type: ignore
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
