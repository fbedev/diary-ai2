"""Pydantic models shared across the FastAPI app."""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)


class UserRegister(UserBase):
    password: str = Field(..., min_length=6, max_length=128)


class UserLogin(UserBase):
    password: str


class TokenData(BaseModel):
    token: str


class UserProfile(UserBase):
    created_at: datetime


class ChatMessage(BaseModel):
    """A single message exchanged between the user and the assistant."""

    message_id: str
    role: Literal["user", "assistant"] = "user"
    text: str = Field(..., min_length=1)
    timestamp: datetime


class ChatMessageCreate(BaseModel):
    """Payload used when storing a new chat message."""

    text: str = Field(..., min_length=1)
    role: Literal["user", "assistant"] = "user"


class DiarySummary(BaseModel):
    """Structured representation of a diary summary."""

    date: date
    summary: str
    mood: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class DiaryTimelineEntry(BaseModel):
    date: date
    messages: List[ChatMessage] = Field(default_factory=list)
    summary: Optional[DiarySummary] = None


class DiaryTimeline(BaseModel):
    entries: List[DiaryTimelineEntry]


class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1)


class SearchResult(BaseModel):
    query: str
    answer: str


__all__ = [
    "UserRegister",
    "UserLogin",
    "TokenData",
    "UserProfile",
    "ChatMessage",
    "ChatMessageCreate",
    "DiarySummary",
    "DiaryTimelineEntry",
    "DiaryTimeline",
    "SearchQuery",
    "SearchResult",
]
