"""#75461: interrupt_debug.log is a persistent on-disk file, so a credential in a
steered/queued user message must never reach it verbatim.

Behavior contract, not a source-text check: drive the real write path with a
Telegram-token-shaped payload and assert the bytes that land in the file.
"""

import types
from pathlib import Path

from hermes_cli.cli_tui_mixin import CLITuiMixin

# Shape that triggered the original leak.
TOKEN = "1234567890:" + "A" * 35


def _run_busy_submit(tmp_path, monkeypatch, text):
    """Drive the legacy interrupt-queue branch of the busy-submit path."""
    import cli

    monkeypatch.setattr(cli, "_hermes_home", tmp_path)
    mixin = CLITuiMixin.__new__(CLITuiMixin)
    mixin.busy_input_mode = "interrupt"
    mixin.agent = types.SimpleNamespace()  # no redirect() -> legacy queue branch
    mixin._agent_running = True
    mixin._interrupt_queue = types.SimpleNamespace(
        put=lambda payload: None,
    )
    CLITuiMixin._tui_enter_while_busy(mixin, text, [], {"text": text})
    return Path(tmp_path) / "interrupt_debug.log"


def test_queued_interrupt_message_is_redacted_on_disk(tmp_path, monkeypatch):
    log = _run_busy_submit(tmp_path, monkeypatch, f"my key is {TOKEN}")

    assert log.exists()
    contents = log.read_text(encoding="utf-8")
    assert "A" * 35 not in contents
    assert "1234567890:***" in contents
