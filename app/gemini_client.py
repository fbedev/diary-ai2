import os
import requests

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

def generate_summary(prompt: str) -> str:
    headers = {"Authorization": f"Bearer {GEMINI_API_KEY}"}
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    resp = requests.post(GEMINI_API_URL, headers=headers, json=body)
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]