"""PyInstaller entry point for the standalone .exe build.

Not part of the installed package — used only to drive the build.
"""
from dns_changer.main import main

if __name__ == "__main__":
    main()
