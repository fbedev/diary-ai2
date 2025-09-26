# Diary-AI2 Backend

This repository contains the FastAPI backend that powers **Diary-AI2**, an AI
assisted journaling application.  Users chat with the assistant throughout the
day and the backend stores each message in Redis, generates end-of-day diary
summaries and exposes APIs used by the Streamlit frontend.

## Features

- **Authentication** – User sign-up, login and logout using Redis-backed
  sessions.  Sessions are passed via `Authorization: Bearer <token>` headers.
- **Chat storage** – Every chat message is stored under the authenticated user
  and grouped by day.  Messages receive server-generated IDs and timestamps.
- **Automatic summarisation** – A dedicated endpoint generates AI-assisted
  summaries for each day's conversation, including mood, highlights and tags.
- **Search** – Search across stored chats and summaries, using Gemini when
  available with a graceful text-based fallback.
- **Admin utilities** – Lightweight dashboard endpoints to inspect users,
  sessions and message counts.

## Getting Started

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Provide environment variables (create a `.env` file for local development):

   ```env
   REDIS_URL=redis://localhost:6379/0
   GEMINI_API_KEY=your_api_key_here  # optional – the app falls back to local summarisation
   ```

3. Run the FastAPI server:

   ```bash
   uvicorn app.main:app --reload
   ```

4. Explore the interactive API documentation at `http://localhost:8000/docs`.

## Testing the Workflow

```bash
# Sign up and login
http --json POST :8000/auth/signup username=jane password=secret123
TOKEN=$(http --json POST :8000/auth/login username=jane password=secret123 | jq -r .token)

# Add a message
http --json POST :8000/diary/add \ \
  "Authorization:Bearer $TOKEN" text="Went for a long run and felt amazing" role=user

# Generate a summary for today
http --json POST :8000/diary/generate/$(date +%F) "Authorization:Bearer $TOKEN"
```

## Project Structure

```
app/
├── admin.py          # Admin dashboard endpoints
├── auth.py           # Authentication and session management
├── diary.py          # Chat storage and summarisation endpoints
├── gemini_client.py  # Gemini API integration with graceful fallback
├── main.py           # FastAPI application bootstrap
├── models.py         # Shared Pydantic models
└── redis_client.py   # Redis connection utilities
```

## License

MIT
