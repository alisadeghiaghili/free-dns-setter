"""
OS-level privilege utilities.
Kept separate so the rest of the project stays platform-agnostic.
"""

import sys
import ctypes
from pathlib import Path


def is_admin() -> bool:
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
    "dns_changer.cli.dns_cli" (CLI). Under `python -m`, sys.argv[0] is the
    absolute path of that entry script, so convert it relative to the root.
    """
    root = _project_root()
    try:
        rel = Path(sys.argv[0]).resolve().relative_to(root)
        mod = ".".join(rel.with_suffix("").parts)
    except ValueError:
        return "dns_changer.main"
    # guard against argv[0] not being a real entry script (e.g. `python -c`)
    return mod if mod.startswith("dns_changer.") else "dns_changer.main"


def relaunch_as_admin() -> None:
    """Re-launch the current program with UAC elevation and exit.

    - Frozen (PyInstaller .exe): re-launch the exe itself via "runas".
    - From source: re-run as a module (`python -m dns_changer.main`) with the
      working directory pinned to the project root, since re-running the entry
      file directly (python main.py) would break the package's relative imports.
    """
    if getattr(sys, "frozen", False):
        # PyInstaller build — sys.executable IS the exe.
        # ShellExecuteW(hwnd, verb, lpFile, lpParameters, lpDir, nShowCmd)
        # lpFile  = the exe; lpParameters = any CLI args (empty for GUI)
        extra = " ".join(sys.argv[1:])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, extra, None, 1)
        sys.exit(0)

    root = _project_root()
    extra = " ".join(sys.argv[1:])
    args = f"-m {_entry_module()} {extra}".strip()
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{args}"', str(root), 1)
    sys.exit(0)


def ensure_admin() -> None:
    """Call at startup — re-launches with elevation if not already admin."""
    if not is_admin():
        relaunch_as_admin()
