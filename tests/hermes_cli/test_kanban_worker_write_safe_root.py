"""Tests: kanban worker spawn scopes HERMES_WRITE_SAFE_ROOT to the task workspace.

Regression coverage for #70688: ``_default_spawn`` pinned ``TERMINAL_CWD`` to
the task workspace (the #41312 / #34619 fixes) but left
``HERMES_WRITE_SAFE_ROOT`` untouched, so every worker inherited the
deployment-wide value the dispatcher process happened to export. That value is
either too narrow (the Docker ``/opt/data`` default blocks legitimate writes
inside the task's own workspace) or too wide (a worker can write into a
*sibling* task's workspace). The fix scopes the file-tool sandbox to the
worker's own workspace, failing closed on degenerate paths.
"""

from __future__ import annotations

import os
import subprocess


def _make_task(kb, *, assignee: str = "w"):
    return kb.Task(
        id="t_wsr",
        title="write safe root",
        body=None,
        assignee=assignee,
        status="running",
        priority=0,
        created_by="test",
        created_at=1,
        started_at=None,
        completed_at=None,
        workspace_kind="dir",
        workspace_path=None,
        claim_lock="lock",
        claim_expires=None,
        tenant=None,
        current_run_id=1,
    )


def _capture_spawn_env(kb, monkeypatch, workspace: str) -> dict:
    monkeypatch.setattr(kb, "_resolve_hermes_argv", lambda: ["hermes"])

    captured: dict = {}

    class FakeProc:
        pid = 4242

    def fake_popen(cmd, *args, **kwargs):
        captured["cmd"] = list(cmd)
        captured["env"] = dict(kwargs.get("env") or {})
        captured["cwd"] = kwargs.get("cwd")
        return FakeProc()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    kb._default_spawn(_make_task(kb), workspace)
    return captured


def _setup_profile(monkeypatch, tmp_path):
    root = tmp_path / ".hermes"
    (root / "profiles" / "w").mkdir(parents=True)
    (root / "profiles" / "w" / "config.yaml").write_text(
        "toolsets:\n  - kanban\n", encoding="utf-8"
    )
    root.joinpath("config.yaml").write_text(
        "toolsets:\n  - kanban\n", encoding="utf-8"
    )
    monkeypatch.setenv("HERMES_HOME", str(root))
    from hermes_cli import kanban_db as kb

    return kb


def test_write_safe_root_scoped_to_workspace(monkeypatch, tmp_path):
    """A real, absolute workspace dir is scoped as HERMES_WRITE_SAFE_ROOT."""
    kb = _setup_profile(monkeypatch, tmp_path)
    workspace = tmp_path / "ws"
    workspace.mkdir()

    captured = _capture_spawn_env(kb, monkeypatch, str(workspace))

    assert "HERMES_WRITE_SAFE_ROOT" in captured["env"]
    assert captured["env"]["HERMES_WRITE_SAFE_ROOT"] == os.path.realpath(str(workspace))
    # TERMINAL_CWD and the safe root derive from the same normalized workspace.
    assert captured["env"]["TERMINAL_CWD"] == str(workspace)


def test_write_safe_root_not_set_for_nonexistent_workspace(monkeypatch, tmp_path):
    """A workspace path that isn't an existing dir must not widen the sandbox.

    Fail closed: leave the inherited HERMES_WRITE_SAFE_ROOT rather than
    exporting a meaningless one (mirrors the TERMINAL_CWD guard).
    """
    kb = _setup_profile(monkeypatch, tmp_path)
    workspace = tmp_path / "does-not-exist"

    captured = _capture_spawn_env(kb, monkeypatch, str(workspace))

    assert "HERMES_WRITE_SAFE_ROOT" not in captured["env"]
    # TERMINAL_CWD is equally absent for a non-dir workspace.
    assert "TERMINAL_CWD" not in captured["env"]


def test_write_safe_root_not_set_for_relative_workspace(monkeypatch, tmp_path):
    """A relative workspace must not be exported as a safe root."""
    kb = _setup_profile(monkeypatch, tmp_path)

    captured = _capture_spawn_env(kb, monkeypatch, "relative/ws")

    assert "HERMES_WRITE_SAFE_ROOT" not in captured["env"]


def test_write_safe_root_replaces_inherited_value(monkeypatch, tmp_path):
    """The task workspace replaces — not appends — the inherited safe root.

    The dispatcher's deployment-wide root is intentionally dropped so a
    confused/compromised worker cannot write into a sibling task's workspace.
    """
    kb = _setup_profile(monkeypatch, tmp_path)
    workspace = tmp_path / "ws"
    workspace.mkdir()
    # Simulate the dispatcher's inherited deployment-wide root.
    monkeypatch.setenv("HERMES_WRITE_SAFE_ROOT", str(tmp_path))

    captured = _capture_spawn_env(kb, monkeypatch, str(workspace))

    # Replaced by the narrow task-scoped root, not the inherited wide one.
    assert captured["env"]["HERMES_WRITE_SAFE_ROOT"] == os.path.realpath(str(workspace))
    assert captured["env"]["HERMES_WRITE_SAFE_ROOT"] != str(tmp_path)
