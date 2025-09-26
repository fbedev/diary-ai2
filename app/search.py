from fastapi import APIRouter
from app.models import SearchQuery
from app.gemini_client import generate_summary
from app.redis_client import redis_client

router = APIRouter(prefix="/search", tags=["search"])

@router.post("/")
def search(query: SearchQuery):
    entries = [redis_client.get(k) for k in redis_client.keys("diary:*")]
    docs = "\n".join([e for e in entries if e])
    prompt = f"Search through these diary entries:\n{docs}\n\nQuery: {query.query}\nAnswer:"
    return {"result": generate_summary(prompt)}