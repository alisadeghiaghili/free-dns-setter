"""Tests for dns_changer.ui.main_window — the Tkinter window.

A real Tk root is created per test and torn down afterwards, so the tests run
headlessly (no mainloop, no UAC). The service is a stub; the message box is
patched so nothing can pop a native dialog.
"""
from __future__ import annotations

import pytest
import tkinter as tk

import dns_changer.ui.main_window as main_window
from dns_changer.core import ServiceError
from dns_changer.core.providers import DNS_PROVIDERS


@pytest.fixture(scope="session", autouse=True)
def _prime_tcl():
    """Warm up the Tcl interpreter once so per-test Tk() roots are reliable.

    On some Tk installs the very first interpreter init (and rapid create/destroy
    of many roots in one process) can transiently fail to load the tk library;
    priming once here plus the retry in the ``win`` fixture makes this
    environment-independent.
    """
    for _ in range(3):
        try:
            root = tk.Tk()
            root.update_idletasks()
            root.destroy()
            break
        except Exception:
            continue


class FakeService:
    def __init__(self, dns=("1.2.3.4",), active=False, provider=None):
        self._dns = list(dns)
        self._active = active
        self._provider = provider
        self.calls: list = []

    def current_dns(self):
        return list(self._dns)

    @property
    def is_active(self):
        return self._active

    @property
    def active_provider(self):
        return self._provider

    def available_providers(self):
        return DNS_PROVIDERS

    def activate(self, key):
        self.calls.append(("activate", key))
        self._active = True
        self._provider = DNS_PROVIDERS[key]

    def deactivate(self):
        self.calls.append(("deactivate", None))
        self._active = False
        self._provider = None


@pytest.fixture
def win(monkeypatch):
    m = main_window.messagebox
    monkeypatch.setattr(m, "showwarning", lambda title, msg: None)
    last = None
    for _ in range(5):
        try:
            w = main_window.MainWindow(FakeService())
            break
        except tk.TclError as exc:  # transient Tcl init hiccup — retry
            last = exc
    else:
        raise last
    yield w
    w._close_dd()
    w._root.destroy()


def _select(win, key) -> None:
    """Move the dropdown to the row holding *key* (or None)."""
    for i, k in enumerate(win._keys):
        if k == key:
            win._set_dd_text(i)
            win._on_select()
            return
    raise AssertionError(f"key {key!r} not found in dropdown")


# ── construction & helpers ───────────────────────────────────────────────────


def test_builds_with_default_state(win) -> None:
    assert win._dd_index == 0
    assert win._keys[0] is None
    assert win._dd_win is None


def test_populate_lists_categories_and_providers(win) -> None:
    # every provider appears once, plus category headers plus the default row
    provider_names = [p.name for p in DNS_PROVIDERS.values()]
    assert all(n in win._dd_items for n in provider_names)
    assert "یک provider انتخاب کنید" in win._dd_items
    assert len(win._keys) == len(win._dd_items)


def test_set_dd_text_updates_entry(win) -> None:
    win._set_dd_text(1)
    assert win._dd_index == 1
    assert win._dd_entry.get() == win._dd_items[1]


def test_key_returns_matching_key(win) -> None:
    _select(win, "Shecan")
    assert win._key() == "Shecan"


def test_key_out_of_range_returns_none(win) -> None:
    win._dd_index = 9999
    assert win._key() is None


def test_set_dot_draws_oval(win) -> None:
    win._set_dot("#ff0000")
    # an oval item now exists on the canvas
    assert win._dot.find_all()


def test_btn_hover_disabled_is_noop(win) -> None:
    win._btn.config(state="disabled")
    win._btn_hover(True)  # must not raise while disabled


def test_warn_calls_messagebox(win, monkeypatch) -> None:
    from types import SimpleNamespace
    calls = []
    monkeypatch.setattr(main_window.messagebox, "showwarning",
                        lambda t, m: calls.append((t, m)))
    win._warn("hello")
    assert calls and calls[0][1] == "hello"


# ── dropdown open/close/pick ─────────────────────────────────────────────────


def test_open_and_close_dropdown(win) -> None:
    win._open_dd()
    assert win._dd_win is not None
    assert win._dd_list is not None
    win._close_dd()
    assert win._dd_win is None


def test_toggle_closes_when_open(win) -> None:
    win._open_dd()
    win._toggle_dd(None)
    assert win._dd_win is None


def test_toggle_opens_when_closed(win) -> None:
    win._toggle_dd(None)
    assert win._dd_win is not None


def test_pick_dd_with_int_index(win) -> None:
    # pick the first provider row (index 1 is a category header, find a real key)
    target = next(i for i, k in enumerate(win._keys) if k is not None)
    win._pick_dd(target)
    assert win._dd_index == target
    assert win._dd_win is None  # picking closes it


