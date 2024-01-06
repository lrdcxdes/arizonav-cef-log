import asyncio
import functools
import inspect
import os
import threading

from ceflogs.logger import logger


def async_to_sync(obj, name):
    function = getattr(obj, name)
    main_loop = asyncio.get_event_loop()

    def async_to_sync_gen(agen, loop, is_main_thread):
        async def anext(agen):
            try:
                return await agen.__anext__(), False
            except StopAsyncIteration:
                return None, True

        while True:
            if is_main_thread:
                item, done = loop.run_until_complete(anext(agen))
            else:
                item, done = asyncio.run_coroutine_threadsafe(
                    anext(agen), loop
                ).result()

            if done:
                break

            yield item

    @functools.wraps(function)
    def async_to_sync_wrap(*args, **kwargs):
        try:
            coroutine = function(*args, **kwargs)

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            if (
                threading.current_thread() is threading.main_thread()
                or not main_loop.is_running()
            ):
                if loop.is_running():
                    return coroutine
                else:
                    if inspect.iscoroutine(coroutine):
                        return loop.run_until_complete(coroutine)

                    if inspect.isasyncgen(coroutine):
                        return async_to_sync_gen(coroutine, loop, True)
            else:
                if inspect.iscoroutine(coroutine):
                    if loop.is_running():

                        async def coro_wrapper():
                            return await asyncio.wrap_future(
                                asyncio.run_coroutine_threadsafe(coroutine, main_loop)
                            )

                        return coro_wrapper()
                    else:
                        return asyncio.run_coroutine_threadsafe(
                            coroutine, main_loop
                        ).result()

                if inspect.isasyncgen(coroutine):
                    if loop.is_running():
                        return coroutine
                    else:
                        return async_to_sync_gen(coroutine, main_loop, False)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Bye!")
            # noinspection PyUnresolvedReferences,PyProtectedMember
            os._exit(0)
        except Exception as e:
            logger.error(e)
            # noinspection PyUnresolvedReferences,PyProtectedMember
            os._exit(0)

    setattr(obj, name, async_to_sync_wrap)


# Special case for idle and compose, because they are not inside Methods
# async_to_sync(Object, "idle")
# idle = getattr(Object, "idle")
