"""Tests for dns_changer.cli.dns_cli — the rich CLI.

The DNS service is a lightweight stub (the CLI only uses its public surface);
rich's ``console`` is swapped for a recording Console; ``ensure_admin`` and the
interactive ``Prompt.ask`` are monkeypatched so nothing blocks on input.
``sys.exit(1)`` naturally raises SystemExit, which the tests assert on.
"""
from __future__ import annotations

import io

import pytest
from rich.console import Console

import dns_changer.utils.privileges as privileges
import dns_changer.cli.dns_cli as dns_cli
from dns_changer.core import ServiceError
from dns_changer.core.providers import DNS_PROVIDERS


# ── stubs ────────────────────────────────────────────────────────────────────


class FakeService:
    def __init__(self, dns=None, active=False, provider=None):
        self._dns = list(dns or [])
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
def cap_console(monkeypatch):
    console = Console(record=True, file=io.StringIO(), width=200, height=100)
    monkeypatch.setattr(dns_cli, "console", console)
    return console


def _render(console: Console) -> str:
    return console.export_text()


def _drive_interactive(monkeypatch, choices):
    queue = list(choices)
    monkeypatch.setattr(
        dns_cli.Prompt, "ask",
        staticmethod(lambda *a, **k: queue.pop(0) if queue else "q"),
    )


# ── rendering helpers ────────────────────────────────────────────────────────


def test_dns_status_text_shows_servers() -> None:
    assert "1.2.3.4" in str(dns_cli._dns_status_text(FakeService(dns=["1.2.3.4"])))


def test_dns_status_text_automatic_when_empty() -> None:
    assert "Automatic" in str(dns_cli._dns_status_text(FakeService(dns=[])))


def test_active_panel_active() -> None:
    svc = FakeService(active=True, provider=DNS_PROVIDERS["Shecan"])
    assert dns_cli._active_panel(svc) is not None


def test_active_panel_idle() -> None:
    assert dns_cli._active_panel(FakeService()) is not None


def test_style_unknown_category_defaults() -> None:
    assert dns_cli._style(None) == ("white", "•")


def test_providers_table_lists_every_provider(cap_console) -> None:
    table = dns_cli._providers_table()
    c = io.StringIO()
    Console(file=c, width=200).print(table)
    rendered = c.getvalue()
    for name in DNS_PROVIDERS:
        assert name in rendered


# ── commands ─────────────────────────────────────────────────────────────────


def test_cmd_list_prints_all(cap_console) -> None:
    dns_cli.cmd_list(FakeService())
    out = _render(cap_console)
    for name in DNS_PROVIDERS:
        assert name in out


def test_cmd_status_active(cap_console) -> None:
    dns_cli.cmd_status(FakeService(active=True, provider=DNS_PROVIDERS["Google"]))
    assert "Google" in _render(cap_console)


def test_cmd_set_success(cap_console) -> None:
    svc = FakeService()
    dns_cli.cmd_set(svc, "Shecan")
    assert svc.calls == [("activate", "Shecan")]
    assert "Shecan" in _render(cap_console)


def test_cmd_set_by_display_name(cap_console) -> None:
    svc = FakeService()
    dns_cli.cmd_set(svc, "dns pro")  # lowercase display name should match
    assert svc.calls == [("activate", "DNS Pro")]


def test_cmd_set_unknown_exits(cap_console) -> None:
    with pytest.raises(SystemExit) as exc:
        dns_cli.cmd_set(FakeService(), "Nope")
    assert exc.value.code == 1


def test_cmd_set_failure_exits(cap_console) -> None:
    svc = FakeService()
    svc.activate = lambda key: (_ for _ in ()).throw(ServiceError("nope"))
    with pytest.raises(SystemExit):
        dns_cli.cmd_set(svc, "Shecan")


def test_cmd_reset_already_idle(cap_console) -> None:
    svc = FakeService()
    dns_cli.cmd_reset(svc)
    assert svc.calls == []
    assert "already" in _render(cap_console).lower()


def test_cmd_reset_success(cap_console) -> None:
    svc = FakeService(active=True, provider=DNS_PROVIDERS["Shecan"])
    dns_cli.cmd_reset(svc)
    assert svc.calls == [("deactivate", None)]


def test_cmd_reset_failure_exits(cap_console) -> None:
    svc = FakeService(active=True, provider=DNS_PROVIDERS["Shecan"])
    svc.deactivate = lambda: (_ for _ in ()).throw(ServiceError("nope"))
    with pytest.raises(SystemExit):
        dns_cli.cmd_reset(svc)


# ── interactive TUI ──────────────────────────────────────────────────────────


def test_interactive_quit(cap_console, monkeypatch) -> None:
    _drive_interactive(monkeypatch, ["q"])
    dns_cli.cmd_interactive(FakeService())
    assert "Goodbye" in _render(cap_console)


def test_interactive_set_by_number(cap_console, monkeypatch) -> None:
    _drive_interactive(monkeypatch, ["1", "q"])
    svc = FakeService()
    dns_cli.cmd_interactive(svc)
    assert any(c[0] == "activate" for c in svc.calls)


def test_interactive_reset(cap_console, monkeypatch) -> None:
    _drive_interactive(monkeypatch, ["r", "q"])
    svc = FakeService(active=True, provider=DNS_PROVIDERS["Shecan"])
    dns_cli.cmd_interactive(svc)
    assert any(c[0] == "deactivate" for c in svc.calls)


def test_interactive_unknown_option(cap_console, monkeypatch) -> None:
    _drive_interactive(monkeypatch, ["99", "q"])
    dns_cli.cmd_interactive(FakeService())
    assert "Unknown" in _render(cap_console)


# ── parser & main() ──────────────────────────────────────────────────────────


def test_build_parser_list() -> None:
    assert dns_cli.build_parser().parse_args(["list"]).command == "list"


def test_build_parser_set() -> None:
    args = dns_cli.build_parser().parse_args(["set", "Shecan"])
    assert args.command == "set" and args.provider == "Shecan"


def test_cli_main_runs_list(monkeypatch) -> None:
    monkeypatch.setattr(privileges, "ensure_admin", lambda: None)
    monkeypatch.setattr(dns_cli, "DNSService", lambda: FakeService())
    monkeypatch.setattr(dns_cli.sys, "argv", ["dns-changer", "list"])
    dns_cli.main()  # must not raise


def test_cli_main_dispatches_set(monkeypatch) -> None:
    svc = FakeService()
    monkeypatch.setattr(privileges, "ensure_admin", lambda: None)
    monkeypatch.setattr(dns_cli, "DNSService", lambda: svc)
    monkeypatch.setattr(dns_cli.sys, "argv", ["dns-changer", "set", "Google"])
    dns_cli.main()
    assert svc.calls == [("activate", "Google")]


def test_cli_main_interactive_when_no_command(monkeypatch) -> None:
    svc = FakeService()
    monkeypatch.setattr(privileges, "ensure_admin", lambda: None)
    monkeypatch.setattr(dns_cli, "DNSService", lambda: svc)
    monkeypatch.setattr(dns_cli.sys, "argv", ["dns-changer"])
    _drive_interactive(monkeypatch, ["q"])
    dns_cli.main()
