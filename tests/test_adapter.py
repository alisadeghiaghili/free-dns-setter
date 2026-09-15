"""Tests for dns_changer.core.adapter — the OS seam.

Every backend is exercised in isolation:
  - Windows : a stub ``wmi`` module injected into ``sys.modules``
  - Linux   : ``subprocess.run`` + ``shutil.which`` monkeypatched
  - macOS   : ``subprocess.run`` monkeypatched
Plus the public read_dns / set_dns dispatch.
"""
from __future__ import annotations

import sys
import types
from types import SimpleNamespace

import pytest

import dns_changer.core.adapter as adapter


# ── helpers ──────────────────────────────────────────────────────────────────


def _win_adapter(desc, gateway, dns, set_rc=0):
    a = SimpleNamespace(Description=desc, DefaultIPGateway=gateway,
                        DNSServerSearchOrder=dns)
    a.SetDNSServerSearchOrder = lambda servers: (set_rc, None, None)
    return a


@pytest.fixture
def fake_wmi(monkeypatch):
    """Install a stub ``wmi`` module; the inner callable sets its adapters."""
    box: dict = {"adapters": []}

    def _wmi_class():
        return SimpleNamespace(
            Win32_NetworkAdapterConfiguration=lambda **_kw: list(box["adapters"])
        )

    module = types.ModuleType("wmi")
    module.WMI = _wmi_class
    monkeypatch.setitem(sys.modules, "wmi", module)

    def _set(adapters):
        box["adapters"] = adapters

    return _set


def _run_fake(responses):
    """Build a fake subprocess.run keyed by a substring of the arg line."""
    calls: list[list[str]] = []

    def fake(args, **_kw):
        calls.append(list(args))
        line = " ".join(args)
        for key, (out, rc) in responses.items():
            if key in line:
                return SimpleNamespace(stdout=out, returncode=rc, stderr="")
        return SimpleNamespace(stdout="", returncode=0, stderr="")

    return fake, calls


# ── Windows (wmi) ────────────────────────────────────────────────────────────


def test_win_read_returns_active_adapter_dns(fake_wmi) -> None:
    fake_wmi([
        _win_adapter("Realtek GbE", "10.0.0.1", ("172.25.1.1", "172.25.1.2")),
    ])
    assert adapter._win_read() == ["172.25.1.1", "172.25.1.2"]


def test_win_read_empty_when_no_servers(fake_wmi) -> None:
    fake_wmi([_win_adapter("Realtek GbE", "10.0.0.1", None)])
    assert adapter._win_read() == []


def test_win_read_empty_when_no_adapters(fake_wmi) -> None:
    fake_wmi([])
    assert adapter._win_read() == []


def test_win_active_adapter_prefers_gateway_holder(fake_wmi) -> None:
    a = _win_adapter("first", None, None)
    b = _win_adapter("second", "192.168.1.1", ("9.9.9.9",))
    fake_wmi([a, b])
    # the gateway holder is picked even though it is not first
    assert adapter._wmi_active_adapter() is b


def test_win_active_adapter_falls_back_to_first(fake_wmi) -> None:
    a = _win_adapter("first", None, None)
    b = _win_adapter("second", None, None)
    fake_wmi([a, b])
    assert adapter._wmi_active_adapter() is a


def test_win_active_adapter_none_when_empty(fake_wmi) -> None:
    fake_wmi([])
    assert adapter._wmi_active_adapter() is None


def test_win_set_applies_to_all_and_reports_success(fake_wmi) -> None:
    seen: dict = {}

    def rec(servers):
        seen["servers"] = list(servers)
        return (0, None, None)

    a = _win_adapter("one", "10.0.0.1", None)
    a.SetDNSServerSearchOrder = rec
    fake_wmi([a])
    assert adapter._win_set(["1.1.1.1"]) is True
    assert seen["servers"] == ["1.1.1.1"]


def test_win_set_reports_failure_on_nonzero_return(fake_wmi) -> None:
    fake_wmi([_win_adapter("one", "10.0.0.1", None, set_rc=2)])
    assert adapter._win_set(["1.1.1.1"]) is False


def test_win_set_false_when_no_adapters(fake_wmi) -> None:
    fake_wmi([])
    assert adapter._win_set(["1.1.1.1"]) is False


# ── Linux (nmcli) ────────────────────────────────────────────────────────────


@pytest.fixture
def nmcli_present(monkeypatch):
    monkeypatch.setattr(adapter.shutil, "which", lambda name: "/usr/bin/" + name)


