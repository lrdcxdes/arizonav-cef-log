from pydantic import BaseModel
from typing import Optional
from enum import Enum


class Log(BaseModel):
    pass


class LogType(Enum):
    CHAT = 1
    NOTIFICATION = 2


class ChatLog(Log):
    type: Optional[str]
    message: str

    # Ads
    vip: Optional[bool]
    sender: Optional[str]
    sender_number: Optional[str]
    editor: Optional[str]

    # Local chat
    rank_name: Optional[str]
    from_name: Optional[str]
    from_id: Optional[int]

    # Department chat
    gov_tag: Optional[str]

    # Tag
    tag_color: Optional[str]
    tag_background: Optional[str]
    tag: Optional[str]


class NotificationElement(BaseModel):
    node: str
    value: str


class NotificationLog(Log):
    key: str
    title: str
    elements: list[NotificationElement]
    timeout: int
    endtime: int
    percent: int
