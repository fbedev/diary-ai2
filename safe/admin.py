from fastapi import APIRouter
from app.redis_client import redis_client

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/dashboard")
def admin_dashboard():
    return {"status": "ok", "message": "Admin dashboard works"}

@router.get("/users")
def list_users():
    # Placeholder, replace with DB lookup
    return {"users": redis_client.keys("session:*")}

@router.get("/sessions")
def list_sessions():
    return {"sessions": redis_client.keys("session:*")}