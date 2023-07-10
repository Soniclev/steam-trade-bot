import asyncio
from asyncio.proactor_events import _ProactorBasePipeTransport
from functools import wraps


def _silence_event_loop_closed(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except RuntimeError as e:
            if str(e) != 'Event loop is closed':
                raise
    return wrapper


def spark_run_async(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        async def async_func():
            return await func(*args, **kwargs)

        _ProactorBasePipeTransport.__del__ = _silence_event_loop_closed(
            _ProactorBasePipeTransport.__del__)
        return asyncio.run(async_func())

    return wrapper


def surround_async(func):
    return spark_run_async(func)
