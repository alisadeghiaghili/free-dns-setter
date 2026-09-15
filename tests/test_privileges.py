"""Tests for dns_changer.utils.privileges — elevation logic.

Windows elevation is driven through a stubbed ``ctypes.windll``; the Unix
``sudo`` re-launch is driven through a recorder standing in for ``os.execv``
(the real one replaces the process and never returns).
"""
from __future__ import annotations

import ctypes
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import dns_changer.utils.privileges as privileges

ROOT = Path(__file__).resolve().parents[1]


_STATE: dict = {}


class _Shell32:
    """An instance of this is used as ``ctypes.windll.shell32``."""

    def IsUserAnAdmin(self):
        if _STATE["raise_exc"]:
            raise OSError("cannot query")
        return _STATE["admin"]

    def ShellExecuteW(self, *args):
        _STATE["calls"].append(args)


@pytest.fixture(autouse=True)
def state(monkeypatch):
    """Installs a stub ``ctypes.windll`` and yields the shared state dict."""
    _STATE.update(admin=True, raise_exc=False, calls=[])
    monkeypatch.setattr(ctypes, "windll", SimpleNamespace(shell32=_Shell32()))
    yield _STATE


def _set_frozen(monkeypatch, value: bool = True) -> None:
    monkeypatch.setattr(sys, "frozen", value, raising=False)


# ── is_admin (Windows branch) ────────────────────────────────────────────────


def test_win_is_admin_true() -> None:
    assert privileges._win_is_admin() is True


def test_win_is_admin_false(state) -> None:
    state["admin"] = False
    assert privileges._win_is_admin() is False


def test_win_is_admin_false_on_error(state) -> None:
    state["raise_exc"] = True
    assert privileges._win_is_admin() is False


def test_is_admin_windows_branch(monkeypatch, state) -> None:
    monkeypatch.setattr(privileges, "_IS_WIN", True)
    state["admin"] = True
    assert privileges.is_admin() is True
    state["admin"] = False
    assert privileges.is_admin() is False


def test_unix_is_root(monkeypatch) -> None:
    # os.geteuid does not exist on Windows, so setting it needs raising=False.
    monkeypatch.setattr(privileges.os, "geteuid", lambda: 0, raising=False)
    assert privileges._unix_is_root() is True
    monkeypatch.setattr(privileges.os, "geteuid", lambda: 1000, raising=False)
    assert privileges._unix_is_root() is False


def test_unix_is_root_without_geteuid(monkeypatch) -> None:
    # Simulate a platform that has no os.geteuid (e.g. Windows) by removing it.
    monkeypatch.delattr(privileges.os, "geteuid", raising=False)
    assert privileges._unix_is_root() is False


def test_is_admin_unix_branch(monkeypatch) -> None:
    monkeypatch.setattr(privileges, "_IS_WIN", False)
    monkeypatch.setattr(privileges.os, "geteuid", lambda: 0, raising=False)
    assert privileges.is_admin() is True
    monkeypatch.setattr(privileges.os, "geteuid", lambda: 1000, raising=False)
    assert privileges.is_admin() is False


def test_project_root_contains_package() -> None:
    assert (privileges._project_root() / "dns_changer").is_dir()


# ── _entry_module ────────────────────────────────────────────────────────────


