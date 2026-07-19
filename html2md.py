"""Load documents from file paths or URLs. Converts HTML to markdown via LLM.

PLACEHOLDER: Uses OpenRouter (inclusionai/ling-2.6-flash) for conversion. Should be
replaced with a proper HTML-to-markdown parser when the naive approach
becomes a bottleneck.
"""

import os
import re
from pathlib import Path

import httpx


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


def _resolve_github_wiki(url: str) -> str:
    """Convert a GitHub wiki URL to its raw markdown URL."""
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/wiki/([^#]+)(#.*)?$", url)
    if m:
        owner, repo, page, anchor = m.group(1), m.group(2), m.group(3).rstrip("/"), m.group(4) or ""
        return f"https://raw.githubusercontent.com/wiki/{owner}/{repo}/{page}.md{anchor}"
    return url


def _is_html(text: str) -> bool:
    return bool(re.search(r"(?i)<!DOCTYPE html|<html[^>]*>", text.strip()[:500]))


def _html_to_md(html: str) -> str:
    """Send HTML to OpenRouter (tencent/hy3:free) and return clean markdown."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set. Add OPENROUTER_API_KEY=your_key to .env or export it.")

    resp = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/RTFM-interactive",
        },
        json={
            "model": "inclusionai/ling-2.6-flash",
            "messages": [
                {"role": "system", "content": "Convert the following HTML documentation page to clean, well-structured Markdown. Preserve all meaningful content, headings, lists, code blocks, and links. Output only the Markdown, no commentary."},
                {"role": "user", "content": html},
            ],
            "temperature": 0.1,
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def load(source: str) -> str:
    """Load text from a file path or URL. Converts HTML to markdown if needed."""
    if source.startswith(("http://", "https://")):
        resp = httpx.get(_resolve_github_wiki(source), follow_redirects=True, timeout=30)
        resp.raise_for_status()
        text = resp.text
    else:
        text = Path(source).read_text(encoding="utf-8")
    if _is_html(text):
        text = _html_to_md(text)
    return text
