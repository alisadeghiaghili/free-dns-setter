"""Test configuration.

Anchors pytest's rootdir at the repo root so ``import dns_changer`` resolves.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
