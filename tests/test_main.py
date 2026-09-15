"""Tests for dns_changer.main — the GUI entry point (thin wiring)."""
from __future__ import annotations

import runpy
import warnings

import dns_changer.core as core_pkg
import dns_changer.ui as ui_pkg
import dns_changer.utils.privileges as privileges
import dns_changer.main as main_module


def test_main_ensures_admin_then_runs_window(monkeypatch) -> None:
    # main.py binds these names at import time, so patch them on main_module.
    seen: dict = {}

    class FakeWin:
        def __init__(self, service):
            seen["service"] = service

        def run(self):
            seen["ran"] = True

    monkeypatch.setattr(main_module, "ensure_admin", lambda: seen.setdefault("admin", True))
    monkeypatch.setattr(main_module, "MainWindow", FakeWin)
    monkeypatch.setattr(main_module, "DNSService", lambda: "SVC")

    main_module.main()

    assert seen["admin"] is True
    assert seen["service"] == "SVC"
    assert seen["ran"] is True


def test_main_guard_executes_when_run_as_module(monkeypatch) -> None:
    """Cover the ``if __name__ == "__main__": main()`` guard by actually running
    the module under its ``__main__`` name via runpy.

    The entry point imports ``ensure_admin``/``DNSService``/``MainWindow`` into
    its own namespace, so patching them in their source modules covers the
    freshly-executed module's imports too — without ever triggering UAC or a
    real Tk window.
    """
    seen: dict = {}

    class FakeWin:
        def __init__(self, service):
            seen["service"] = service

        def run(self):
            seen["ran"] = True

    # Patch in the namespaces main.py re-imports from (that's where the names
    # resolve at execution time, not in the leaf modules):
    #   ensure_admin <- dns_changer.utils.privileges
    #   DNSService   <- dns_changer.core  (core/__init__ re-exports it)
    #   MainWindow   <- dns_changer.ui    (ui/__init__ re-exports it)
    monkeypatch.setattr(privileges, "ensure_admin", lambda: seen.setdefault("admin", True))
    monkeypatch.setattr(core_pkg, "DNSService", lambda: "SVC")
    monkeypatch.setattr(ui_pkg, "MainWindow", FakeWin)

    # runpy warns that the module is already imported (expected — it is a
    # submodule of an already-imported package); it's harmless here.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        runpy.run_module("dns_changer.main", run_name="__main__")

    assert seen["admin"] is True
    assert seen["service"] == "SVC"
    assert seen["ran"] is True