def test_pick_dd_with_event_object(win) -> None:
    class Event:
        y = 5
    target = next(i for i, k in enumerate(win._keys) if k is not None)
    win._open_dd()
    win._pick_dd(Event())  # uses listbox.nearest(event.y)
    assert win._dd_win is None


def test_pick_dd_ignores_bad_index(win) -> None:
    before = win._dd_index
    win._pick_dd(99999)  # out of range -> no change
    assert win._dd_index == before


# ── selection / toggle / refresh ─────────────────────────────────────────────


def test_on_select_disables_button_when_nothing_chosen(win) -> None:
    win._dd_index = 0
    win._on_select()
    assert win._btn.cget("state") == "disabled"
    assert win._desc_lbl.cget("text") == ""


def test_on_select_enables_button_and_shows_description(win) -> None:
    _select(win, "Cloudflare")
    assert win._btn.cget("state") == "normal"
    assert win._desc_lbl.cget("text")  # provider description shown


def test_on_select_deactivates_active_provider(win) -> None:
    svc = win._s
    svc._active = True
    svc._provider = DNS_PROVIDERS["Shecan"]
    _select(win, "Cloudflare")  # changing selection while active deactivates
    assert ("deactivate", None) in svc.calls


def test_on_toggle_activates_when_idle(win) -> None:
    _select(win, "Google")
    win._on_toggle()
    assert ("activate", "Google") in win._s.calls


def test_on_toggle_deactivates_when_active(win) -> None:
    win._s._active = True
    win._s._provider = DNS_PROVIDERS["Google"]
    _select(win, "Google")
    win._on_toggle()
    assert ("deactivate", None) in win._s.calls


def test_on_toggle_noop_when_no_selection(win) -> None:
    win._dd_index = 0
    win._on_toggle()
    assert win._s.calls == []


def test_on_toggle_surfaces_service_error(win, monkeypatch) -> None:
    def boom(key):
        raise ServiceError("nope")

    win._s.activate = boom
    monkeypatch.setattr(main_window.messagebox, "showwarning", lambda t, m: None)
    _select(win, "Google")
    win._on_toggle()  # must not raise


def test_refresh_shows_current_dns(win) -> None:
    win._s = FakeService(dns=("9.9.9.9",))
    win._refresh()
    assert "9.9.9.9" in win._dns_lbl.cget("text")


def test_refresh_automatic_when_no_dns(win) -> None:
    win._s = FakeService(dns=())
    win._refresh()
    assert "Automatic" in win._dns_lbl.cget("text")


def test_refresh_active_state(win) -> None:
    win._s = FakeService(active=True, provider=DNS_PROVIDERS["Shecan"])
    win._refresh()
    assert win._btn.cget("text").strip() == "Deactivate"


def test_refresh_inactive_no_selection(win) -> None:
    win._s = FakeService(dns=("1.1.1.1",))
    win._dd_index = 0
    win._refresh()
    assert win._btn.cget("text").strip() == "Activate"


def test_refresh_inactive_with_selection(win) -> None:
    win._s = FakeService(dns=("1.1.1.1",))
    _select(win, "Google")
    win._refresh()


def test_refresh_survives_dns_error(win) -> None:
    def boom():
        raise RuntimeError("wmi down")

    win._s = FakeService()
    win._s.current_dns = boom
    win._refresh()  # must not raise
    assert "Automatic" in win._dns_lbl.cget("text")


def test_run_enters_mainloop(win, monkeypatch) -> None:
    ran = []
    monkeypatch.setattr(win._root, "mainloop", lambda: ran.append(True))
    win.run()
    assert ran == [True]


def test_btn_hover_applies_color_when_enabled(win) -> None:
    win._btn.config(state="normal")
    win._btn_hover(True)
    assert win._btn.cget("bg") == main_window._ACCENT_H
    win._btn_hover(False)
    assert win._btn.cget("bg") == main_window._ACCENT


def test_on_select_deactivate_failure_surfaces_warning(win, monkeypatch) -> None:
    warned = []
    monkeypatch.setattr(main_window.messagebox, "showwarning", lambda t, m: warned.append(m))
    win._s._active = True
    win._s._provider = DNS_PROVIDERS["Shecan"]
    win._s.deactivate = lambda: (_ for _ in ()).throw(ServiceError("cannot revert"))
    _select(win, "Cloudflare")
    assert any("cannot revert" in m for m in warned)


def test_on_toggle_deactivate_failure_surfaces_warning(win, monkeypatch) -> None:
    warned = []
    monkeypatch.setattr(main_window.messagebox, "showwarning", lambda t, m: warned.append(m))
    win._s._active = True
    win._s._provider = DNS_PROVIDERS["Google"]
    win._s.deactivate = lambda: (_ for _ in ()).throw(ServiceError("cannot revert"))
    win._set_dd_text(win._dd_items.index("Google"))
    win._on_toggle()
    assert any("cannot revert" in m for m in warned)
