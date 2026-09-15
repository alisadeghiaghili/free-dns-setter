"""
OS-level privilege utilities.
Kept separate so the rest of the project stays platform-agnostic.

  - Windows: UAC elevation (``ShellExecuteW`` + ``runas``)
  - Linux   : ``sudo``
  - macOS   : ``sudo`` (the ``networksetup`` backend requires root)
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


_IS_WIN = sys.platform == "win32"


# ── Windows helpers ──────────────────────────────────────────────────────────


def _win_is_admin() -> bool:
    import ctypes

    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _project_root() -> Path:
    # dns_changer/utils/privileges.py -> two levels up = project root
    return Path(__file__).resolve().parents[2]


def _entry_module() -> str:
    """
    Dotted entry-point module, e.g. "dns_changer.main" (GUI) or
    "dns_changer.cli.dns_cli" (CLI). Under ``python -m`` sys.argv[0] is the
    absolute path of that entry script, so convert it relative to the root.
    """
    root = _project_root()
    try:
        rel = Path(sys.argv[0]).resolve().relative_to(root)
        mod = ".".join(rel.with_suffix("").parts)
    except ValueError:
        return "dns_changer.main"
    # guard against argv[0] not being a real entry script (e.g. ``python -c``)
    return mod if mod.startswith("dns_changer.") else "dns_changer.main"


def _win_relaunch() -> None:
    """Re-launch the current program with UAC elevation and exit.

    - Frozen (PyInstaller .exe): re-launch the exe itself via ``runas``.
    - From source: re-run as a module (``python -m dns_changer.main``) with the
      working directory pinned to the project root, since re-running the entry
      file directly (``python main.py``) would break the package's relative imports.
    """
    import ctypes

    if getattr(sys, "frozen", False):
        # PyInstaller build — sys.executable IS the exe.
        # ShellExecuteW(hwnd, verb, lpFile, lpParameters, lpDir, nShowCmd)
        extra = " ".join(sys.argv[1:])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, extra, None, 1)
        sys.exit(0)

    root = _project_root()
    extra = " ".join(sys.argv[1:])
    args = f"-m {_entry_module()} {extra}".strip()
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{args}"', str(root), 1)
    sys.exit(0)


# ── Unix (Linux / macOS) helpers ─────────────────────────────────────────────


def _unix_is_root() -> bool:
    return os.geteuid() == 0 if hasattr(os, "geteuid") else False


def _unix_relaunch() -> None:
    """Re-launch the current program under ``sudo`` and exit.

    Three launch shapes must keep working, each re-invoked so that its package
    context (relative imports) is preserved:

    - Frozen binary (PyInstaller)   → ``sudo <the binary> [args]``
    - ``python -m dns_changer.X``    → ``sudo <python> -m dns_changer.X [args]``
    - Installed console script       → ``sudo <script path> [args]``
    """
    sudo = shutil.which("sudo") or "/usr/bin/sudo"

    if getattr(sys, "frozen", False):
        args = [sys.executable, *sys.argv[1:]]
    else:
        argv0 = sys.argv[0]
        if argv0.endswith(".py"):
            # ``python -m`` form — argv[0] is the entry module's file. Re-run as
            # a module so the package's relative imports survive.
            args = [sys.executable, "-m", _entry_module(), *sys.argv[1:]]
        else:
            # Console script (or any non-module entry) — re-run it as-is.
            args = [argv0, *sys.argv[1:]]

    os.execv(sudo, [sudo, *args])


# ── public API ───────────────────────────────────────────────────────────────


def is_admin() -> bool:
    """True when running with the elevated privileges the OS backend needs."""
    if _IS_WIN:
        return _win_is_admin()
    return _unix_is_root()


def relaunch_as_admin() -> None:
    """Re-launch the current program elevated, then exit."""
    if _IS_WIN:
        _win_relaunch()
    else:
        _unix_relaunch()


def ensure_admin() -> None:
    """Call at startup — re-launches elevated if not already privileged."""
    if not is_admin():
        relaunch_as_admin()