def test_linux_ensure_nmcli_raises_when_missing(monkeypatch) -> None:
    monkeypatch.setattr(adapter.shutil, "which", lambda name: None)
    with pytest.raises(adapter._Unsupported):
        adapter._linux_ensure_nmcli()


def test_linux_read_returns_active_explicit_dns(monkeypatch, nmcli_present) -> None:
    out = "wired1:enp3s0:dhcp\neth0:enp0s8:1.1.1.1,8.8.8.8\nwifi0:\n"
    fake, _ = _run_fake({"NAME,DEVICE,IP4.DNS": (out, 0)})
    monkeypatch.setattr(adapter.subprocess, "run", fake)
    assert adapter._linux_read() == ["1.1.1.1", "8.8.8.8"]


def test_linux_read_empty_when_only_automatic(monkeypatch, nmcli_present) -> None:
    out = "wired1:enp3s0:dhcp\nwired2:enp5s0:--\n"
    fake, _ = _run_fake({"NAME,DEVICE,IP4.DNS": (out, 0)})
    monkeypatch.setattr(adapter.subprocess, "run", fake)
    assert adapter._linux_read() == []


def test_linux_read_ignores_inactive_and_bad_lines(monkeypatch, nmcli_present) -> None:
    out = "wifi0::\nnot-a-row\nlo::--\n"
    fake, _ = _run_fake({"NAME,DEVICE,IP4.DNS": (out, 0)})
    monkeypatch.setattr(adapter.subprocess, "run", fake)
    assert adapter._linux_read() == []


def test_linux_set_applies_manual_dns(monkeypatch, nmcli_present) -> None:
    device_out = "eth0:ethernet:enp0s8\nwlp2s0:wifi:wlp2s0\n"
    fake, calls = _run_fake({"CONNECTION,TYPE,DEVICE": (device_out, 0)})
    monkeypatch.setattr(adapter.subprocess, "run", fake)

    assert adapter._linux_set(["1.1.1.1", "8.8.8.8"]) is True

    joined = [" ".join(c) for c in calls]
    assert any("connection modify eth0" in c for c in joined)
    assert any("ipv4.dns 1.1.1.1,8.8.8.8" in c for c in joined)
    assert any("ipv4.method manual" in c for c in joined)
    assert any("connection up eth0" in c for c in joined)


def test_linux_set_restores_auto_on_empty(monkeypatch, nmcli_present) -> None:
    device_out = "eth0:ethernet:enp0s8\n"
    fake, calls = _run_fake({"CONNECTION,TYPE,DEVICE": (device_out, 0)})
    monkeypatch.setattr(adapter.subprocess, "run", fake)

    assert adapter._linux_set([]) is True
    joined = [" ".join(c) for c in calls]
    assert any("ipv4.method auto" in c for c in joined)
    assert not any("ipv4.dns" in c for c in joined)


def test_linux_set_prefers_ethernet_connection(monkeypatch, nmcli_present) -> None:
    device_out = "wlp2s0:wifi:wlp2s0\neth0:ethernet:enp0s8\n"
    fake, calls = _run_fake({"CONNECTION,TYPE,DEVICE": (device_out, 0)})
    monkeypatch.setattr(adapter.subprocess, "run", fake)

    adapter._linux_set(["1.1.1.1"])
    joined = [" ".join(c) for c in calls]
    assert any("modify eth0" in c for c in joined)
    assert not any("modify wlp2s0" in c for c in joined)


def test_linux_set_false_when_no_active_connection(monkeypatch, nmcli_present) -> None:
    fake, calls = _run_fake({"CONNECTION,TYPE,DEVICE": ("", 0)})
    monkeypatch.setattr(adapter.subprocess, "run", fake)
    assert adapter._linux_set(["1.1.1.1"]) is False
    assert not any("modify" in " ".join(c) for c in calls)


def test_linux_set_false_when_modify_fails(monkeypatch, nmcli_present) -> None:
    device_out = "eth0:ethernet:enp0s8\n"
    fake, _ = _run_fake({
        "CONNECTION,TYPE,DEVICE": (device_out, 0),
        "modify": ("", 1),  # the modify step fails
    })
    monkeypatch.setattr(adapter.subprocess, "run", fake)
    assert adapter._linux_set(["1.1.1.1"]) is False


# ── macOS (networksetup / scutil) ────────────────────────────────────────────


