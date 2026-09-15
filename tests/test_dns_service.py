"""Tests for dns_changer.core.dns_service — the state machine.

Only the adapter seam is mocked (read_dns / set_dns); everything else is real.
"""
from __future__ import annotations

import pytest

from dns_changer.core import dns_service as ds
from dns_changer.core.dns_service import DNSService, ServiceError
from dns_changer.core.providers import DNS_PROVIDERS


# ── initial state ────────────────────────────────────────────────────────────

def test_starts_idle_with_no_provider() -> None:
    s = DNSService()
    assert s.is_active is False
    assert s.active_provider is None


def test_current_dns_delegates_to_adapter(monkeypatch) -> None:
    monkeypatch.setattr(ds, "read_dns", lambda: ["1.2.3.4"])
    assert DNSService().current_dns() == ["1.2.3.4"]


def test_current_dns_empty_when_no_servers(monkeypatch) -> None:
    monkeypatch.setattr(ds, "read_dns", lambda: [])
    assert DNSService().current_dns() == []


def test_available_providers_is_the_catalog() -> None:
    assert DNSService.available_providers() is DNS_PROVIDERS


# ── activate ─────────────────────────────────────────────────────────────────

def test_activate_snapshots_then_applies_provider(monkeypatch) -> None:
    monkeypatch.setattr(ds, "read_dns", lambda: ["9.9.9.9"])
    calls: dict = {}

    def fake_set(servers):
        calls["servers"] = list(servers)
        return True

    monkeypatch.setattr(ds, "set_dns", fake_set)

    s = DNSService()
    s.activate("Shecan")

    assert s.is_active is True
    assert s.active_provider.name == "Shecan"
    # applied the provider's two public servers, in order
    assert calls["servers"] == ["178.22.122.100", "185.51.200.2"]


def test_activate_unknown_provider_raises() -> None:
    s = DNSService()
    with pytest.raises(ServiceError):
        s.activate("DoesNotExist")


def test_activate_failure_clears_snapshot_and_stays_idle(monkeypatch) -> None:
    monkeypatch.setattr(ds, "read_dns", lambda: ["1.1.1.1"])
    monkeypatch.setattr(ds, "set_dns", lambda servers: False)

    s = DNSService()
    with pytest.raises(ServiceError):
        s.activate("Google")

    assert s.is_active is False
    assert s.active_provider is None
    assert s._snapshot == []  # no dangling snapshot to revert to


# ── deactivate ───────────────────────────────────────────────────────────────

def test_deactivate_reverts_to_the_snapshot(monkeypatch) -> None:
    monkeypatch.setattr(ds, "read_dns", lambda: ["1.2.3.4"])
    applied: dict = {}

    def fake_set(servers):
        applied["servers"] = list(servers)
        return True

    monkeypatch.setattr(ds, "set_dns", fake_set)

    s = DNSService()
    s.activate("Shecan")
    s.deactivate()

    assert s.is_active is False
    assert s.active_provider is None
    # reverted to exactly what was captured before the activate
    assert applied["servers"] == ["1.2.3.4"]


def test_deactivate_failure_keeps_active_state(monkeypatch) -> None:
    monkeypatch.setattr(ds, "read_dns", lambda: ["1.2.3.4"])
    flag = {"ok": True}
    monkeypatch.setattr(ds, "set_dns", lambda servers: flag["ok"])

    s = DNSService()
    s.activate("Shecan")
    flag["ok"] = False
    with pytest.raises(ServiceError):
        s.deactivate()
    # a failed revert must NOT mark the app idle
    assert s.is_active is True
    assert s.active_provider.name == "Shecan"


def test_deactivate_when_idle_raises_without_talking_to_os(monkeypatch) -> None:
    called: list = []
    monkeypatch.setattr(ds, "set_dns", lambda servers: (called.append(servers), True)[1])

    s = DNSService()
    with pytest.raises(ServiceError):
        s.deactivate()
    # guard must short-circuit before touching the OS
    assert called == []
