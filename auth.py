from fastapi import APIRouter, HTTPException
from app.redis_client import redis_client

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup")
def signup(username: str, password: str):
    if redis_client.exists(f"user:{username}"):
        raise HTTPException(status_code=400, detail="User already exists")
    redis_client.hset(f"user:{username}", mapping={"password": password, "role": "user"})
    return {"msg": "Signup successful"}

@router.post("/login")
def login(username: str, password: str):
    user = redis_client.hgetall(f"user:{username}")
    if not user or user.get("password") != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"msg": "Login successful"}