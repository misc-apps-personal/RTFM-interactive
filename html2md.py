"""Load documents from file paths or URLs. Converts HTML to markdown."""

import re
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify


_REMOVE_TAGS = {"script", "style", "nav", "footer", "noscript", "svg", "meta", "link", "iframe", "form", "button"}


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
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(_REMOVE_TAGS):
        tag.decompose()
    for a in soup.select("a.headerlink"):
        a.decompose()
    return markdownify(str(soup), heading_style="ATX", autolinks=False)


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
