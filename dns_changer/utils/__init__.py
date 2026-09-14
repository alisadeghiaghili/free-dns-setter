"""OS-specific utilities (UAC elevation)."""

from .privileges import is_admin, ensure_admin, relaunch_as_admin

__all__ = ["is_admin", "ensure_admin", "relaunch_as_admin"]
