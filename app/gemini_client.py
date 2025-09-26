"""Utilities for interacting with the Gemini Generative AI API."""

from __future__ import annotations

import os

import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
)
REQUEST_TIMEOUT_SECONDS = 30


class GeminiClientError(RuntimeError):
    """Base exception for Gemini client errors."""


def _call_gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        raise GeminiClientError(
            "GEMINI_API_KEY is not configured; unable to call Gemini API."
        )

    body = {"contents": [{"parts": [{"text": prompt}]}]}
    params = {"key": GEMINI_API_KEY}

    try:
        response = requests.post(
            GEMINI_API_URL,
            params=params,
            json=body,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException as exc:  # pragma: no cover - network guard
        raise GeminiClientError("Failed to communicate with Gemini API") from exc

    try:
        payload = response.json()
        return payload["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError, ValueError) as exc:
        raise GeminiClientError("Unexpected Gemini API response structure") from exc


def generate_summary(prompt: str) -> str:
    """Generate a summary from Gemini or fall back to a basic heuristic.

    Parameters
    ----------
    prompt:
        The textual prompt describing what to summarise.
    """

    try:
        return _call_gemini(prompt)
    except GeminiClientError:
        # Provide a deterministic fallback so the app continues to function in
        # development or when the API is unreachable.
        snippet = prompt.strip().splitlines()
        snippet = " ".join(snippet[-5:]).strip()
        if not snippet:
            return "No content available to summarise."
        # Return the last few lines, truncated to a readable length.
        return snippet[:500]
