"""Command line interface for universe-evolution-lab."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .modes import VALID_MODES, create_universe
from .reporting import (
    format_comparison,
    format_stats,
    format_timeline,
    write_export,
    write_markdown_report,
)
from .simulator import step_universe, summarize_universe
from .storage import branch_universe, default_run_path, load_universe, save_universe


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "create":
            return _create(args)
        if args.command == "step":
            return _step(args)
        if args.command == "show":
            return _show(args)
        if args.command == "branch":
            return _branch(args)
        if args.command == "stats":
            return _stats(args)
        if args.command == "timeline":
            return _timeline(args)
        if args.command == "export":
            return _export(args)
        if args.command == "report":
            return _report(args)
        if args.command == "compare":
            return _compare(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    parser.print_help()
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m universe_lab.main",
        description="Run small random multiverse civilization experiments.",
    )
    subparsers = parser.add_subparsers(dest="command")

    create = subparsers.add_parser("create", help="create a new universe run")
    create.add_argument("--mode", choices=VALID_MODES, required=True)
    create.add_argument("--name", required=True)
    create.add_argument("--seed", type=int)
    create.add_argument("--output", type=Path)

    step = subparsers.add_parser("step", help="advance a saved run")
    step.add_argument("--run", type=Path, required=True)
    step.add_argument("--steps", type=int, default=1)

    show = subparsers.add_parser("show", help="show a saved run summary")
    show.add_argument("--run", type=Path, required=True)
    show.add_argument("--events", type=int, default=10)
    show.add_argument("--json", action="store_true", help="print raw JSON summary")

    branch = subparsers.add_parser("branch", help="copy a saved run into a new branch")
    branch.add_argument("--run", type=Path, required=True)
    branch.add_argument("--name", required=True)
    branch.add_argument("--output", type=Path)

    stats = subparsers.add_parser("stats", help="show aggregate run statistics")
    stats.add_argument("--run", type=Path, required=True)

    timeline = subparsers.add_parser("timeline", help="show event history")
    timeline.add_argument("--run", type=Path, required=True)
    timeline.add_argument("--limit", type=int)

    export = subparsers.add_parser("export", help="export analysis JSON")
    export.add_argument("--run", type=Path, required=True)
    export.add_argument("--out", type=Path, required=True)

    report = subparsers.add_parser("report", help="write a Markdown run report")
    report.add_argument("--run", type=Path, required=True)
    report.add_argument("--out", type=Path, required=True)

    compare = subparsers.add_parser("compare", help="compare two saved runs")
    compare.add_argument("--run-a", type=Path, required=True)
    compare.add_argument("--run-b", type=Path, required=True)

    return parser


def _create(args: argparse.Namespace) -> int:
    universe = create_universe(args.mode, args.name, args.seed)
    path = save_universe(universe, args.output or default_run_path(args.name))
    print(f"created: {path}")
    print(_format_summary(universe))
    return 0


def _step(args: argparse.Namespace) -> int:
    universe = load_universe(args.run)
    step_universe(universe, args.steps)
    path = save_universe(universe, args.run)
    print(f"saved: {path}")
    print(_format_summary(universe))
    if universe.events:
        print()
        print("Recent events:")
        for event in universe.events[-min(5, len(universe.events)) :]:
            print(f"- year {event.year}: {event.type} - {event.title}")
    return 0


def _show(args: argparse.Namespace) -> int:
    universe = load_universe(args.run)
    summary = summarize_universe(universe)

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0

    print(f"Universe name: {universe.name}")
    print(f"Mode: {universe.mode}")
    print(f"Age: {universe.age}")
    print(
        "Species: "
        f"{summary['living_species']}/{summary['species']} active"
    )
    print(
        "Civilizations: "
        f"{summary['living_civilizations']}/{summary['civilizations']} active"
    )
    print()
    print("Species:")
    if not universe.species:
        print("- none")
    for species in universe.species:
        civ = f", civ={species.civilization_id}" if species.civilization_id else ""
        print(
            "- "
            f"{species.name} ({species.status}, pop={species.population}, "
            f"int={species.intelligence:.2f}, coop={species.cooperation:.2f}, "
            f"adapt={species.adaptability:.2f}{civ})"
        )

    print()
    print("Civilizations:")
    active_civs = universe.civilizations
    if not active_civs:
        print("- none")
    for civilization in active_civs:
        print(
            "- "
            f"{civilization.name} ({civilization.status}, "
            f"pop={civilization.population}, knowledge={civilization.knowledge:.2f}, "
            f"organization={civilization.organization:.2f}, "
            f"stability={civilization.stability:.2f})"
        )

    print()
    print("Recent events:")
    recent_events = universe.events[-max(0, args.events) :]
    if not recent_events:
        print("- none")
    for event in recent_events:
        print(
            f"- year {event.year}: {event.type} - "
            f"{event.title}: {event.description}"
        )
    return 0


def _branch(args: argparse.Namespace) -> int:
    branch, path = branch_universe(args.run, args.name, args.output)
    print(f"branched: {path}")
    print(_format_summary(branch))
    return 0


def _stats(args: argparse.Namespace) -> int:
    universe = load_universe(args.run)
    print(format_stats(universe))
    return 0


def _timeline(args: argparse.Namespace) -> int:
    universe = load_universe(args.run)
    print(format_timeline(universe, args.limit))
    return 0


def _export(args: argparse.Namespace) -> int:
    universe = load_universe(args.run)
    path = write_export(universe, args.out)
    print(f"exported: {path}")
    return 0


def _report(args: argparse.Namespace) -> int:
    universe = load_universe(args.run)
    path = write_markdown_report(universe, args.out)
    print(f"reported: {path}")
    return 0


def _compare(args: argparse.Namespace) -> int:
    run_a = load_universe(args.run_a)
    run_b = load_universe(args.run_b)
    print(format_comparison(run_a, run_b))
    return 0


def _format_summary(universe) -> str:
    summary = summarize_universe(universe)
    return (
        f"{summary['name']} | mode={summary['mode']} | turn={summary['turn']} | "
        f"age={summary['age']} | "
        f"species={summary['living_species']}/{summary['species']} | "
        f"civilizations={summary['living_civilizations']}/{summary['civilizations']} | "
        f"events={summary['events']}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
