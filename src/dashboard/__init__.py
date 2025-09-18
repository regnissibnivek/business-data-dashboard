"""Business data dashboard utilities."""
from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_ROOT.parent.parent / "data"

__all__ = ["DATA_DIR"]
