import contextlib
import functools
import sys
from collections import defaultdict
from typing import DefaultDict


class GeneratorStats:
    _warn_cache: DefaultDict[str, int] = defaultdict(int)
    _error_cache: DefaultDict[str, int] = defaultdict(int)

    def __getattr__(self, name):
        if not self.__dict__:
            from drf_spectacular.settings import spectacular_settings
            self.silent = spectacular_settings.DISABLE_ERRORS_AND_WARNINGS
        return getattr(self, name)

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
        msg = _get_current_trace() + str(msg)
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


def warn(msg):
    GENERATOR_STATS.emit(msg, 'warning')


def error(msg):
    GENERATOR_STATS.emit(msg, 'error')


def reset_generator_stats():
    GENERATOR_STATS.reset()


_TRACES = []


@contextlib.contextmanager
def add_trace_message(trace_message):
    """
    Adds a message to be used as a prefix when emitting warnings and errors.
    """
    _TRACES.append(trace_message)
    yield
    _TRACES.pop()


def _get_current_trace():
    return ''.join(f"{trace}: " for trace in _TRACES if trace)


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
    obj._spectacular_annotation[prop] = value
    return obj


def get_view_methods(view, schema=None):
    return [
        getattr(view, item) for item in dir(view) if callable(getattr(view, item)) and (
            item in view.http_method_names
            or item in (schema or view.schema).method_mapping.values()
            or item == 'list'
            or hasattr(getattr(view, item), 'mapping')
        )
    ]


def cache(user_function):
    """ simple polyfill for python < 3.9 """
    return functools.lru_cache(maxsize=None)(user_function)
