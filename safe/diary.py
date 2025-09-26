from fastapi import APIRouter, Depends
from app.models import DiaryEntry
from app.redis_client import redis_client
import uuid, json

router = APIRouter(prefix="/diary", tags=["diary"])

@router.post("/add")
def add_entry(entry: DiaryEntry):
    entry_id = str(uuid.uuid4())
    redis_client.set(f"diary:{entry_id}", entry.json())
    return {"id": entry_id, "msg": "Diary entry added"}

@router.get("/timeline")
def get_timeline():
    keys = redis_client.keys("diary:*")
    entries = [redis_client.get(k) for k in keys]
    return {"entries": [json.loads(e) for e in entries if e]}