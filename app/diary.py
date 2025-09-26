"""Diary and chat endpoints."""

from __future__ import annotations

import uuid
from collections import Counter
from datetime import date, datetime, timezone
from typing import Iterable, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user
from app.gemini_client import generate_summary
from app.models import (
    ChatMessage,
    ChatMessageCreate,
    DiarySummary,
    DiaryTimeline,
    DiaryTimelineEntry,
)
from app.redis_client import redis_client

router = APIRouter(prefix="/diary", tags=["diary"])

POSITIVE_WORDS = {
    "happy",
    "excited",
    "great",
    "awesome",
    "amazing",
    "love",
    "joy",
    "good",
    "fantastic",
    "proud",
}
NEGATIVE_WORDS = {
    "sad",
    "tired",
    "angry",
    "upset",
    "bad",
    "worried",
    "stress",
    "stressed",
    "anxious",
    "frustrated",
}


def _chat_key(username: str, day: date) -> str:
    return f"chat:{username}:{day.isoformat()}"


def _summary_key(username: str, day: date) -> str:
    return f"summary:{username}:{day.isoformat()}"


def _load_messages(username: str, day: date) -> List[ChatMessage]:
    key = _chat_key(username, day)
    raw_messages = redis_client.lrange(key, 0, -1)
    messages: List[ChatMessage] = []
    for raw in raw_messages:
        try:
            messages.append(ChatMessage.parse_raw(raw))
        except Exception:  # pragma: no cover - defensive against bad data
            continue
    return messages


def _store_message(username: str, message: ChatMessage) -> None:
    key = _chat_key(username, message.timestamp.date())
    redis_client.rpush(key, message.json())


def _store_summary(username: str, summary: DiarySummary) -> None:
    redis_client.set(_summary_key(username, summary.date), summary.json())


def _load_summary(username: str, day: date) -> Optional[DiarySummary]:
    raw = redis_client.get(_summary_key(username, day))
    if not raw:
        return None
    try:
        return DiarySummary.parse_raw(raw)
    except Exception:  # pragma: no cover - defensive
        return None


def _build_prompt(day: date, messages: Iterable[ChatMessage]) -> str:
    conversations = []
    for message in messages:
        timestamp = message.timestamp.astimezone(timezone.utc).isoformat()
        conversations.append(f"[{timestamp}] {message.role.upper()}: {message.text}")
    conversation_text = "\n".join(conversations)
    return (
        "You are an empathetic journaling assistant. Summarise the user's day "
        "based on the following chat transcript. Provide a short paragraph "
        "summary, followed by bullet point highlights and an overall mood word.\n"
        f"Date: {day.isoformat()}\n"
        "Transcript:\n"
        f"{conversation_text}\n"
        "Response format:\n"
        "Summary: <paragraph>\n"
        "Highlights:\n- <point>\n"
        "Mood: <single word>\n"
    )


def _infer_mood(messages: Iterable[ChatMessage]) -> str:
    score = 0
    for message in messages:
        if message.role != "user":
            continue
        text = message.text.lower()
        score += sum(1 for word in POSITIVE_WORDS if word in text)
        score -= sum(1 for word in NEGATIVE_WORDS if word in text)
    if score > 1:
        return "positive"
    if score < -1:
        return "negative"
    return "neutral"


def _extract_highlights(messages: Iterable[ChatMessage], limit: int = 3) -> List[str]:
    user_messages = [m.text for m in messages if m.role == "user"]
    if not user_messages:
        return []
    # Pick the most recent distinct messages as highlights.
    highlights: List[str] = []
    for text in reversed(user_messages):
        cleaned = text.strip()
        if cleaned and cleaned not in highlights:
            highlights.append(cleaned)
        if len(highlights) == limit:
            break
    highlights.reverse()
    return highlights


def _extract_tags(messages: Iterable[ChatMessage], limit: int = 5) -> List[str]:
    words: Counter[str] = Counter()
    for message in messages:
        if message.role != "user":
            continue
        for word in message.text.split():
            cleaned = "".join(ch for ch in word.lower() if ch.isalnum())
            if len(cleaned) >= 4:
                words[cleaned] += 1
    most_common = [word for word, _ in words.most_common(limit)]
    return most_common


@router.post("/add", response_model=ChatMessage, status_code=status.HTTP_201_CREATED)
def add_entry(
    payload: ChatMessageCreate, username: str = Depends(get_current_user)
) -> ChatMessage:
    now = datetime.now(timezone.utc)
    message = ChatMessage(
        message_id=str(uuid.uuid4()),
        role=payload.role,
        text=payload.text,
        timestamp=now,
    )
    _store_message(username, message)
    return message


@router.get("/timeline", response_model=DiaryTimeline)
def get_timeline(username: str = Depends(get_current_user)) -> DiaryTimeline:
    pattern = f"chat:{username}:*"
    entries: List[DiaryTimelineEntry] = []
    for key in redis_client.scan_iter(match=pattern):
        _, _, date_str = key.split(":", 2)
        day = date.fromisoformat(date_str)
        messages = _load_messages(username, day)
        summary = _load_summary(username, day)
        entries.append(DiaryTimelineEntry(date=day, messages=messages, summary=summary))
    entries.sort(key=lambda entry: entry.date, reverse=True)
    return DiaryTimeline(entries=entries)


@router.get("/list", response_model=List[DiarySummary])
def get_list(username: str = Depends(get_current_user)) -> List[DiarySummary]:
    summaries: List[DiarySummary] = []
    pattern = f"summary:{username}:*"
    for key in redis_client.scan_iter(match=pattern):
        day = date.fromisoformat(key.split(":", 2)[2])
        summary = _load_summary(username, day)
        if summary:
            summaries.append(summary)
    summaries.sort(key=lambda item: item.date, reverse=True)
    return summaries


@router.post("/generate/{entry_date}", response_model=DiarySummary)
def generate_daily_summary(entry_date: str, username: str = Depends(get_current_user)) -> DiarySummary:
    try:
        day = date.fromisoformat(entry_date)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format") from exc

    messages = _load_messages(username, day)
    if not messages:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No chat history for the requested date")

    prompt = _build_prompt(day, messages)
    summary_text = generate_summary(prompt)

    diary_summary = DiarySummary(
        date=day,
        summary=summary_text,
        mood=_infer_mood(messages),
        highlights=_extract_highlights(messages),
        tags=_extract_tags(messages),
    )
    _store_summary(username, diary_summary)
    return diary_summary
