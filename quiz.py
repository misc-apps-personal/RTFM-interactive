"""Generate multiple-choice quizzes from a section of text using DeepSeek."""

import json
import os
from pathlib import Path

import httpx


API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"
PROMPT = """You are a quiz generator. Given a section of documentation, create a short multiple-choice quiz.

Return a JSON array of objects. Each object has:
- "question": string
- "choices": object with keys "A", "B", "C", "D" and string values
- "answer": one of "A", "B", "C", "D"

Generate exactly 3 questions. Only return valid JSON, no other text."""


def _load_env():
    """Load .env file from project root, if it exists."""
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_env()


def _call_api(text: str) -> str:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY not set. Add DEEPSEEK_API_KEY=your_key to .env or export it.")

    resp = httpx.post(
        API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": text},
            ],
            "temperature": 0.5,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def generate_quiz(text: str) -> list[dict]:
    """Generate quiz questions from section text. Returns list of question dicts."""
    raw = _call_api(text)
    # Strip markdown code fences if present
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0].strip()
    return json.loads(raw)
