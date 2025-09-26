from fastapi import FastAPI
from app import auth, admin  # add diary, search later if they exist
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(title="ChatDiary Pro")

app.include_router(auth.router)
app.include_router(admin.router)

@app.get("/")
def root():
    return {"msg": "ChatDiary Pro backend running"}