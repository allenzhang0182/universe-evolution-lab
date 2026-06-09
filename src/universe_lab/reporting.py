"""Read-only reporting helpers for saved universe runs."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from typing import Any

from .models import Event, Universe


def build_stats(universe: Universe) -> dict[str, Any]:
    active_species = [
        species for species in universe.species if species.status != "extinct"
    ]
    extinct_species = [
        species for species in universe.species if species.status == "extinct"
    ]
    active_civilizations = [
        civilization
        for civilization in universe.civilizations
        if civilization.status != "collapsed"
    ]
    collapsed_civilizations = [
        civilization
        for civilization in universe.civilizations
        if civilization.status == "collapsed"
    ]
    event_counts = Counter(event.type for event in universe.events)

    return {
        "universe_name": universe.name,
        "mode": universe.mode,
        "age": universe.age,
        "species_total": len(universe.species),
        "species_active": len(active_species),
        "species_extinct": len(extinct_species),
        "total_species_population": sum(
            species.population for species in universe.species
        ),
        "average_species_intelligence": _average(
            species.intelligence for species in universe.species
        ),
        "average_species_cooperation": _average(
            species.cooperation for species in universe.species
        ),
        "average_species_adaptability": _average(
            species.adaptability for species in universe.species
        ),
        "civilizations_total": len(universe.civilizations),
        "civilizations_active": len(active_civilizations),
        "civilizations_collapsed": len(collapsed_civilizations),
        "total_civilization_population": sum(
            civilization.population for civilization in universe.civilizations
        ),
        "average_civilization_knowledge": _average(
            civilization.knowledge for civilization in universe.civilizations
        ),
        "average_civilization_organization": _average(
            civilization.organization for civilization in universe.civilizations
        ),
        "average_civilization_stability": _average(
            civilization.stability for civilization in universe.civilizations
        ),
        "events_total": len(universe.events),
        "events_count_by_type": dict(sorted(event_counts.items())),
    }


def format_stats(universe: Universe) -> str:
    stats = build_stats(universe)
    lines = [
        f"Universe name: {stats['universe_name']}",
        f"Mode: {stats['mode']}",
        f"Age: {stats['age']}",
        f"Species total: {stats['species_total']}",
        f"Species active: {stats['species_active']}",
        f"Species extinct: {stats['species_extinct']}",
        f"Total species population: {stats['total_species_population']}",
        (
            "Average species intelligence: "
            f"{stats['average_species_intelligence']:.2f}"
        ),
        (
            "Average species cooperation: "
            f"{stats['average_species_cooperation']:.2f}"
        ),
        (
            "Average species adaptability: "
            f"{stats['average_species_adaptability']:.2f}"
        ),
        f"Civilizations total: {stats['civilizations_total']}",
        f"Civilizations active: {stats['civilizations_active']}",
        f"Civilizations collapsed: {stats['civilizations_collapsed']}",
        (
            "Total civilization population: "
            f"{stats['total_civilization_population']}"
        ),
        (
            "Average civilization knowledge: "
            f"{stats['average_civilization_knowledge']:.2f}"
        ),
        (
            "Average civilization organization: "
            f"{stats['average_civilization_organization']:.2f}"
        ),
        (
            "Average civilization stability: "
            f"{stats['average_civilization_stability']:.2f}"
        ),
        f"Events total: {stats['events_total']}",
        "Events count by type:",
    ]
    event_counts = stats["events_count_by_type"]
    if not event_counts:
        lines.append("- none")
    else:
        for event_type, count in event_counts.items():
            lines.append(f"- {event_type}: {count}")
    return "\n".join(lines)


def select_timeline_events(universe: Universe, limit: int | None = None) -> list[Event]:
    events = list(universe.events)
    if limit is not None:
        if limit < 0:
            raise ValueError("limit must be non-negative")
        events = events[-limit:] if limit else []
    return sorted(events, key=lambda event: event.year)


def format_timeline(universe: Universe, limit: int | None = None) -> str:
    events = select_timeline_events(universe, limit)
    header = f"Timeline for {universe.name} (mode={universe.mode}, age={universe.age})"
    lines = [header]
    if not events:
        lines.append("- no events recorded")
        return "\n".join(lines)

    for event in events:
        lines.append(
            f"- year {event.year}: {event.type} - "
            f"{event.title}: {event.description}"
        )
    return "\n".join(lines)


def _average(values: Iterable[float]) -> float:
    items = list(values)
    if not items:
        return 0.0
    return sum(items) / len(items)
