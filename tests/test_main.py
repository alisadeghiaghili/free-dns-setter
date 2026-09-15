"""Tests for dns_changer.main — the GUI entry point (thin wiring)."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

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