def test_mac_read_parses_and_dedupes_nameservers(monkeypatch) -> None:
    out = (
        "DNS configuration for interfaces\n"
        "nameserver[0] : 1.1.1.1\n"
        "nameserver[1] : 1.1.1.1\n"
        "nameserver[2] : 8.8.8.8\n"
        "search domain[0] : lan\n"
    )
    fake, _ = _run_fake({"scutil --dns": (out, 0)})
    monkeypatch.setattr(adapter.subprocess, "run", fake)
    assert adapter._mac_read() == ["1.1.1.1", "8.8.8.8"]


def test_mac_read_empty_when_none(monkeypatch) -> None:
    fake, _ = _run_fake({"scutil --dns": ("DNS configuration\n", 0)})
    monkeypatch.setattr(adapter.subprocess, "run", fake)
    assert adapter._mac_read() == []


def test_mac_set_configures_en_services(monkeypatch) -> None:
    ports = (
        "Hardware Port: Ethernet\nDevice: en0\nEthernet Address: aa\n"
        "Hardware Port: Wi-Fi\nDevice: en1\nWi-Fi Hardware: AirPort\n"
        "Hardware Port: Thunderbolt Bridge\nDevice: bridge0\n"
    )
    fake, calls = _run_fake({"listallhardwareports": (ports, 0)})
    monkeypatch.setattr(adapter.subprocess, "run", fake)

    assert adapter._mac_set(["1.1.1.1", "8.8.8.8"]) is True
    joined = [" ".join(c) for c in calls]
    assert any("setdnsservers Ethernet 1.1.1.1 8.8.8.8" in c for c in joined)
    assert any("setdnsservers Wi-Fi 1.1.1.1 8.8.8.8" in c for c in joined)
    assert not any("bridge0" in c for c in joined)  # non-en device untouched


def test_mac_set_resets_on_empty(monkeypatch) -> None:
    ports = "Hardware Port: Ethernet\nDevice: en0\n"
    fake, calls = _run_fake({"listallhardwareports": (ports, 0)})
    monkeypatch.setattr(adapter.subprocess, "run", fake)

    assert adapter._mac_set([]) is True
    joined = [" ".join(c) for c in calls]
    assert any("setemptydnsservers Ethernet" in c for c in joined)


def test_mac_set_false_when_no_hardware(monkeypatch) -> None:
    ports = "Hardware Port: Loopback\nDevice: lo0\n"
    fake, _ = _run_fake({"listallhardwareports": (ports, 0)})
    monkeypatch.setattr(adapter.subprocess, "run", fake)
    assert adapter._mac_set(["1.1.1.1"]) is False


def test_mac_set_false_on_setdnsservers_failure(monkeypatch) -> None:
    ports = "Hardware Port: Ethernet\nDevice: en0\n"
    fake, _ = _run_fake({
        "listallhardwareports": (ports, 0),
        "setdnsservers": ("", 1),  # the configure step fails
    })
    monkeypatch.setattr(adapter.subprocess, "run", fake)
    assert adapter._mac_set(["1.1.1.1"]) is False


# ── public dispatch ──────────────────────────────────────────────────────────


def _pin(monkeypatch, platform: str) -> None:
    monkeypatch.setattr(adapter, "_IS_WIN", platform == "win32")
    monkeypatch.setattr(adapter, "_IS_MAC", platform == "darwin")
    monkeypatch.setattr(adapter, "_IS_LINUX", platform not in ("win32", "darwin"))


@pytest.mark.parametrize("platform", ["win32", "darwin", "linux"])
def test_read_dns_routes_by_platform(monkeypatch, platform) -> None:
    _pin(monkeypatch, platform)
    monkeypatch.setattr(adapter, "_win_read", lambda: "win")
    monkeypatch.setattr(adapter, "_mac_read", lambda: "mac")
    monkeypatch.setattr(adapter, "_linux_read", lambda: "linux")
    expected = {"win32": "win", "darwin": "mac", "linux": "linux"}[platform]
    assert adapter.read_dns() == expected


@pytest.mark.parametrize("platform", ["win32", "darwin", "linux"])
def test_set_dns_routes_by_platform(monkeypatch, platform) -> None:
    _pin(monkeypatch, platform)
    monkeypatch.setattr(adapter, "_win_set", lambda s: "win")
    monkeypatch.setattr(adapter, "_mac_set", lambda s: "mac")
    monkeypatch.setattr(adapter, "_linux_set", lambda s: "linux")
    expected = {"win32": "win", "darwin": "mac", "linux": "linux"}[platform]
    assert adapter.set_dns(["1.1.1.1"]) == expected
