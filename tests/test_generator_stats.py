import inspect

import pytest

from drf_spectacular.drainage import GENERATOR_STATS


def test_known_attribute_access_succeeds():
    assert hasattr(GENERATOR_STATS, 'silent')


def test_unknown_attribute_access_fails():
    with pytest.raises(AttributeError):
        getattr(GENERATOR_STATS, '__spam__')


def test_inspect_unwrap():
    assert inspect.unwrap(GENERATOR_STATS) is GENERATOR_STATS


import threading
from concurrent.futures import ThreadPoolExecutor

from drf_spectacular.drainage import GeneratorStats, add_trace_message


def _trace_alpha():
    pass


def _trace_beta():
    pass


def test_caches_are_instance_state_not_class_state():
    stats_a = GeneratorStats()
    stats_b = GeneratorStats()
    with stats_a.silence():
        stats_a.emit('only in a', 'warning')
    assert stats_a._warn_cache
    assert not stats_b._warn_cache
    assert not stats_b._error_cache


def test_concurrent_emit_counts_are_exact():
    stats = GeneratorStats()
    threads, emits_per_thread = 8, 250

    def worker(n):
        with stats.silence():
            for i in range(emits_per_thread):
                stats.emit(f'unique {n}-{i}', 'warning')
                stats.emit('shared message', 'error')

    with ThreadPoolExecutor(max_workers=threads) as pool:
        list(pool.map(worker, range(threads)))

    assert len(stats._warn_cache) == threads * emits_per_thread
    assert sum(stats._warn_cache.values()) == threads * emits_per_thread
    # every shared error emit was counted exactly once
    shared = [v for k, v in stats._error_cache.items() if 'shared message' in k]
    assert shared == [threads * emits_per_thread]
    assert bool(stats) is True


def test_concurrent_emit_and_reset_do_not_raise():
    stats = GeneratorStats()

    def emitter():
        with stats.silence():
            for i in range(300):
                stats.emit(f'msg {i % 10}', 'warning')
                bool(stats)
                stats.emit_summary()

    def resetter():
        for _ in range(300):
            stats.reset()

    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = [pool.submit(emitter) for _ in range(3)]
        futures += [pool.submit(resetter) for _ in range(2)]
        for future in futures:
            future.result()  # re-raises any exception from the threads


def test_traces_are_isolated_between_threads():
    barrier = threading.Barrier(2)
    observed = {}

    def worker(fn, key):
        with add_trace_message(fn):
            # both threads are inside their trace context simultaneously;
            # neither may observe the other thread's breadcrumb.
            barrier.wait(timeout=10)
            observed[key] = GENERATOR_STATS._get_current_trace()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(worker, _trace_alpha, 'alpha'),
            pool.submit(worker, _trace_beta, 'beta'),
        ]
        for future in futures:
            future.result()

    assert observed['alpha'][1] == '_trace_alpha'
    assert observed['beta'][1] == '_trace_beta'
    # and both stacks unwound cleanly afterwards
    assert GENERATOR_STATS._traces == []


def test_trace_is_unwound_on_exception():
    def exploding():
        pass

    with pytest.raises(RuntimeError):
        with add_trace_message(exploding):
            raise RuntimeError('generation failed')
    assert GENERATOR_STATS._traces == []


def test_silence_is_isolated_between_threads():
    stats = GeneratorStats()
    barrier = threading.Barrier(2)
    observed = {}

    def silenced_worker():
        with stats.silence():
            barrier.wait(timeout=10)
            observed['inside'] = stats.silent
        observed['after'] = stats.silent

    def observing_worker():
        barrier.wait(timeout=10)
        observed['other_thread'] = stats.silent

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(silenced_worker), pool.submit(observing_worker)]
        for future in futures:
            future.result()

    assert observed['inside'] is True
    assert observed['other_thread'] is False
    assert observed['after'] is False
