"""Tests for dns_changer.core.providers — the data model.

The provider table is the app's core value; a wrong/private IP or a broken
category mapping silently breaks the whole tool. These tests pin that down.
"""
from __future__ import annotations

import ipaddress

import pytest

from dns_changer.core.providers import (
    Category,
    DNSProvider,
    DNS_PROVIDERS,
    providers_by_category,
)


# ── the data itself ──────────────────────────────────────────────────────────

def test_has_nine_verified_providers() -> None:
    assert len(DNS_PROVIDERS) == 9


def test_known_providers_present() -> None:
    for name in [
        "Shecan", "Begzar", "Electro", "HostIran",
        "AsiaTech", "Cloudflare", "Google", "Quad9", "DNS Pro",
    ]:
        assert name in DNS_PROVIDERS, f"missing provider: {name}"


@pytest.mark.parametrize("key", list(DNS_PROVIDERS))
def test_each_provider_is_well_formed(key: str) -> None:
    p = DNS_PROVIDERS[key]
    assert isinstance(p, DNSProvider)
    assert p.name
    assert p.description.strip(), f"{key} has an empty description"
    assert p.category in Category
    # both servers must be syntactically valid IPv4 and distinct
    assert ipaddress.IPv4Address(p.primary).is_global
    assert ipaddress.IPv4Address(p.secondary).is_global
    assert p.primary != p.secondary
    assert p.servers == [p.primary, p.secondary]
    assert str(p) == p.name


@pytest.mark.parametrize("key", list(DNS_PROVIDERS))
def test_no_private_or_reserved_addresses(key: str) -> None:
    """Regressions guard: a provider must never ship an RFC1918 / loopback /
    reserved address — that was the 403 / Radar Game bug."""
    for ip in (DNS_PROVIDERS[key].primary, DNS_PROVIDERS[key].secondary):
        addr = ipaddress.IPv4Address(ip)
        assert addr.is_global, f"{key} {ip} is not a public address"
        assert not addr.is_private
        assert not addr.is_loopback


def test_names_are_unique_keys() -> None:
    names = [p.name for p in DNS_PROVIDERS.values()]
    assert len(names) == len(set(names))
    # keys and display names should stay in sync
    assert set(DNS_PROVIDERS) == set(names)


# ── grouping ─────────────────────────────────────────────────────────────────

def test_providers_by_category_covers_all_categories() -> None:
    grouped = providers_by_category()
    assert set(grouped) == set(Category)


def test_every_provider_lands_in_exactly_one_bucket() -> None:
    grouped = providers_by_category()
    flat = [p for provs in grouped.values() for p in provs]
    assert len(flat) == len(DNS_PROVIDERS)
    assert {id(p) for p in flat} == {id(p) for p in DNS_PROVIDERS.values()}


def test_anti_filter_has_no_public_provider_yet() -> None:
    # Documented current state: no verified public anti-filter resolver.
    assert providers_by_category()[Category.ANTI_FILTER] == []


def test_grouped_entries_match_their_category() -> None:
    grouped = providers_by_category()
    for cat, provs in grouped.items():
        for p in provs:
            assert p.category is cat
