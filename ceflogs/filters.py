import inspect
import re
from typing import Callable, Union, List, Pattern

from ceflogs.types import Log, ChatLog, NotificationLog


class Filter:
    async def __call__(self, client: "ceflogs.client.CefLogs", log: Log):
        raise NotImplementedError

    def __invert__(self):
        return InvertFilter(self)

    def __and__(self, other):
        return AndFilter(self, other)

    def __or__(self, other):
        return OrFilter(self, other)


class InvertFilter(Filter):
    def __init__(self, base):
        self.base = base

    async def __call__(self, client: "ceflogs.client.CefLogs", log: Log):
        if inspect.iscoroutinefunction(self.base.__call__):
            x = await self.base(log)
        else:
            x = await client.loop.run_in_executor(None, self.base, log)

        return not x


class AndFilter(Filter):
    def __init__(self, base, other):
        self.base = base
        self.other = other

    async def __call__(self, client: "ceflogs.client.CefLogs", log: Log):
        if inspect.iscoroutinefunction(self.base.__call__):
            x = await self.base(client, log)
        else:
            x = await client.loop.run_in_executor(None, self.base, client, log)

            # short circuit
        if not x:
            return False

        if inspect.iscoroutinefunction(self.other.__call__):
            y = await self.other(client, log)
        else:
            y = await client.loop.run_in_executor(None, self.other, client, log)

        return x and y


class OrFilter(Filter):
    def __init__(self, base, other):
        self.base = base
        self.other = other

    async def __call__(self, client: "ceflogs.client.CefLogs", log: Log):
        if inspect.iscoroutinefunction(self.base.__call__):
            x = await self.base(client, log)
        else:
            x = await client.loop.run_in_executor(None, self.base, client, log)

            # short circuit
        if x:
            return True

        if inspect.iscoroutinefunction(self.other.__call__):
            y = await self.other(client, log)
        else:
            y = await client.loop.run_in_executor(None, self.other, client, log)

        return x or y


CUSTOM_FILTER_NAME = "CustomFilter"


def create(func: Callable, name: str = None, **kwargs) -> Filter:
    return type(
        name or func.__name__ or CUSTOM_FILTER_NAME,
        (Filter,),
        {"__call__": func, **kwargs},
    )()


# region all_filter
async def all_filter(_, __):
    return True


# noinspection PyShadowingBuiltins
all = create(all_filter)
"""Filter all messages."""

# endregion


def chat_type(value: Union[str, List[str]]):
    """Filter chat messages by their ``type``.

    Can be applied to handlers that receive one of the following logs:

    - :obj:`~ChatLog`: The filter will match ``type``.

    Parameters:
        value (``str``):
            The chat type to match.
    """

    async def func(_, log: ChatLog):
        return log.type in value

    return create(func, "ChatTypeFilter", value=value)


# region startswith


def startswith(prefix: Union[str, List[str]]):
    """Filter logs that start with a given prefix.

    Can be applied to handlers that receive one of the following logs:

    - :obj:`~ChatLog`: The filter will match ``message``.
    - :obj:`~NotificationLog`: The filter will match ``text`` and ``pre`` elements.

    Parameters:
        prefix (``str`` | ``List[str]``):
            The prefix to match. If a list is passed, any of the prefixes will match.
    """

    async def func(flt, log: Log):
        if isinstance(log, ChatLog):
            value = log.message
        elif isinstance(log, NotificationLog):
            value = " ".join(
                [i.value for i in log.elements if i.node == "text" or i.node == "pre"]
            )
        else:
            raise ValueError(f"Startswith filter doesn't work with {type(log)}")

        if value:
            return value.startswith(flt.prefix)

    return create(func, "StartswithFilter", prefix=prefix)


# endregion


def regex(pattern: Union[str, Pattern], flags: int = 0):
    """Filter logs that match a given regular expression pattern.

    Can be applied to handlers that receive one of the following logs:

    - :obj:`~ChatLog`: The filter will match ``message``.
    - :obj:`~NotificationLog`: The filter will match ``text`` and ``pre`` elements.

    When a pattern matches, all the `Match Objects <https://docs.python.org/3/library/re.html#match-objects>`_ are
    stored in the ``matches`` field of the log object itself.

    Parameters:
        pattern (``str`` | ``Pattern``):
            The regex pattern as string or as pre-compiled pattern.

        flags (``int``, *optional*):
            Regex flags.
    """

    async def func(flt, log: Log):
        if isinstance(log, ChatLog):
            value = log.message
        elif isinstance(log, NotificationLog):
            value = " ".join(
                [i.value for i in log.elements if i.node == "text" or i.node == "pre"]
            )
        else:
            raise ValueError(f"Regex filter doesn't work with {type(log)}")

        if value:
            log.matches = list(flt.p.finditer(value)) or None

        return bool(log.matches)

    return create(
        func,
        "RegexFilter",
        p=pattern if isinstance(pattern, Pattern) else re.compile(pattern, flags),
    )
