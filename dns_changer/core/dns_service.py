"""
DNS service — pure business logic, zero UI dependency.
Orchestrates adapter.py + providers.py and owns the application state.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto

from .providers import DNS_PROVIDERS, DNSProvider
from .adapter import read_dns, set_dns


class ServiceError(Exception):
    """Raised when a DNS operation cannot be completed."""


class State(Enum):
    IDLE = auto()  # no custom DNS active
    ACTIVE = auto()  # custom DNS is applied


@dataclass
class DNSService:
    _state: State = field(default=State.IDLE, init=False, repr=False)
    _snapshot: list[str] = field(default_factory=list, init=False, repr=False)
    _provider: DNSProvider | None = field(default=None, init=False, repr=False)

    # ---------------------------------------------------------------- queries

    @property
    def active_provider(self) -> DNSProvider | None:
        return self._provider

    @property
    def is_active(self) -> bool:
        return self._state is State.ACTIVE

    @staticmethod
    def current_dns() -> list[str]:
        """Current DNS servers as reported by the OS."""
        return read_dns()

    @staticmethod
    def available_providers() -> dict[str, DNSProvider]:
        return DNS_PROVIDERS

    # --------------------------------------------------------------- commands

    def activate(self, provider_name: str) -> None:
        """Apply DNS for *provider_name*. Raises ServiceError on failure."""
        provider = DNS_PROVIDERS.get(provider_name)
        if provider is None:
            raise ServiceError(f"Provider '{provider_name}' not found.")

        # snapshot before any change
        self._snapshot = read_dns()

        if not set_dns(provider.servers):
            self._snapshot = []
            raise ServiceError(
                "تغییر DNS با خطا مواجه شد.\nمطمئن شوید برنامه با دسترسی Administrator اجرا شده."
            )

        self._provider = provider
        self._state = State.ACTIVE

    def deactivate(self) -> None:
        """Revert to the DNS that was active before the last activate()."""
        if not set_dns(self._snapshot):
            raise ServiceError("بازگردانی DNS با خطا مواجه شد.")

        self._provider = None
        self._snapshot = []
        self._state = State.IDLE
