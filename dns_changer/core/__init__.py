"""Core business logic — no UI or OS-import side effects here."""

from .dns_service import DNSService, ServiceError, State
from .providers import DNSProvider, Category, DNS_PROVIDERS, providers_by_category

__all__ = [
    "DNSService",
    "ServiceError",
    "State",
    "DNSProvider",
    "Category",
    "DNS_PROVIDERS",
    "providers_by_category",
]
