"""JSON storage for universe runs."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .models import Event, Universe, new_id, utc_now


DEFAULT_RUN_DIR = Path("data/runs")


def default_run_path(name: str) -> Path:
    return DEFAULT_RUN_DIR / f"{slugify(name)}.json"


def save_universe(universe: Universe, path: str | Path | None = None) -> Path:
    resolved = Path(path) if path is not None else default_run_path(universe.name)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    universe.updated_at = utc_now()
    with resolved.open("w", encoding="utf-8") as handle:
        json.dump(universe.to_dict(), handle, indent=2, sort_keys=True)
        handle.write("\n")
    return resolved


def load_universe(path: str | Path) -> Universe:
    resolved = Path(path)
    with resolved.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Run file {resolved} does not contain a JSON object")
    return Universe.from_dict(data)


def branch_universe(
    source_path: str | Path,
    new_name: str,
    target_path: str | Path | None = None,
) -> tuple[Universe, Path]:
    source = load_universe(source_path)
    branch = Universe.from_dict(source.to_dict())
    branch.id = new_id("uni")
    branch.name = new_name
    branch.config.name = new_name
    branch.branch_of = source.id
    branch.created_at = utc_now()
    branch.updated_at = branch.created_at
    branch.events.append(
        Event(
            year=branch.age,
            type="branch_created",
            title="Branch Created",
            description=f"Branch '{new_name}' copied from '{source.name}'.",
            impact={"source_id": source.id},
            target_kind="universe",
            target_id=branch.id,
        )
    )
    resolved = save_universe(branch, target_path or default_run_path(new_name))
    return branch, resolved


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_.-]+", "-", value.strip().lower()).strip("-")
    return slug or "run"
