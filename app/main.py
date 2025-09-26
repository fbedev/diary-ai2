"""FastAPI application bootstrap."""

from __future__ import annotations

from fastapi import FastAPI

from app import admin, auth, diary, search

app = FastAPI(title="Diary-AI2 Backend")

# Register routers
app.include_router(auth.router)
app.include_router(diary.router)
app.include_router(search.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return {"msg": "ChatDiary Pro backend running"}
