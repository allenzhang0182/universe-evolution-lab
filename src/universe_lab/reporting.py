"""Read-only reporting helpers for saved universe runs."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .models import Event, Universe


def build_stats(universe: Universe) -> dict[str, Any]:
    active_structures = [
        structure for structure in universe.structures if structure.status != "collapsed"
    ]
    collapsed_structures = [
        structure for structure in universe.structures if structure.status == "collapsed"
    ]
    classification_counts = Counter(
        structure.classification for structure in universe.structures
    )
    active_populations = [
        population for population in universe.populations if population.status != "extinct"
    ]
    extinct_populations = [
        population for population in universe.populations if population.status == "extinct"
    ]
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
        "structures_total": len(universe.structures),
        "structures_active": len(active_structures),
        "structures_collapsed": len(collapsed_structures),
        "average_structure_complexity": _average(
            structure.complexity for structure in universe.structures
        ),
        "average_structure_stability": _average(
            structure.stability for structure in universe.structures
        ),
        "structure_classification_counts": dict(sorted(classification_counts.items())),
        "populations_total": len(universe.populations),
        "populations_active": len(active_populations),
        "populations_extinct": len(extinct_populations),
        "total_population_size": sum(
            population.size for population in universe.populations
        ),
        "average_population_diversity": _average(
            population.diversity for population in universe.populations
        ),
        "average_population_adaptation": _average(
            population.adaptation for population in universe.populations
        ),
        "average_population_stability": _average(
            population.stability for population in universe.populations
        ),
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
        f"Structures total: {stats['structures_total']}",
        f"Structures active: {stats['structures_active']}",
        f"Structures collapsed: {stats['structures_collapsed']}",
        (
            "Average structure complexity: "
            f"{stats['average_structure_complexity']:.2f}"
        ),
        (
            "Average structure stability: "
            f"{stats['average_structure_stability']:.2f}"
        ),
        "Structure classification counts:",
    ]
    lines.extend(_plain_count_lines(stats["structure_classification_counts"]))
    lines.extend(
        [
            f"Populations total: {stats['populations_total']}",
            f"Populations active: {stats['populations_active']}",
            f"Populations extinct: {stats['populations_extinct']}",
            f"Total population size: {stats['total_population_size']}",
            (
                "Average population diversity: "
                f"{stats['average_population_diversity']:.2f}"
            ),
            (
                "Average population adaptation: "
                f"{stats['average_population_adaptation']:.2f}"
            ),
            (
                "Average population stability: "
                f"{stats['average_population_stability']:.2f}"
            ),
        ]
    )
    lines.extend(
        [
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
    )
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


def build_export_data(universe: Universe) -> dict[str, Any]:
    stats = build_stats(universe)
    return {
        "universe": {
            "id": universe.id,
            "name": universe.name,
            "mode": universe.mode,
            "age": universe.age,
            "seed": universe.seed,
        },
        "structure_summary": _structure_summary(stats),
        "population_summary": _population_summary(stats),
        "species_summary": _species_summary(stats),
        "civilization_summary": _civilization_summary(stats),
        "event_summary": _event_summary(stats),
        "structures": [
            _simplify_structure(structure) for structure in universe.structures
        ],
        "populations": [
            _simplify_population(population) for population in universe.populations
        ],
        "species": [_simplify_species(species) for species in universe.species],
        "civilizations": [
            _simplify_civilization(civilization)
            for civilization in universe.civilizations
        ],
        "timeline": [_simplify_event(event) for event in select_timeline_events(universe)],
    }


def write_export(universe: Universe, path: str | Path) -> Path:
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with resolved.open("w", encoding="utf-8") as handle:
        json.dump(build_export_data(universe), handle, indent=2, sort_keys=True)
        handle.write("\n")
    return resolved


def format_markdown_report(universe: Universe, recent_limit: int = 20) -> str:
    export_data = build_export_data(universe)
    structure_summary = export_data["structure_summary"]
    population_summary = export_data["population_summary"]
    species_summary = export_data["species_summary"]
    civilization_summary = export_data["civilization_summary"]
    event_summary = export_data["event_summary"]
    recent_events = select_timeline_events(universe, recent_limit)

    lines: list[str] = [
        f"# Universe Report: {universe.name}",
        "",
        "## Basic Info",
        "",
        f"- ID: {universe.id}",
        f"- Mode: {universe.mode}",
        f"- Age: {universe.age}",
        f"- Seed: {universe.seed}",
        "",
        "## Structure Summary",
        "",
        f"- Total: {structure_summary['total']}",
        f"- Active: {structure_summary['active']}",
        f"- Collapsed: {structure_summary['collapsed']}",
        f"- Average complexity: {structure_summary['average_complexity']:.2f}",
        f"- Average stability: {structure_summary['average_stability']:.2f}",
        "- Classification counts:",
    ]
    lines.extend(_markdown_count_lines(structure_summary["classification_counts"]))
    lines.extend(
        [
            "",
            "## Population Summary",
            "",
            f"- Total: {population_summary['total']}",
            f"- Active: {population_summary['active']}",
            f"- Extinct: {population_summary['extinct']}",
            f"- Total size: {population_summary['total_size']}",
            f"- Average diversity: {population_summary['average_diversity']:.2f}",
            f"- Average adaptation: {population_summary['average_adaptation']:.2f}",
            f"- Average stability: {population_summary['average_stability']:.2f}",
            "",
            "## Species Summary",
            "",
            f"- Total: {species_summary['total']}",
            f"- Active: {species_summary['active']}",
            f"- Extinct: {species_summary['extinct']}",
            f"- Total population: {species_summary['total_population']}",
            f"- Average intelligence: {species_summary['average_intelligence']:.2f}",
            f"- Average cooperation: {species_summary['average_cooperation']:.2f}",
            f"- Average adaptability: {species_summary['average_adaptability']:.2f}",
            "",
        ]
    )
    lines.extend(
        [
            "## Civilization Summary",
            "",
            f"- Total: {civilization_summary['total']}",
            f"- Active: {civilization_summary['active']}",
            f"- Collapsed: {civilization_summary['collapsed']}",
            f"- Total population: {civilization_summary['total_population']}",
            f"- Average knowledge: {civilization_summary['average_knowledge']:.2f}",
            (
                "- Average organization: "
                f"{civilization_summary['average_organization']:.2f}"
            ),
            f"- Average stability: {civilization_summary['average_stability']:.2f}",
            "",
            "## Event Summary",
            "",
            f"- Total: {event_summary['total']}",
            "- Counts by type:",
        ]
    )
    lines.extend(_markdown_count_lines(event_summary["counts_by_type"]))

    lines.extend(["", "## Structure Overview", ""])
    if not export_data["structures"]:
        lines.append("- none")
    else:
        for structure in export_data["structures"]:
            lines.append(
                "- "
                f"{structure['name']} ({structure['status']}, "
                f"{structure['classification']}): "
                f"complexity={structure['complexity']:.2f}, "
                f"stability={structure['stability']:.2f}, "
                f"replication={structure['replication_potential']:.2f}"
            )

    lines.extend(["", "## Population Overview", ""])
    if not export_data["populations"]:
        lines.append("- none")
    else:
        for population in export_data["populations"]:
            lines.append(
                "- "
                f"{population['name']} ({population['status']}): "
                f"size={population['size']}, "
                f"adaptation={population['adaptation']:.2f}, "
                f"reproduction={population['reproduction']:.2f}, "
                f"stability={population['stability']:.2f}"
            )

    lines.extend(
        [
            "",
            "## Species Overview",
            "",
        ]
    )
    if not export_data["species"]:
        lines.append("- none")
    else:
        for species in export_data["species"]:
            lines.append(
                "- "
                f"{species['name']} ({species['status']}): "
                f"population={species['population']}, "
                f"intelligence={species['intelligence']:.2f}, "
                f"cooperation={species['cooperation']:.2f}, "
                f"adaptability={species['adaptability']:.2f}"
            )

    lines.extend(
        [
            "",
            "## Civilization Overview",
            "",
        ]
    )
    if not export_data["civilizations"]:
        lines.append("- none")
    else:
        for civilization in export_data["civilizations"]:
            lines.append(
                "- "
                f"{civilization['name']} ({civilization['status']}): "
                f"population={civilization['population']}, "
                f"knowledge={civilization['knowledge']:.2f}, "
                f"organization={civilization['organization']:.2f}, "
                f"stability={civilization['stability']:.2f}"
            )

    lines.extend(
        [
            "",
            "## Recent Timeline",
            "",
        ]
    )
    if not recent_events:
        lines.append("- none")
    else:
        for event in recent_events:
            lines.append(
                "- "
                f"Year {event.year}: {event.type} - "
                f"{event.title}: {event.description}"
            )

    return "\n".join(lines) + "\n"


def write_markdown_report(universe: Universe, path: str | Path) -> Path:
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(format_markdown_report(universe), encoding="utf-8")
    return resolved


def format_comparison(run_a: Universe, run_b: Universe) -> str:
    data_a = build_export_data(run_a)
    data_b = build_export_data(run_b)
    species_a = data_a["species_summary"]
    species_b = data_b["species_summary"]
    structures_a = data_a["structure_summary"]
    structures_b = data_b["structure_summary"]
    populations_a = data_a["population_summary"]
    populations_b = data_b["population_summary"]
    civ_a = data_a["civilization_summary"]
    civ_b = data_b["civilization_summary"]
    event_a = data_a["event_summary"]
    event_b = data_b["event_summary"]

    lines = [
        "Universe Comparison",
        (
            f"A: {run_a.name} | mode={run_a.mode} | "
            f"age={run_a.age}"
        ),
        (
            f"B: {run_b.name} | mode={run_b.mode} | "
            f"age={run_b.age}"
        ),
        "",
        "Differences (B - A):",
        _diff_line("Structures active", structures_a["active"], structures_b["active"]),
        _diff_line(
            "Structures collapsed",
            structures_a["collapsed"],
            structures_b["collapsed"],
        ),
        _diff_line(
            "Populations active",
            populations_a["active"],
            populations_b["active"],
        ),
        _diff_line(
            "Populations extinct",
            populations_a["extinct"],
            populations_b["extinct"],
        ),
        _diff_line("Species active", species_a["active"], species_b["active"]),
        _diff_line("Species extinct", species_a["extinct"], species_b["extinct"]),
        _diff_line(
            "Species total population",
            species_a["total_population"],
            species_b["total_population"],
        ),
        _diff_line("Civilizations active", civ_a["active"], civ_b["active"]),
        _diff_line("Civilizations collapsed", civ_a["collapsed"], civ_b["collapsed"]),
        _diff_line(
            "Civilization total population",
            civ_a["total_population"],
            civ_b["total_population"],
        ),
        _diff_line("Events total", event_a["total"], event_b["total"]),
        "",
        "Event type count differences (B - A):",
    ]
    lines.extend(
        _event_diff_lines(
            event_a["counts_by_type"],
            event_b["counts_by_type"],
        )
    )
    lines.append("Classification count differences (B - A):")
    lines.extend(
        _event_diff_lines(
            structures_a["classification_counts"],
            structures_b["classification_counts"],
        )
    )
    lines.extend(["", "Conclusion:"])
    lines.extend(_comparison_conclusions(species_a, species_b, civ_a, civ_b, event_a, event_b))
    return "\n".join(lines)


def _average(values: Iterable[float]) -> float:
    items = list(values)
    if not items:
        return 0.0
    return sum(items) / len(items)


def _round2(value: float) -> float:
    return round(value, 2)


def _structure_summary(stats: dict[str, Any]) -> dict[str, Any]:
    return {
        "total": stats["structures_total"],
        "active": stats["structures_active"],
        "collapsed": stats["structures_collapsed"],
        "average_complexity": _round2(stats["average_structure_complexity"]),
        "average_stability": _round2(stats["average_structure_stability"]),
        "classification_counts": stats["structure_classification_counts"],
    }


def _population_summary(stats: dict[str, Any]) -> dict[str, Any]:
    return {
        "total": stats["populations_total"],
        "active": stats["populations_active"],
        "extinct": stats["populations_extinct"],
        "total_size": stats["total_population_size"],
        "average_diversity": _round2(stats["average_population_diversity"]),
        "average_adaptation": _round2(stats["average_population_adaptation"]),
        "average_stability": _round2(stats["average_population_stability"]),
    }


def _species_summary(stats: dict[str, Any]) -> dict[str, Any]:
    return {
        "total": stats["species_total"],
        "active": stats["species_active"],
        "extinct": stats["species_extinct"],
        "total_population": stats["total_species_population"],
        "average_intelligence": _round2(stats["average_species_intelligence"]),
        "average_cooperation": _round2(stats["average_species_cooperation"]),
        "average_adaptability": _round2(stats["average_species_adaptability"]),
    }


def _civilization_summary(stats: dict[str, Any]) -> dict[str, Any]:
    return {
        "total": stats["civilizations_total"],
        "active": stats["civilizations_active"],
        "collapsed": stats["civilizations_collapsed"],
        "total_population": stats["total_civilization_population"],
        "average_knowledge": _round2(stats["average_civilization_knowledge"]),
        "average_organization": _round2(stats["average_civilization_organization"]),
        "average_stability": _round2(stats["average_civilization_stability"]),
    }


def _event_summary(stats: dict[str, Any]) -> dict[str, Any]:
    return {
        "total": stats["events_total"],
        "counts_by_type": stats["events_count_by_type"],
    }


def _simplify_structure(structure: Any) -> dict[str, Any]:
    return {
        "id": structure.id,
        "name": structure.name,
        "age": structure.age,
        "scale": structure.scale,
        "substrate": structure.substrate,
        "status": structure.status,
        "classification": structure.classification,
        "complexity": _round2(structure.complexity),
        "stability": _round2(structure.stability),
        "energy_flow": _round2(structure.energy_flow),
        "information_retention": _round2(structure.information_retention),
        "replication_potential": _round2(structure.replication_potential),
        "variation_rate": _round2(structure.variation_rate),
        "boundary_strength": _round2(structure.boundary_strength),
        "adaptation_score": _round2(structure.adaptation_score),
    }


def _simplify_population(population: Any) -> dict[str, Any]:
    return {
        "id": population.id,
        "name": population.name,
        "source_structure_id": population.source_structure_id,
        "lineage_id": population.lineage_id,
        "age": population.age,
        "status": population.status,
        "size": population.size,
        "diversity": _round2(population.diversity),
        "adaptation": _round2(population.adaptation),
        "reproduction": _round2(population.reproduction),
        "stability": _round2(population.stability),
    }


def _simplify_species(species: Any) -> dict[str, Any]:
    return {
        "id": species.id,
        "name": species.name,
        "status": species.status,
        "population": species.population,
        "intelligence": _round2(species.intelligence),
        "cooperation": _round2(species.cooperation),
        "adaptability": _round2(species.adaptability),
        "aggression": _round2(species.aggression),
        "mutation_rate": _round2(species.mutation_rate),
        "civilization_id": species.civilization_id,
    }


def _simplify_civilization(civilization: Any) -> dict[str, Any]:
    return {
        "id": civilization.id,
        "name": civilization.name,
        "status": civilization.status,
        "species_id": civilization.species_id,
        "population": civilization.population,
        "knowledge": _round2(civilization.knowledge),
        "organization": _round2(civilization.organization),
        "creativity": _round2(civilization.creativity),
        "stability": _round2(civilization.stability),
        "expansion": _round2(civilization.expansion),
        "ethics": _round2(civilization.ethics),
    }


def _simplify_event(event: Event) -> dict[str, Any]:
    return {
        "year": event.year,
        "type": event.type,
        "title": event.title,
        "description": event.description,
        "impact": event.impact,
    }


def _markdown_count_lines(counts: dict[str, int]) -> list[str]:
    if not counts:
        return ["  - none"]
    return [f"  - {event_type}: {count}" for event_type, count in counts.items()]


def _plain_count_lines(counts: dict[str, int]) -> list[str]:
    if not counts:
        return ["- none"]
    return [f"- {event_type}: {count}" for event_type, count in counts.items()]


def _diff_line(label: str, value_a: int, value_b: int) -> str:
    return f"- {label}: A={value_a}, B={value_b}, diff={value_b - value_a}"


def _event_diff_lines(counts_a: dict[str, int], counts_b: dict[str, int]) -> list[str]:
    event_types = sorted(set(counts_a) | set(counts_b))
    if not event_types:
        return ["- none"]
    return [
        _diff_line(event_type, counts_a.get(event_type, 0), counts_b.get(event_type, 0))
        for event_type in event_types
    ]


def _comparison_conclusions(
    species_a: dict[str, Any],
    species_b: dict[str, Any],
    civ_a: dict[str, Any],
    civ_b: dict[str, Any],
    event_a: dict[str, Any],
    event_b: dict[str, Any],
) -> list[str]:
    conclusions = []
    if species_a["active"] > species_b["active"]:
        conclusions.append("- A has more active species.")
    elif species_b["active"] > species_a["active"]:
        conclusions.append("- B has more active species.")
    else:
        conclusions.append("- Both universes have the same number of active species.")

    if civ_a["active"] == 0 and civ_b["active"] == 0:
        conclusions.append("- Both universes have no active civilizations.")
    elif civ_a["active"] > civ_b["active"]:
        conclusions.append("- A has more active civilizations.")
    elif civ_b["active"] > civ_a["active"]:
        conclusions.append("- B has more active civilizations.")
    else:
        conclusions.append("- Both universes have the same number of active civilizations.")

    if event_a["total"] > event_b["total"]:
        conclusions.append("- A has more recorded events.")
    elif event_b["total"] > event_a["total"]:
        conclusions.append("- B has more recorded events.")
    else:
        conclusions.append("- Both universes have the same number of recorded events.")
    return conclusions
