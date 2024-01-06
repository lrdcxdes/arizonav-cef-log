from typing import Callable, Type

from ceflogs.filters import Filter
from ceflogs.types import Log


class CefLogsHandler:
    def __init__(self, log_type: Type[Log], callback: Callable, filters: Filter = None):
        self.log_type = log_type
        self.callback = callback
        self.filters = filters

    async def check(self, log: Log):
        if callable(self.filters):
            return await self.filters(log)

        return True
