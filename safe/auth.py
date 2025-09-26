from fastapi import APIRouter, Depends, HTTPException
from app.redis_client import redis_client
from app.models import UserLogin, UserRegister
import bcrypt, uuid

router = APIRouter(prefix="/auth", tags=["auth"])

USERS = {}  # Replace with real DB later

@router.post("/register")
def register(data: UserRegister):
    if data.username in USERS:
        raise HTTPException(400, "User exists")
    hashed = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    USERS[data.username] = hashed
    return {"msg": "Registered"}

@router.post("/login")
def login(data: UserLogin):
    hashed = USERS.get(data.username)
    if not hashed or not bcrypt.checkpw(data.password.encode(), hashed.encode()):
        raise HTTPException(401, "Invalid credentials")
    token = str(uuid.uuid4())
    redis_client.setex(f"session:{token}", 3600, data.username)
    return {"token": token}

@router.post("/logout")
def logout(token: str):
    redis_client.delete(f"session:{token}")
    return {"msg": "Logged out"}