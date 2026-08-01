"""Tests: Windows update does not cold-start a duplicate gateway when the
desktop app (``hermes serve``) is the runtime.

Regression coverage for #76129. The desktop app's backend runs
``python -m hermes_cli.main serve ...`` and hosts the gateway runtime itself,
but the update flow's strict gateway liveness matcher
(``looks_like_gateway_command_line``) only recognizes ``gateway run`` /
``gateway restart``. So when a vestigial autostart entry made
``gateway_windows.is_installed()`` true, every ``hermes update`` cold-started a
second standalone ``gateway run`` alongside the desktop backend — two daemons
racing on ports/state files and accumulating across updates.

The fix recognizes the desktop backend as gateway-equivalent at the two
cold-start decision points (the pre-update pause token and the post-update
spawn re-check) via ``_find_stale_dashboard_pids`` (the same ``serve`` /
``dashboard`` scan the dashboard-kill path uses). If a desktop backend is
already serving, no standalone gateway is spawned.
"""

from __future__ import annotations

from unittest.mock import patch

from hermes_cli import main as cli_main


def _stub_gateway_pids(monkeypatch, pids):
    """Make ``find_gateway_pids`` return *pids* (strict ``gateway run`` view)."""
    import hermes_cli.gateway as gateway_mod

    monkeypatch.setattr(gateway_mod, "find_gateway_pids", lambda **_k: list(pids))


def _stub_desktop_serve(monkeypatch, pids):
    """Make ``_find_stale_dashboard_pids`` return *pids* (desktop ``serve`` view)."""
    monkeypatch.setattr(
        cli_main,
        "_find_stale_dashboard_pids",
        lambda **_k: list(pids),
    )


# ---------------------------------------------------------------------------
# Pre-update pause token: cold_start_if_installed must NOT be set when a
# desktop backend is already serving.
# ---------------------------------------------------------------------------


@patch.object(cli_main, "_is_windows", return_value=True)
def test_pause_suppresses_cold_start_when_desktop_serving(_winp, monkeypatch):
    """A running ``hermes serve`` suppresses the autostart cold-start token."""
    import hermes_cli.gateway_windows as gw

    # No ``gateway run`` process, but an autostart entry is installed (the
    # lose condition from #76129) AND the desktop backend is up.
    _stub_gateway_pids(monkeypatch, [])
    _stub_desktop_serve(monkeypatch, [555])
    monkeypatch.setattr(gw, "is_installed", lambda *_a, **_k: True)

    token = cli_main._pause_windows_gateways_for_update()

    # The desktop app owns gateway lifecycle here — no cold-start requested.
    assert token is None


@patch.object(cli_main, "_is_windows", return_value=True)
def test_pause_still_cold_starts_when_no_desktop_serving(_winp, monkeypatch):
    """Without a desktop backend, the autostart cold-start token is preserved."""
    import hermes_cli.gateway_windows as gw

    _stub_gateway_pids(monkeypatch, [])
    _stub_desktop_serve(monkeypatch, [])
    monkeypatch.setattr(gw, "is_installed", lambda *_a, **_k: True)

    token = cli_main._pause_windows_gateways_for_update()

    assert token is not None
    assert token.get("resume_needed") is True
    assert token.get("cold_start_if_installed") is True


@patch.object(cli_main, "_is_windows", return_value=True)
def test_pause_no_cold_start_when_autostart_not_installed(_winp, monkeypatch):
    """No autostart entry and no desktop backend → nothing to resume."""
    import hermes_cli.gateway_windows as gw

    _stub_gateway_pids(monkeypatch, [])
    _stub_desktop_serve(monkeypatch, [])
    monkeypatch.setattr(gw, "is_installed", lambda *_a, **_k: False)

    token = cli_main._pause_windows_gateways_for_update()

    assert token is None


# ---------------------------------------------------------------------------
# Post-update cold-start spawn: must NOT spawn when a desktop backend is
# already serving.
# ---------------------------------------------------------------------------


@patch.object(cli_main, "_is_windows", return_value=True)
def test_cold_start_skips_spawn_when_desktop_serving(_winp, monkeypatch):
    """The post-update spawn is suppressed when ``hermes serve`` survived."""
    import hermes_cli.gateway_windows as gw

    _stub_gateway_pids(monkeypatch, [])
    _stub_desktop_serve(monkeypatch, [555])

    spawned = []
    monkeypatch.setattr(gw, "_spawn_detached", lambda *_a, **_k: spawned.append(1) or 999)

    cli_main._cold_start_windows_gateway_after_update()

    assert spawned == []  # no duplicate gateway spawned


@patch.object(cli_main, "_is_windows", return_value=True)
def test_cold_start_skips_spawn_when_gateway_run_already_up(_winp, monkeypatch):
    """Existing pre-spawn guard still fires: a live ``gateway run`` blocks spawn."""
    import hermes_cli.gateway_windows as gw

    # A real gateway is already up (e.g. autostart entry fired during pause).
    _stub_gateway_pids(monkeypatch, [4242])
    _stub_desktop_serve(monkeypatch, [])

    spawned = []
    monkeypatch.setattr(gw, "_spawn_detached", lambda *_a, **_k: spawned.append(1) or 999)

    cli_main._cold_start_windows_gateway_after_update()

    assert spawned == []


@patch.object(cli_main, "_is_windows", return_value=True)
def test_cold_start_spawns_when_nothing_serving(_winp, monkeypatch, capsys):
    """No gateway and no desktop backend → spawn proceeds (preserved behavior)."""
    import hermes_cli.gateway_windows as gw

    _stub_gateway_pids(monkeypatch, [])
    _stub_desktop_serve(monkeypatch, [])

    monkeypatch.setattr(gw, "_spawn_detached", lambda *_a, **_k: 31337)

    cli_main._cold_start_windows_gateway_after_update()

    assert "Starting Windows gateway after update (PID 31337)" in capsys.readouterr().out
