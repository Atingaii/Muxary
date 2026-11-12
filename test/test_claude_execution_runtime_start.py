from __future__ import annotations

from provider_backends.claude.execution_runtime.start import looks_ready, send_prompt


def test_looks_ready_rejects_welcome_banner_without_prompt_shortcuts() -> None:
    text = """
╭─ Claude Code ────────────────────────────╮
│                                          │
│              Welcome back!               │
│                                          │
│                Sonnet 4.6                │
│            API Usage Billing             │
╰──────────────────────────────────────────╯
"""

    assert looks_ready(text) is False


def test_looks_ready_accepts_idle_prompt_with_shortcuts() -> None:
    text = """
╭─── Claude Code v2.1.89 ─────────────────╮
│               Welcome back!             │
╰─────────────────────────────────────────╯

───────────────────────────────────────────
❯
───────────────────────────────────────────
  ? for shortcuts
"""

    assert looks_ready(text) is True


def test_looks_ready_accepts_busy_prompt() -> None:
    text = """
❯ 1+1=

✽ Blanching…

───────────────────────────────────────────
❯
───────────────────────────────────────────
  esc to interrupt
"""

    assert looks_ready(text) is True


class _Backend:
    def __init__(self, pane_text: str) -> None:
        self.pane_text = pane_text
        self.keys: list[tuple[str, str]] = []
        self.sent: list[tuple[str, str]] = []

    def get_pane_content(self, pane_id: str, *, lines: int = 120) -> str:
        return self.pane_text

    def send_key(self, pane_id: str, key: str) -> bool:
        self.keys.append((pane_id, key))
        return True

    def send_text_to_pane(self, pane_id: str, text: str) -> None:
        self.sent.append((pane_id, text))


def test_send_prompt_clears_stale_claude_prompt_input_before_paste() -> None:
    backend = _Backend(
        """
───────────────────────────────────────────
❯ /tell
───────────────────────────────────────────
  ? for shortcuts
"""
    )

    send_prompt(backend, "%2", "CCB_REQ_ID: job_123\n\nhello")

    assert backend.keys == [("%2", "C-c"), ("%2", "Escape"), ("%2", "C-u")]
    assert backend.sent == [("%2", "CCB_REQ_ID: job_123\n\nhello")]


def test_send_prompt_does_not_clear_empty_claude_prompt_line() -> None:
    backend = _Backend(
        """
───────────────────────────────────────────
❯
───────────────────────────────────────────
  ? for shortcuts
"""
    )

    send_prompt(backend, "%2", "CCB_REQ_ID: job_123\n\nhello")

    assert backend.keys == []
    assert backend.sent == [("%2", "CCB_REQ_ID: job_123\n\nhello")]
