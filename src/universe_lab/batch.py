"""Batch run and aggregate summary helpers."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .modes import create_universe
from .reporting import build_stats
from .simulator import step_universe
from .storage import DEFAULT_RUN_DIR, load_universe, save_universe


@dataclass
class BatchRunResult:
    name: str
    mode: str
    age: int
    active_species: int
    active_civilizations: int
    events_total: int
    path: Path


def run_batch(
    mode: str,
    count: int,
    steps: int,
    prefix: str,
    run_dir: str | Path = DEFAULT_RUN_DIR,
) -> list[BatchRunResult]:
    if count <= 0:
        raise ValueError("count must be greater than 0")
    if steps < 0:
        raise ValueError("steps must be zero or greater")

    output_dir = Path(run_dir)
    results = []
    for index in range(1, count + 1):
        name = f"{prefix}_{index:03d}"
        universe = create_universe(mode, name)
        if steps:
            step_universe(universe, steps)
        path = save_universe(universe, output_dir / f"{name}.json")
        stats = build_stats(universe)
        results.append(
            BatchRunResult(
                name=name,
                mode=mode,
                age=universe.age,
                active_species=stats["species_active"],
                active_civilizations=stats["civilizations_active"],
                events_total=stats["events_total"],
                path=path,
            )
        )
    return results


def format_batch_results(results: list[BatchRunResult]) -> str:
    lines = [f"Batch created {len(results)} runs:"]
    for result in results:
        lines.append(
            "- "
            f"{result.name} | mode={result.mode} | age={result.age} | "
            f"active_species={result.active_species} | "
            f"active_civilizations={result.active_civilizations} | "
            f"events={result.events_total}"
        )
    return "\n".join(lines)


def summarize_run_directory(run_dir: str | Path, prefix: str) -> dict[str, Any]:
    directory = Path(run_dir)
    records = _load_records(directory, prefix)
    if not records:
        return {
            "prefix": prefix,
            "run_dir": str(directory),
            "runs_count": 0,
            "modes_involved": [],
            "average_age": 0.0,
            "average_active_species": 0.0,
            "total_extinct_species": 0,
            "average_species_population": 0.0,
            "runs_with_active_civilizations": 0,
            "average_active_civilizations": 0.0,
            "total_collapsed_civilizations": 0,
            "average_events_per_run": 0.0,
            "event_counts_by_type": {},
            "interesting_runs": {},
        }

    event_counts = Counter()
    for record in records:
        event_counts.update(record["stats"]["events_count_by_type"])

    return {
        "prefix": prefix,
        "run_dir": str(directory),
        "runs_count": len(records),
        "modes_involved": sorted({record["mode"] for record in records}),
        "average_age": _round2(_average(record["age"] for record in records)),
        "average_active_species": _round2(
            _average(record["stats"]["species_active"] for record in records)
        ),
        "total_extinct_species": sum(
            record["stats"]["species_extinct"] for record in records
        ),
        "average_species_population": _round2(
            _average(
                record["stats"]["total_species_population"] for record in records
            )
        ),
        "runs_with_active_civilizations": sum(
            1 for record in records if record["stats"]["civilizations_active"] > 0
        ),
        "average_active_civilizations": _round2(
            _average(
                record["stats"]["civilizations_active"] for record in records
            )
        ),
        "total_collapsed_civilizations": sum(
            record["stats"]["civilizations_collapsed"] for record in records
        ),
        "average_events_per_run": _round2(
            _average(record["stats"]["events_total"] for record in records)
        ),
        "event_counts_by_type": dict(sorted(event_counts.items())),
        "interesting_runs": _interesting_runs(records),
    }


def format_batch_summary(summary: dict[str, Any]) -> str:
    if summary["runs_count"] == 0:
        return (
            f"No runs found for prefix '{summary['prefix']}' "
            f"in {summary['run_dir']}."
        )

    lines = [
        "Batch Summary",
        f"Prefix: {summary['prefix']}",
        f"Runs count: {summary['runs_count']}",
        f"Modes involved: {', '.join(summary['modes_involved'])}",
        f"Average age: {summary['average_age']:.2f}",
        f"Average active species: {summary['average_active_species']:.2f}",
        f"Total extinct species: {summary['total_extinct_species']}",
        (
            "Average species population: "
            f"{summary['average_species_population']:.2f}"
        ),
        (
            "Runs with active civilizations: "
            f"{summary['runs_with_active_civilizations']}"
        ),
        (
            "Average active civilizations: "
            f"{summary['average_active_civilizations']:.2f}"
        ),
        (
            "Total collapsed civilizations: "
            f"{summary['total_collapsed_civilizations']}"
        ),
        f"Average events per run: {summary['average_events_per_run']:.2f}",
        "Event counts by type:",
    ]
    lines.extend(_count_lines(summary["event_counts_by_type"]))
    lines.append("Interesting runs:")
    for label, item in summary["interesting_runs"].items():
        lines.append(f"- {label}: {item['name']} ({item['value']})")
    return "\n".join(lines)


def format_batch_summary_markdown(summary: dict[str, Any]) -> str:
    if summary["runs_count"] == 0:
        return (
            f"# Batch Summary: {summary['prefix']}\n\n"
            f"No runs found in `{summary['run_dir']}`.\n"
        )

    lines = [
        f"# Batch Summary: {summary['prefix']}",
        "",
        "## Overview",
        "",
        f"- Runs count: {summary['runs_count']}",
        f"- Modes involved: {', '.join(summary['modes_involved'])}",
        f"- Average age: {summary['average_age']:.2f}",
        f"- Average active species: {summary['average_active_species']:.2f}",
        f"- Total extinct species: {summary['total_extinct_species']}",
        (
            "- Average species population: "
            f"{summary['average_species_population']:.2f}"
        ),
        (
            "- Runs with active civilizations: "
            f"{summary['runs_with_active_civilizations']}"
        ),
        (
            "- Average active civilizations: "
            f"{summary['average_active_civilizations']:.2f}"
        ),
        (
            "- Total collapsed civilizations: "
            f"{summary['total_collapsed_civilizations']}"
        ),
        f"- Average events per run: {summary['average_events_per_run']:.2f}",
        "",
        "## Event Counts",
        "",
    ]
    lines.extend(_count_lines(summary["event_counts_by_type"]))
    lines.extend(["", "## Interesting Runs", ""])
    for label, item in summary["interesting_runs"].items():
        lines.append(f"- {label}: {item['name']} ({item['value']})")
    return "\n".join(lines) + "\n"


def write_batch_summary_markdown(summary: dict[str, Any], path: str | Path) -> Path:
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(format_batch_summary_markdown(summary), encoding="utf-8")
    return resolved


def _load_records(directory: Path, prefix: str) -> list[dict[str, Any]]:
    if not directory.exists():
        return []

    records = []
    for path in sorted(directory.glob(f"{prefix}*.json")):
        try:
            universe = load_universe(path)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            continue
        stats = build_stats(universe)
        records.append(
            {
                "name": universe.name,
                "mode": universe.mode,
                "age": universe.age,
                "path": path,
                "stats": stats,
            }
        )
    return records


def _interesting_runs(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        "most active species": _max_record(
            records,
            lambda record: record["stats"]["species_active"],
        ),
        "most active civilizations": _max_record(
            records,
            lambda record: record["stats"]["civilizations_active"],
        ),
        "highest species population": _max_record(
            records,
            lambda record: record["stats"]["total_species_population"],
        ),
        "most events": _max_record(
            records,
            lambda record: record["stats"]["events_total"],
        ),
        "most extinction events": _max_record(
            records,
            lambda record: record["stats"]["events_count_by_type"].get(
                "extinction",
                0,
            ),
        ),
    }


def _max_record(
    records: list[dict[str, Any]],
    metric: Any,
) -> dict[str, Any]:
    record = max(records, key=metric)
    return {"name": record["name"], "value": metric(record)}


def _count_lines(counts: dict[str, int]) -> list[str]:
    if not counts:
        return ["- none"]
    return [f"- {event_type}: {count}" for event_type, count in counts.items()]


def _average(values: Any) -> float:
    items = list(values)
    if not items:
        return 0.0
    return sum(items) / len(items)


def _round2(value: float) -> float:
    return round(value, 2)
