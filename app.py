"""RTFM-interactive: read manuals section by section in the terminal."""

import re
import sys
from pathlib import Path

import httpx
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static
from textual.binding import Binding


def _resolve_github_wiki(url: str) -> str:
    """Convert a GitHub wiki URL to its raw markdown URL."""
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/wiki/([^#]+)(#.*)?$", url)
    if m:
        owner, repo, page, anchor = m.group(1), m.group(2), m.group(3).rstrip("/"), m.group(4) or ""
        return f"https://raw.githubusercontent.com/wiki/{owner}/{repo}/{page}.md{anchor}"
    return url


def load(source: str) -> str:
    """Load text from a file path or URL."""
    if source.startswith(("http://", "https://")):
        resp = httpx.get(_resolve_github_wiki(source), follow_redirects=True, timeout=30)
        resp.raise_for_status()
        return resp.text
    return Path(source).read_text(encoding="utf-8")


def parse_sections(text: str) -> list[dict]:
    """Split markdown into sections by headers."""
    sections = []
    prev = 0
    level, title = 0, "Preamble"
    for m in re.finditer(r"^(#{1,6})\s+(.+)$", text, re.MULTILINE):
        if prev:
            sections.append({"level": level, "title": title, "body": text[prev:m.start()].strip()})
        level, title, prev = len(m.group(1)), m.group(2), m.end()
    sections.append({"level": level, "title": title, "body": text[prev:].strip()})
    return sections


class RTFMApp(App):
    BINDINGS = [
        Binding("n", "next", "Next section"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, source: str):
        super().__init__()
        self.source = source
        self.sections = []
        self.idx = 0

    def compose(self) -> ComposeResult:
        yield VerticalScroll(Static("Loading...", id="view"))

    def on_mount(self) -> None:
        text = load(self.source)
        self.sections = parse_sections(text)
        if self.sections:
            self.show(self.idx)

    def show(self, i: int) -> None:
        s = self.sections[i]
        self.query_one("#view", Static).update(f"[bold]{s['title']}[/bold]\n\n{s['body']}")
        self.query_one(VerticalScroll).scroll_home(animate=False)

    def action_next(self) -> None:
        if self.idx < len(self.sections) - 1:
            self.idx += 1
            self.show(self.idx)


def main():
    if len(sys.argv) < 2:
        print("Usage: rtfm <file-or-url>", file=sys.stderr)
        sys.exit(1)
    RTFMApp(sys.argv[1]).run()


if __name__ == "__main__":
    main()
