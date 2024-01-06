import asyncio
import inspect
import json
from datetime import datetime
from pathlib import Path
import signal
from signal import signal as signal_fn, SIGINT, SIGTERM, SIGABRT
from typing import AsyncGenerator, Type, List, Callable

from ceflogs.sync import async_to_sync
from ceflogs.handler import CefLogsHandler
from ceflogs.filters import Filter
from ceflogs.types import LogType, NotificationLog, NotificationElement, ChatLog, Log
from ceflogs.logger import logger

signals = {
    k: v
    for v, k in signal.__dict__.items()
    if v.startswith("SIG") and not v.startswith("SIG_")
}


class CefLogs:
    def __init__(
        self, log_path: Path | str = r"C:\RAGEMP\clientdata\cef_game_logs.txt"
    ):
        self.last_update_time: datetime
        self.log_path = log_path if isinstance(log_path, Path) else Path(log_path)
        self.loop = None
        self.handlers: list[CefLogsHandler] = []

    def on(self, log_type: Type[Log], filters: List[Filter] = None):
        def decorator(callback: Callable):
            self.handlers.append(CefLogsHandler(log_type, callback, filters))
            return callback

        return decorator

    # Read game live-logs
    async def _read_logs(self) -> AsyncGenerator[str, None]:
        with open(self.log_path, "r", encoding="utf-8") as file:
            # Go to the end of the file
            file.seek(0, 2)
            logger.info("Reading logs...")
            while True:
                # Read last line
                line = file.readline()
                # If line is empty, wait a bit and try again
                if not line:
                    await asyncio.sleep(0.1)
                    continue
                # Yield the line
                yield line

    # Parse game live-logs
    async def _parse_logs(self) -> AsyncGenerator[Log, None]:
        async for line in self._read_logs():
            if " logs]" in line:
                logger.info(line)

                log_type = (
                    LogType.CHAT
                    if '"[chat logs]' in line
                    else LogType.NOTIFICATION
                    if '"[notification logs]' in line
                    else None
                )
                if log_type is None:
                    continue
                try:
                    json_raw = (
                        line.split(f'"[{log_type.name.lower()} logs] ')[1]
                        .split('", source: package://userinterface/build/bundle.js')[0]
                        .strip()
                    )
                except IndexError:
                    logger.error("IndexError: " + line)
                    continue
                try:
                    json_data = json.loads(json_raw)
                except json.decoder.JSONDecodeError:
                    logger.error("JSONDecodeError: " + line)
                    continue

                if log_type == LogType.NOTIFICATION:
                    yield NotificationLog(
                        key=json_data["key"],
                        title=json_data["title"],
                        elements=[
                            NotificationElement(
                                node=element["node"], value=element["value"]
                            )
                            for element in json_data["elements"]
                        ],
                        timeout=json_data["timeout"],
                        endtime=json_data["endtime"],
                        percent=json_data["percent"],
                    )

                elif log_type == LogType.CHAT:
                    yield ChatLog(
                        type=json_data.get("type"),
                        message=json_data["message"],
                        vip=json_data.get("vip"),
                        sender=json_data.get("sender"),
                        sender_number=json_data.get("senderNumber"),
                        editor=json_data.get("editor"),
                        rank_name=json_data.get("rankName"),
                        from_name=json_data.get("from"),
                        from_id=json_data.get("fromId"),
                        gov_tag=json_data.get("govTag"),
                        tag_color=json_data.get("tagColor"),
                        tag_background=json_data.get("tagBackground"),
                        tag=json_data.get("tag"),
                    )

    async def get_logs(self) -> AsyncGenerator[Log, None]:
        async for log in self._parse_logs():
            yield log

    async def dispatch(self, log: Log):
        for handler in self.handlers:
            if isinstance(log, handler.log_type):
                if await handler.check(log):
                    if inspect.iscoroutinefunction(handler.callback):
                        await handler.callback(log)
                    else:
                        self.loop.run_in_executor(None, handler.callback, log)

    async def handle_logs(self) -> None:
        async for log in self.get_logs():
            logger.debug(log)
            await self.dispatch(log)

    async def idle(self) -> None:
        task = None

        def signal_handler(signum, __):
            logging.info(f"Stop signal received ({signals[signum]}). Exiting...")
            task.cancel()

        for s in (SIGINT, SIGTERM, SIGABRT):
            signal_fn(s, signal_handler)
        while True:
            task = self.loop.create_task(asyncio.sleep(600))
            await task

    async def start(self):
        logger.info("Starting CefLogs...")
        await self.handle_logs()
        return self

    async def stop(self):
        self.loop.stop()
        logger.info("Bye!")

    def run(self) -> None:
        self.loop = asyncio.get_event_loop()
        try:
            run = self.loop.run_until_complete

            if inspect.iscoroutinefunction(self.start):
                run(self.start())
                run(self.idle())
                run(self.stop())
            else:
                self.start()
                run(self.idle())
                self.stop()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Bye!")
        except Exception as e:
            logger.error(e)
        finally:
            self.loop.close()


async_to_sync(CefLogs, "get_logs")
async_to_sync(CefLogs, "dispatch")
async_to_sync(CefLogs, "handle_logs")
async_to_sync(CefLogs, "start")
async_to_sync(CefLogs, "stop")
async_to_sync(CefLogs, "idle")
