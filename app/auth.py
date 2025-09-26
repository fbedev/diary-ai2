"""Authentication endpoints and helpers."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.models import TokenData, UserLogin, UserProfile, UserRegister
from app.redis_client import redis_client

router = APIRouter(prefix="/auth", tags=["auth"])

SESSION_TTL_SECONDS = 60 * 60 * 12  # 12 hours


def _user_key(username: str) -> str:
    return f"user:{username}"


def _session_key(token: str) -> str:
    return f"session:{token}"


def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization")
) -> str:
    """Resolve the username for the current session token.

    The frontend should send the token in the form ``Authorization: Bearer <token>``.
    """

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    token = authorization.split(" ", 1)[1]
    username = redis_client.hget(_session_key(token), "username")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return username


@router.post("/signup")
def register(data: UserRegister):
    key = _user_key(data.username)
    if redis_client.exists(key):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")

    hashed = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    created_at = datetime.now(timezone.utc).isoformat()
    redis_client.hset(key, mapping={"password": hashed, "created_at": created_at})

    return {"status": "success", "message": "User registered successfully"}


@router.post("/login")
def login(data: UserLogin):
    key = _user_key(data.username)
    stored_hash = redis_client.hget(key, "password")
    if not stored_hash or not bcrypt.checkpw(data.password.encode(), stored_hash.encode()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = str(uuid.uuid4())
    session_key = _session_key(token)
    now = datetime.now(timezone.utc)
    redis_client.hset(
        session_key,
        mapping={
            "username": data.username,
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(seconds=SESSION_TTL_SECONDS)).isoformat(),
        },
    )
    redis_client.expire(session_key, SESSION_TTL_SECONDS)

    return {"status": "success", "token": token, "expires_in": SESSION_TTL_SECONDS}


@router.post("/logout")
def logout(token_data: TokenData):
    redis_client.delete(_session_key(token_data.token))
    return {"status": "success", "message": "Logged out successfully"}


@router.get("/me", response_model=UserProfile)
def read_profile(username: str = Depends(get_current_user)) -> UserProfile:
    user_raw = redis_client.hgetall(_user_key(username))
    if not user_raw:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    created_at = user_raw.get("created_at")
    if created_at:
        created_at_dt = datetime.fromisoformat(created_at)
    else:  # pragma: no cover - defensive default
        created_at_dt = datetime.now(timezone.utc)

    return UserProfile(username=username, created_at=created_at_dt)


__all__ = ["router", "get_current_user"]
