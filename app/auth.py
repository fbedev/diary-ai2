from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.redis_client import redis_client
from app.models import UserLogin, UserRegister
import bcrypt, uuid

router = APIRouter(prefix="/auth", tags=["auth"])

USERS = {}  # Replace with real DB later

class TokenData(BaseModel):
    token: str

@router.post("/signup")
def register(data: UserRegister):
    if data.username in USERS:
        raise HTTPException(status_code=400, detail="User already exists")
    hashed = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    USERS[data.username] = hashed
    return {"status": "success", "message": "User registered successfully"}

@router.post("/login")
def login(data: UserLogin):
    hashed = USERS.get(data.username)
    if not hashed or not bcrypt.checkpw(data.password.encode(), hashed.encode()):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = str(uuid.uuid4())
    redis_client.setex(f"session:{token}", 3600, data.username)
    return {"status": "success", "token": token}

@router.post("/logout")
def logout(data: TokenData):
    redis_client.delete(f"session:{data.token}")
    return {"status": "success", "message": "Logged out successfully"}