"""Administrative helper endpoints."""

from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.redis_client import redis_client

router = APIRouter(prefix="/admin", tags=["admin"])


def _list_usernames() -> List[str]:
    usernames: List[str] = []
    for key in redis_client.scan_iter(match="user:*"):
        _, username = key.split(":", 1)
        usernames.append(username)
    usernames.sort()
    return usernames


def _list_sessions() -> List[Dict[str, str]]:
    sessions: List[Dict[str, str]] = []
    for key in redis_client.scan_iter(match="session:*"):
        data = redis_client.hgetall(key)
        if data:
            sessions.append({"token": key.split(":", 1)[1], **data})
    sessions.sort(key=lambda session: session.get("created_at", ""), reverse=True)
    return sessions


def _count_diary_entries() -> int:
    count = 0
    for key in redis_client.scan_iter(match="chat:*"):
        count += redis_client.llen(key)
    return count


@router.get("/dashboard")
def admin_dashboard(username: str = Depends(get_current_user)):
    return {
        "current_user": username,
        "total_users": len(_list_usernames()),
        "active_sessions": len(_list_sessions()),
        "stored_messages": _count_diary_entries(),
    }


@router.get("/users")
def list_users(_: str = Depends(get_current_user)):
    return {"users": _list_usernames()}


@router.get("/sessions")
def list_sessions(_: str = Depends(get_current_user)):
    return {"sessions": _list_sessions()}
