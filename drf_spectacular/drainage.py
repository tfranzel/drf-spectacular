import contextlib
import functools
import sys
from collections import defaultdict
from typing import DefaultDict, List, Union


class GeneratorStats:
    _warn_cache: DefaultDict[str, int] = defaultdict(int)
    _error_cache: DefaultDict[str, int] = defaultdict(int)

    def __getattr__(self, name):
        if not self.__dict__:
            from drf_spectacular.settings import spectacular_settings
            self.silent = spectacular_settings.DISABLE_ERRORS_AND_WARNINGS
        try:
            return self.__dict__[name]
        except KeyError:
            raise AttributeError(name)

    def __bool__(self):
        return bool(self._warn_cache or self._error_cache)

    @contextlib.contextmanager
    def silence(self):
        self.silent, tmp = True, self.silent
        try:
            yield
        finally:
            self.silent = tmp

    def reset(self):
        self._warn_cache.clear()
        self._error_cache.clear()

    def emit(self, msg, severity):
        assert severity in ['warning', 'error']
        msg = _get_current_trace() + str(msg) + _get_current_trace_suffix()
        cache = self._warn_cache if severity == 'warning' else self._error_cache
        if not self.silent and msg not in cache:
            print(f'{severity.capitalize()} #{len(cache)}: {msg}', file=sys.stderr)
        cache[msg] += 1

    def emit_summary(self):
        if not self.silent and (self._warn_cache or self._error_cache):
            print(
                f'\nSchema generation summary:\n'
                f'Warnings: {sum(self._warn_cache.values())} ({len(self._warn_cache)} unique)\n'
                f'Errors:   {sum(self._error_cache.values())} ({len(self._error_cache)} unique)\n',
                file=sys.stderr
            )


GENERATOR_STATS = GeneratorStats()


def warn(msg, delayed=None):
    if delayed:
        warnings = get_override(delayed, 'warnings', [])
        warnings.append(msg)
        set_override(delayed, 'warnings', warnings)
    else:
        GENERATOR_STATS.emit(msg, 'warning')


def error(msg, delayed=None):
    if delayed:
        errors = get_override(delayed, 'errors', [])
        errors.append(msg)
        set_override(delayed, 'errors', errors)
    else:
        GENERATOR_STATS.emit(msg, 'error')


def reset_generator_stats():
    GENERATOR_STATS.reset()


_TRACES = []
_TRACES_SUFFIX: List[Union[str, None]] = []


@contextlib.contextmanager
def add_trace_message(trace_message, *, suffix: Union[str, None] = None):
    """
    Adds a message to be used as a prefix (and suffix) when emitting warnings and errors.
    """
    _TRACES.append(trace_message)
    _TRACES_SUFFIX.append(suffix)

    yield

    _TRACES.pop()
    _TRACES_SUFFIX.pop()


def _get_current_trace():
    return ''.join(f"{trace}: " for trace in _TRACES if trace)


def _get_current_trace_suffix():
    return ''.join(f" ({trace})" for trace in _TRACES_SUFFIX if trace)


def has_override(obj, prop):
    if isinstance(obj, functools.partial):
        obj = obj.func
    if not hasattr(obj, '_spectacular_annotation'):
        return False
    if prop not in obj._spectacular_annotation:
        return False
    return True


def get_override(obj, prop, default=None):
    if isinstance(obj, functools.partial):
        obj = obj.func
    if not has_override(obj, prop):
        return default
    return obj._spectacular_annotation[prop]


def set_override(obj, prop, value):
    if not hasattr(obj, '_spectacular_annotation'):
        obj._spectacular_annotation = {}
    elif '_spectacular_annotation' not in obj.__dict__:
        obj._spectacular_annotation = obj._spectacular_annotation.copy()
    obj._spectacular_annotation[prop] = value
    return obj


def get_view_method_names(view, schema=None):
    schema = schema or view.schema
    return [
        item for item in dir(view) if callable(getattr(view, item)) and (
            item in view.http_method_names
            or item in schema.method_mapping.values()
            or item == 'list'
            or hasattr(getattr(view, item), 'mapping')
        )
    ]


def isolate_view_method(view, method_name):
    """
    Prevent modifying a view method which is derived from other views. Changes to
    a derived method would leak into the view where the method originated from.
    Break derivation by wrapping the method and explicitly setting it on the view.
    """
    method = getattr(view, method_name)
    # no isolation is required if the view method is not derived.
    # @api_view is a special case that also breaks isolation. It proxies all view
    # methods through a single handler function, which then also requires isolation.
    if method_name in view.__dict__ and method.__name__ != 'handler':
        return method

    @functools.wraps(method)
    def wrapped_method(self, request, *args, **kwargs):
        return method(self, request, *args, **kwargs)

    # wraps() will only create a shallow copy of method.__dict__. Updates to "kwargs"
    # via @extend_schema would leak to the original method. Isolate by creating a copy.
    if hasattr(method, 'kwargs'):
        wrapped_method.kwargs = method.kwargs.copy()

    setattr(view, method_name, wrapped_method)
    return wrapped_method


def cache(user_function):
    """ simple polyfill for python < 3.9 """
    return functools.lru_cache(maxsize=None)(user_function)