def test_entry_module_gui(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", [str(ROOT / "dns_changer" / "main.py")])
    assert privileges._entry_module() == "dns_changer.main"


def test_entry_module_cli(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", [str(ROOT / "dns_changer" / "cli" / "dns_cli.py")])
    assert privileges._entry_module() == "dns_changer.cli.dns_cli"


def test_entry_module_outside_root_falls_back(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["/somewhere/else.py"])
    assert privileges._entry_module() == "dns_changer.main"


def test_entry_module_not_dns_changer_falls_back(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", [str(ROOT / "other_tool.py")])
    assert privileges._entry_module() == "dns_changer.main"


# ── Windows re-launch ────────────────────────────────────────────────────────


def test_win_relaunch_from_source(monkeypatch, state) -> None:
    _set_frozen(monkeypatch, False)
    monkeypatch.setattr(sys, "argv", [str(ROOT / "dns_changer" / "main.py"), "--flag"])
    with pytest.raises(SystemExit):
        privileges._win_relaunch()
    _, verb, lp_file, lp_params, lp_dir, _ = state["calls"][-1]
    assert verb == "runas"
    assert lp_file == sys.executable
    assert "-m dns_changer.main" in lp_params
    assert "--flag" in lp_params
    assert lp_dir == str(privileges._project_root())


def test_win_relaunch_frozen(monkeypatch, state) -> None:
    _set_frozen(monkeypatch, True)
    monkeypatch.setattr(sys, "argv", ["/app/app.exe", "arg1"])
    with pytest.raises(SystemExit):
        privileges._win_relaunch()
    _, verb, lp_file, lp_params, lp_dir, _ = state["calls"][-1]
    assert verb == "runas"
    assert lp_file == sys.executable
    assert lp_params == "arg1"
    assert lp_dir is None


# ── Unix re-launch ───────────────────────────────────────────────────────────


@pytest.fixture
def execv_recorder(monkeypatch):
    recorded: dict = {}

    def fake_execv(path, argv):
        recorded["path"] = path
        recorded["argv"] = list(argv)

    monkeypatch.setattr(privileges.os, "execv", fake_execv)
    return recorded


def test_unix_relaunch_module_form(execv_recorder, monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", [str(ROOT / "dns_changer" / "main.py"), "--x"])
    privileges._unix_relaunch()
    argv = execv_recorder["argv"]
    assert argv[0] == execv_recorder["path"]  # sudo is argv[0]
    assert argv[1] == sys.executable
    assert "-m" in argv and "dns_changer.main" in argv
    assert "--x" in argv


def test_unix_relaunch_console_script(execv_recorder, monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["/usr/local/bin/dns-changer"])
    privileges._unix_relaunch()
    argv = execv_recorder["argv"]
    assert argv[1] == "/usr/local/bin/dns-changer"
    assert "-m" not in argv


def test_unix_relaunch_frozen(execv_recorder, monkeypatch) -> None:
    _set_frozen(monkeypatch, True)
    monkeypatch.setattr(sys, "argv", ["/app/app"])
    privileges._unix_relaunch()
    argv = execv_recorder["argv"]
    assert argv[1] == sys.executable
    assert len(argv) == 2  # just sudo + executable, no extra args


# ── routing & ensure_admin ───────────────────────────────────────────────────


def test_relaunch_routes_to_win(monkeypatch) -> None:
    called = []
    monkeypatch.setattr(privileges, "_IS_WIN", True)
    monkeypatch.setattr(privileges, "_win_relaunch", lambda: called.append("win"))
    monkeypatch.setattr(privileges, "_unix_relaunch", lambda: called.append("unix"))
    privileges.relaunch_as_admin()
    assert called == ["win"]


def test_relaunch_routes_to_unix(monkeypatch) -> None:
    called = []
    monkeypatch.setattr(privileges, "_IS_WIN", False)
    monkeypatch.setattr(privileges, "_win_relaunch", lambda: called.append("win"))
    monkeypatch.setattr(privileges, "_unix_relaunch", lambda: called.append("unix"))
    privileges.relaunch_as_admin()
    assert called == ["unix"]


def test_ensure_admin_noop_when_admin(monkeypatch) -> None:
    called = []
    monkeypatch.setattr(privileges, "is_admin", lambda: True)
    monkeypatch.setattr(privileges, "relaunch_as_admin", lambda: called.append(1))
    privileges.ensure_admin()
    assert called == []


def test_ensure_admin_relaunches_when_not(monkeypatch) -> None:
    called = []
    monkeypatch.setattr(privileges, "is_admin", lambda: False)
    monkeypatch.setattr(privileges, "relaunch_as_admin", lambda: called.append(1))
    privileges.ensure_admin()
    assert called == [1]
