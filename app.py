"""RTFM-interactive: read manuals section by section in the terminal."""

import re
import sys
from urllib.parse import urljoin

from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Container
from textual.widgets import Static
from textual.binding import Binding

import quiz
from html2md import load


def _md_links_to_textual(text: str, base_url: str | None = None) -> str:
    """Convert markdown links:
    - Absolute URLs → [link=url]text[/link] (clickable)
    - Relative URLs → resolved against base_url, then clickable
    - Anchor-only links (#foo) → just text
    """
    def _replace(m: re.Match) -> str:
        text_label = m.group(1)
        url = m.group(2)
        if url.startswith("#"):
            return text_label
        if not url.startswith(("http://", "https://")) and base_url:
            url = urljoin(base_url, url)
        if url.startswith(("http://", "https://")):
            return f"[link={url}]{text_label}[/link]"
        return text_label

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _replace, text)


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
    CSS = """
    #layout { height: 100%; padding: 1 2; }
    #scroll { height: 1fr; }
    #counter { height: 1; text-align: center; }
    """

    BINDINGS = [
        Binding("n", "next", "Next"),
        Binding("p", "prev", "Previous"),
        Binding("q", "quit", "Quit"),
        Binding("z", "quiz", "Quiz"),
        Binding("a", "a", "A"),
        Binding("b", "b", "B"),
        Binding("c", "c", "C"),
        Binding("d", "d", "D"),
    ]

    def __init__(self, source: str):
        super().__init__()
        self.source = source
        self.sections = []
        self.idx = 0
        self.quiz_mode = False
        self.quiz_questions = []
        self.quiz_idx = 0
        self.quiz_answered = False

    def compose(self) -> ComposeResult:
        yield Container(
            VerticalScroll(Static("Loading...", id="view"), id="scroll"),
            Static("", id="counter"),
            id="layout",
        )

    def on_mount(self) -> None:
        text = load(self.source)
        self.sections = parse_sections(text)
        if self.sections:
            self.show(self.idx)

    def show(self, i: int) -> None:
        s = self.sections[i]
        base = self.source if self.source.startswith(("http://", "https://")) else None
        title = _md_links_to_textual(s['title'], base)
        body = _md_links_to_textual(s['body'], base)
        self.query_one("#view", Static).update(f"[bold]{title}[/bold]\n\n{body}")
        self.query_one(VerticalScroll).scroll_home(animate=False)
        self.query_one("#counter", Static).update(f"{i+1}/{len(self.sections)}")

    def _render_quiz(self) -> None:
        q = self.quiz_questions[self.quiz_idx]
        lines = [f"[bold]Quiz ({self.quiz_idx+1}/{len(self.quiz_questions)})[/bold]"]
        lines.append("")
        lines.append(q["question"])
        lines.append("")
        for letter in ["A", "B", "C", "D"]:
            if letter in q.get("choices", {}):
                prefix = ">" if self.quiz_answered else " "
                lines.append(f"  {prefix} {letter}) {q['choices'][letter]}")
        if self.quiz_answered:
            correct = q["answer"]
            lines.append("")
            if self.quiz_correct:
                lines.append("[green]Correct![/green]")
            else:
                lines.append(f"[red]Incorrect.[/red] Correct answer: {correct})")
            lines.append("")
            lines.append("Press [bold]n[/bold] for next question, [bold]z[/bold] to exit quiz")
        else:
            lines.append("")
            lines.append("Press [bold]a[/bold], [bold]b[/bold], [bold]c[/bold], or [bold]d[/bold] to answer")
        self.query_one("#view", Static).update("\n".join(lines))
        self.query_one("#counter", Static).update(f"{self.idx+1}/{len(self.sections)}")

    def action_quiz(self) -> None:
        if not self.sections:
            return
        if self.quiz_mode:
            self.quiz_mode = False
            self.show(self.idx)
            return
        self.notify("Generating quiz from current section...")
        try:
            s = self.sections[self.idx]
            self.quiz_questions = quiz.generate_quiz(f"# {s['title']}\n\n{s['body']}")
            self.quiz_mode = True
            self.quiz_idx = 0
            self.quiz_answered = False
            self.quiz_correct = False
            self._render_quiz()
        except Exception as e:
            self.notify(f"Quiz error: {e}", severity="error")

    def _answer_quiz(self, letter: str) -> None:
        if not self.quiz_mode or self.quiz_answered:
            return
        q = self.quiz_questions[self.quiz_idx]
        self.quiz_correct = letter.upper() == q["answer"]
        self.quiz_answered = True
        self._render_quiz()

    def action_a(self) -> None:
        self._answer_quiz("A")

    def action_b(self) -> None:
        self._answer_quiz("B")

    def action_c(self) -> None:
        self._answer_quiz("C")

    def action_d(self) -> None:
        self._answer_quiz("D")

    def action_next(self) -> None:
        if self.quiz_mode and self.quiz_answered:
            if self.quiz_idx < len(self.quiz_questions) - 1:
                self.quiz_idx += 1
                self.quiz_answered = False
                self._render_quiz()
            else:
                self.quiz_mode = False
                self.show(self.idx)
            return
        if self.idx < len(self.sections) - 1:
            self.idx += 1
            self.show(self.idx)

    def action_prev(self) -> None:
        if not self.quiz_mode and self.idx > 0:
            self.idx -= 1
            self.show(self.idx)


def main():
    if len(sys.argv) < 2:
        print("Usage: rtfm <file-or-url>", file=sys.stderr)
        sys.exit(1)
    RTFMApp(sys.argv[1]).run()


if __name__ == "__main__":
    main()
