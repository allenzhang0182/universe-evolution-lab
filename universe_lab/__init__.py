"""Repository-root import shim for the src-layout package.

This keeps `python -m universe_lab.main` working from a fresh checkout without
requiring an editable install first. The implementation lives in src/universe_lab.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

_SRC_PACKAGE = Path(__file__).resolve().parent.parent / "src" / "universe_lab"
if _SRC_PACKAGE.is_dir():
    __path__.append(str(_SRC_PACKAGE))

__all__ = [
    "Civilization",
    "EmergentStructure",
    "Event",
    "Population",
    "SimulationConfig",
    "Species",
    "Universe",
]


def __getattr__(name: str) -> Any:
    if name in __all__:
        from . import models

        return getattr(models, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
