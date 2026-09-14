"""
Low-level WMI adapter operations.
All WMI calls are isolated here — nothing else in the project imports wmi.
"""

from __future__ import annotations
import wmi


_ADAPTER_KEYWORDS = ("Wireless", "Ethernet")


def _wmi_adapters() -> list:
    """Return all IP-enabled Wireless/Ethernet adapters."""
    c = wmi.WMI()
    return [
        a
        for a in c.Win32_NetworkAdapterConfiguration(IPEnabled=True)
        if a.Description and any(kw in a.Description for kw in _ADAPTER_KEYWORDS)
    ]


def read_dns() -> list[str]:
    """
    Return the current DNS servers from the first active adapter.
    Returns an empty list when the adapter is set to DHCP / no DNS found.
    """
    for adapter in _wmi_adapters():
        servers = adapter.DNSServerSearchOrder
        if servers:
            return [s for s in servers if s]
    return []


def set_dns(servers: list[str]) -> bool:
    """
    Apply *servers* to all active adapters.
    Pass an empty list to revert to DHCP automatic.
    Returns True on full success, False if any adapter call failed.
    """
    adapters = _wmi_adapters()
    if not adapters:
        return False

    success = True
    for adapter in adapters:
        result = adapter.SetDNSServerSearchOrder(servers or [])
        ret_code = result[0] if isinstance(result, (list, tuple)) else result
        if ret_code != 0:
            success = False

    return success
