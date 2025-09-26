from fastapi import FastAPI
from app import auth, diary, search, admin

app = FastAPI(title="ChatDiary Pro")

# Register routers
app.include_router(auth.router)
app.include_router(diary.router)
app.include_router(search.router)
app.include_router(admin.router)

@app.get("/")
def root():
    return {"msg": "ChatDiary Pro backend running"}