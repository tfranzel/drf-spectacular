import sys
from collections import defaultdict
from typing import DefaultDict


class GeneratorStats:
    _warn_cache: DefaultDict[str, int] = defaultdict(int)
    _error_cache: DefaultDict[str, int] = defaultdict(int)

    def __bool__(self):
        return bool(self._warn_cache or self._error_cache)

    def reset(self):
        self._warn_cache.clear()
        self._error_cache.clear()

    def emit(self, msg, severity):
        assert severity in ['warning', 'error']
        msg = str(msg)
        cache = self._warn_cache if severity == 'warning' else self._error_cache
        if msg not in cache:
            print(f'{severity.capitalize()} #{len(cache)}: {msg}', file=sys.stderr)
        cache[msg] += 1

    def emit_summary(self):
        if self._warn_cache or self._error_cache:
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


def has_override(obj, prop):
    if not hasattr(obj, '_spectacular_annotation'):
        return False
    if prop not in obj._spectacular_annotation:
        return False
    return True


def get_override(obj, prop, default=None):
    if not has_override(obj, prop):
        return default
    return obj._spectacular_annotation[prop]


def set_override(obj, prop, value):
    if not hasattr(obj, '_spectacular_annotation'):
        obj._spectacular_annotation = {}
    obj._spectacular_annotation[prop] = value


def get_view_methods(view, schema=None):
    return [
        getattr(view, item) for item in dir(view) if callable(getattr(view, item)) and (
            item in view.http_method_names
            or item in (schema or view.schema).method_mapping.values()
            or item == 'list'
            or hasattr(getattr(view, item), 'mapping')
        )
    ]
