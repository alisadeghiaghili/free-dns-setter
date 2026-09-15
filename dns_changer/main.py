"""
Entry point (GUI).
  1. Ensure elevated privileges (Windows UAC / sudo on Linux & macOS).
  2. Instantiate DNSService.
  3. Pass service into MainWindow (Tkinter).
  4. Run the event loop.
"""

from .utils.privileges import ensure_admin
from .core import DNSService
from .ui import MainWindow


def main() -> None:
    ensure_admin()
    window = MainWindow(DNSService())
    window.run()


if __name__ == "__main__":
    main()
