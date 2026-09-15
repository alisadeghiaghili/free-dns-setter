"""
OS-level DNS adapter.

This is the ONLY module that talks to the operating system. It exposes two
functions — :func:`read_dns` and :func:`set_dns` — and delegates to a small
per-platform backend. Nothing else in the project imports ``wmi``, ``subprocess``
or any platform-specific tooling; they all live behind this seam.

Backends
--------
- Windows  → WMI (``Win32_NetworkAdapterConfiguration``)
- Linux    → NetworkManager (``nmcli``), the default on Ubuntu/Debian
- macOS    → ``networksetup`` (system-bundled)
"""

from __future__ import annotations

import shutil
import subprocess
import sys

__all__ = ["read_dns", "set_dns"]


# ── dispatch ─────────────────────────────────────────────────────────────────

_IS_WIN = sys.platform == "win32"
_IS_MAC = sys.platform == "darwin"
_IS_LINUX = not _IS_WIN and not _IS_MAC


# ── Windows (WMI) ────────────────────────────────────────────────────────────

def _wmi_ip_enabled():
    """All IP-enabled network adapters (WMI)."""
    import wmi  # Windows-only dependency, imported lazily

    return list(wmi.WMI().Win32_NetworkAdapterConfiguration(IPEnabled=True))


def _wmi_active_adapter():
    """The adapter actually routing traffic — the one holding the default
    gateway. This is robust regardless of how the adapter names itself (e.g.
    "Realtek GbE", "Intel I219", vendor-specific), unlike a keyword match on
    the Description string. Falls back to the first IP-enabled adapter."""
    adapters = _wmi_ip_enabled()
    for adapter in adapters:
        if adapter.DefaultIPGateway:
            return adapter
    return adapters[0] if adapters else None


def _win_read() -> list[str]:
    adapter = _wmi_active_adapter()
    if adapter is None:
        return []
    servers = adapter.DNSServerSearchOrder
    return [s for s in servers if s] if servers else []


def _win_set(servers: list[str]) -> bool:
    adapters = _wmi_ip_enabled()
    if not adapters:
        return False
    success = True
    for adapter in adapters:
        result = adapter.SetDNSServerSearchOrder(servers or [])
        ret_code = result[0] if isinstance(result, (list, tuple)) else result
        if ret_code != 0:
            success = False
    return success


# ── Linux (NetworkManager / nmcli) ───────────────────────────────────────────


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        args, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )


def _linux_ensure_nmcli() -> None:
    if shutil.which("nmcli") is None:
        raise _Unsupported(
            "nmcli not found. This requires NetworkManager (default on Ubuntu/Debian).\n"
            "Install it with:  sudo apt install network-manager"
        )


def _linux_read() -> list[str]:
    """
    Read the DNS servers actually in use. Uses ``nmcli ... connection show``
    over *active* connections only: a connection is active when its DEVICE
    field is non-empty, and ``IP4.DNS`` is ``dhcp``/``--`` when no explicit
    servers are set (i.e. the system is on automatic).
    """
    _linux_ensure_nmcli()
    out = _run(["nmcli", "-t", "-f", "NAME,DEVICE,IP4.DNS", "connection", "show"])
    for line in out.stdout.splitlines():
        parts = line.split(":", 2)
        if len(parts) != 3:
            continue
        _name, device, dns_field = (p.strip() for p in parts)
        if not device:
            continue  # not an active (device-bound) connection
        if not dns_field or dns_field in ("--", "dhcp"):
            continue  # automatic / no explicit DNS
        return [s for s in dns_field.split(",") if s]
    return []


def _linux_set(servers: list[str]) -> bool:
    """
    Apply *servers* to the primary IPv4 connection via NetworkManager.
    An empty list restores automatic (DHCP) resolution.
    Returns True on success, False on any nmcli failure.
    """
    _linux_ensure_nmcli()
    out = _run(["nmcli", "-t", "-f", "CONNECTION,TYPE,DEVICE", "device"])
    active = [
        line
        for line in out.stdout.splitlines()
        if line.split(":")[0].strip() and "disconnected" not in line
    ]
    if not active:
        return False

    # Prefer a wired/connected connection; the first connected one is used.
    conn_field = active[0].split(":")[0].strip()
    for line in active:
        fields = line.split(":")
        if len(fields) >= 2 and fields[1] == "ethernet" and fields[0].strip():
            conn_field = fields[0].strip()
            break

    if servers:
        result = _run(
            ["nmcli", "connection", "modify", conn_field,
             f"ipv4.dns", ",".join(servers), "ipv4.method", "manual"]
        )
    else:
        result = _run(
            ["nmcli", "connection", "modify", conn_field, "ipv4.method", "auto"]
        )
    if result.returncode != 0:
        return False

    # Apply the change without dropping the connection when possible.
    _run(["nmcli", "connection", "up", conn_field])
    return True


# ── macOS (networksetup) ─────────────────────────────────────────────────────


def _mac_read() -> list[str]:
    """
    Read the DNS servers currently in effect for macOS. ``networksetup`` has no
    direct "get DNS" on every release, so we resolve the machine's current DNS
    by asking the system what it is using via ``scutil``.
    """
    out = _run(["scutil", "--dns"])
    servers: list[str] = []
    for line in out.stdout.splitlines():
        if line.startswith("nameserver["):
            parts = line.split(":", 1)
            if len(parts) == 2:
                value = parts[1].strip()
                if value and value not in servers:
                    servers.append(value)
    return servers


def _mac_set(servers: list[str]) -> bool:
    """
    Apply *servers* to every hardware service (Ethernet + Wi-Fi) that
    ``networksetup`` can see. Returns True on success, False on any failure.
    """
    out = _run(["networksetup", "-listallhardwareports"])
    services: list[str] = []
    current: str | None = None
    for line in out.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("Hardware Port:"):
            current = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("Device:"):
            device = stripped.split(":", 1)[1].strip()
            # Skip loopback / software-only devices; only manage real hardware.
            if current and device.startswith(("en", "eth")) and current != "Loopback":
                services.append(current)
            current = None
    if not services:
        return False

    ok = True
    for service in services:
        if servers:
            result = _run(
                ["networksetup", "-setdnsservers", service, *servers]
            )
        else:
            result = _run(["networksetup", "-setemptydnsservers", service])
        if result.returncode != 0:
            ok = False
    return ok


# ── public API ───────────────────────────────────────────────────────────────


class _Unsupported(RuntimeError):
    """Raised when a platform dependency is missing or unusable."""


def read_dns() -> list[str]:
    """Current DNS servers, or an empty list when the OS uses automatic DNS."""
    if _IS_WIN:
        return _win_read()
    if _IS_MAC:
        return _mac_read()
    return _linux_read()


def set_dns(servers: list[str]) -> bool:
    """
    Apply *servers* to the system. An empty list restores automatic/DHCP DNS.
    Returns True on success, False on failure.
    """
    if _IS_WIN:
        return _win_set(servers)
    if _IS_MAC:
        return _mac_set(servers)
    return _linux_set(servers)
