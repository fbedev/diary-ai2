"""Search endpoints for diary content."""

from __future__ import annotations

from typing import Iterable, List

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.gemini_client import generate_summary
from app.models import SearchQuery, SearchResult
from app.redis_client import redis_client

router = APIRouter(prefix="/search", tags=["search"])


def _collect_documents(username: str) -> List[str]:
    documents: List[str] = []
    for key in redis_client.scan_iter(match=f"summary:{username}:*"):
        value = redis_client.get(key)
        if value:
            documents.append(value)
    for key in redis_client.scan_iter(match=f"chat:{username}:*"):
        for message in redis_client.lrange(key, 0, -1):
            if message:
                documents.append(message)
    return documents


def _fallback_search(query: str, documents: Iterable[str]) -> str:
    query_lower = query.lower()
    matches: List[str] = []
    for doc in documents:
        for line in doc.splitlines():
            if query_lower in line.lower():
                matches.append(line.strip())
                if len(matches) >= 5:
                    break
        if len(matches) >= 5:
            break
    if matches:
        return "\n".join(matches)
    return "No matching entries found."


@router.post("/", response_model=SearchResult)
def search_diary(
    query: SearchQuery, username: str = Depends(get_current_user)
) -> SearchResult:
    documents = _collect_documents(username)
    if not documents:
        return SearchResult(query=query.query, answer="No diary content available yet.")

    joined_documents = "\n".join(documents)
    prompt = (
        "You are helping the user search through their personal diary. "
        "Respond with a concise answer that references the diary content when possible.\n"
        f"Diary content:\n{joined_documents}\n\n"
        f"Question: {query.query}\n"
        "Answer:"
    )
    answer = generate_summary(prompt)
    if not answer.strip():
        answer = _fallback_search(query.query, documents)
    return SearchResult(query=query.query, answer=answer.strip())
