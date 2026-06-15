"""Turn-based simulation rules for the MVP."""

from __future__ import annotations

import random

from .models import (
    Civilization,
    EmergentStructure,
    Event,
    Population,
    Species,
    Universe,
    new_id,
    utc_now,
)


def step_universe(universe: Universe, steps: int = 1) -> Universe:
    if steps < 1:
        raise ValueError("steps must be at least 1")

    for _ in range(steps):
        _step_once(universe)

    universe.updated_at = utc_now()
    if len(universe.events) > universe.config.max_events:
        universe.events = universe.events[-universe.config.max_events :]
    return universe


def summarize_universe(universe: Universe) -> dict[str, int | str]:
    active_structures = sum(
        1 for item in universe.structures if item.status != "collapsed"
    )
    collapsed_structures = sum(
        1 for item in universe.structures if item.status == "collapsed"
    )
    active_populations = sum(
        1 for item in universe.populations if item.status != "extinct"
    )
    extinct_populations = sum(
        1 for item in universe.populations if item.status == "extinct"
    )
    living_species = sum(1 for item in universe.species if item.status != "extinct")
    living_civilizations = sum(
        1 for item in universe.civilizations if item.status != "collapsed"
    )
    return {
        "name": universe.name,
        "mode": universe.mode,
        "turn": universe.turn,
        "age": universe.age,
        "structures": len(universe.structures),
        "active_structures": active_structures,
        "collapsed_structures": collapsed_structures,
        "populations": len(universe.populations),
        "active_populations": active_populations,
        "extinct_populations": extinct_populations,
        "species": len(universe.species),
        "living_species": living_species,
        "civilizations": len(universe.civilizations),
        "living_civilizations": living_civilizations,
        "events": len(universe.events),
    }


def _step_once(universe: Universe) -> None:
    universe.turn += 1
    universe.age += 1
    rng = random.Random(universe.seed + universe.turn * 7919)
    event_count = len(universe.events)

    for structure in list(universe.structures):
        _advance_structure(universe, structure, rng)

    _maybe_spawn_population(universe, rng)

    for population in list(universe.populations):
        _advance_population(universe, population, rng)

    _maybe_form_species(universe, rng)

    species_by_id = {item.id: item for item in universe.species}
    for species in universe.species:
        _advance_species(universe, species, rng)

    for civilization in universe.civilizations:
        _advance_civilization(universe, civilization, species_by_id, rng)

    _maybe_spawn_civilizations(universe, rng)
    _maybe_environment_event(universe, rng)

    if len(universe.events) == event_count:
        _add_event(
            universe,
            "quiet_age",
            "Quiet Age",
            "No major evolutionary or civilizational shift was recorded.",
            {"age": universe.age},
        )


def _advance_structure(
    universe: Universe,
    structure: EmergentStructure,
    rng: random.Random,
) -> None:
    if structure.status == "collapsed":
        return

    structure.age += 1
    old_complexity = structure.complexity
    old_status = structure.status
    old_classification = structure.classification
    variation = max(0.005, structure.variation_rate)

    structure.complexity = _clamp(
        structure.complexity
        + rng.uniform(-0.015, 0.034) * (1.0 + variation * 4)
        + structure.energy_flow * 0.004
        + structure.information_retention * 0.003
    )
    structure.stability = _clamp(
        structure.stability
        + rng.uniform(-0.03, 0.026) * (1.0 + variation * 2)
        + structure.boundary_strength * 0.008
        - variation * 0.018
    )
    structure.energy_flow = _clamp(
        structure.energy_flow
        + rng.uniform(-0.022, 0.026) * (1.0 + variation * 2)
        + structure.complexity * 0.004
    )
    structure.information_retention = _clamp(
        structure.information_retention
        + rng.uniform(-0.018, 0.025) * (1.0 + variation * 2)
        + structure.stability * 0.004
    )
    structure.replication_potential = _clamp(
        structure.replication_potential
        + rng.uniform(-0.018, 0.026) * (1.0 + variation * 2)
        + structure.information_retention * 0.003
    )
    structure.boundary_strength = _clamp(
        structure.boundary_strength
        + rng.uniform(-0.02, 0.024) * (1.0 + variation * 2)
        + structure.stability * 0.004
    )
    structure.adaptation_score = _clamp(
        structure.adaptation_score
        + rng.uniform(-0.018, 0.025) * (1.0 + variation * 3)
        + structure.replication_potential * 0.003
    )
    structure.variation_rate = _clamp(
        structure.variation_rate + rng.uniform(-0.005, 0.006),
        0.003,
        0.14,
    )

    _maybe_mutate_structure(universe, structure, rng)
    _update_structure_status(universe, structure, old_status)
    if structure.status == "collapsed":
        return

    _update_structure_classification(universe, structure, old_classification)
    _maybe_replicate_structure(universe, structure, rng)

    if structure.complexity - old_complexity >= 0.055:
        _add_event(
            universe,
            "structure_growth",
            f"{structure.name} Increased Complexity",
            f"{structure.name} retained a more complex configuration.",
            {
                "complexity": structure.complexity,
                "classification": structure.classification,
            },
            "structure",
            structure.id,
        )


def _maybe_mutate_structure(
    universe: Universe,
    structure: EmergentStructure,
    rng: random.Random,
) -> None:
    if rng.random() >= structure.variation_rate * 0.55:
        return

    complexity_delta = rng.uniform(-0.035, 0.05)
    stability_delta = rng.uniform(-0.035, 0.035)
    information_delta = rng.uniform(-0.025, 0.04)
    structure.complexity = _clamp(structure.complexity + complexity_delta)
    structure.stability = _clamp(structure.stability + stability_delta)
    structure.information_retention = _clamp(
        structure.information_retention + information_delta
    )
    structure.replication_potential = _clamp(
        structure.replication_potential + rng.uniform(-0.025, 0.035)
    )
    _add_event(
        universe,
        "structure_mutation",
        f"{structure.name} Varied",
        f"{structure.name} shifted internal organization.",
        {
            "complexity_delta": round(complexity_delta, 4),
            "stability_delta": round(stability_delta, 4),
            "information_delta": round(information_delta, 4),
        },
        "structure",
        structure.id,
    )


def _update_structure_status(
    universe: Universe,
    structure: EmergentStructure,
    old_status: str,
) -> None:
    if structure.stability <= 0.045 or structure.complexity <= 0.025:
        structure.status = "collapsed"
        _add_event(
            universe,
            "structure_collapsed",
            f"{structure.name} Collapsed",
            f"{structure.name} could not maintain its structure.",
            {"stability": structure.stability, "complexity": structure.complexity},
            "structure",
            structure.id,
        )
        return

    if structure.stability < 0.16:
        structure.status = "degraded"
    elif structure.status == "degraded" and structure.stability >= 0.25:
        structure.status = "active"
    else:
        structure.status = "active"

    if structure.status == "degraded" and old_status != "degraded":
        _add_event(
            universe,
            "structure_degraded",
            f"{structure.name} Degraded",
            f"{structure.name} lost structural coherence.",
            {"stability": structure.stability},
            "structure",
            structure.id,
        )


def _update_structure_classification(
    universe: Universe,
    structure: EmergentStructure,
    old_classification: str,
) -> None:
    if structure.status != "active":
        return

    new_classification = _classify_structure(structure)
    structure.classification = new_classification
    if new_classification == old_classification:
        return

    _add_event(
        universe,
        "classification_shift",
        f"{structure.name} Reclassified",
        f"{structure.name} shifted from {old_classification} to {new_classification}.",
        {
            "from": old_classification,
            "to": new_classification,
        },
        "structure",
        structure.id,
    )
    if new_classification == "proto_life":
        _add_event(
            universe,
            "proto_life_detected",
            f"{structure.name} Met Proto-Life Criteria",
            f"{structure.name} combined maintenance, boundary, information, and replication traits.",
            {"classification": new_classification},
            "structure",
            structure.id,
        )
    elif new_classification == "life_lineage":
        _add_event(
            universe,
            "life_lineage_emerged",
            f"{structure.name} Became a Life Lineage",
            f"{structure.name} sustained adaptive replication-like organization.",
            {"classification": new_classification},
            "structure",
            structure.id,
        )


def _classify_structure(structure: EmergentStructure) -> str:
    if (
        structure.complexity >= 0.65
        and structure.stability >= 0.55
        and structure.energy_flow >= 0.5
        and structure.information_retention >= 0.55
        and structure.replication_potential >= 0.5
        and structure.boundary_strength >= 0.5
        and structure.adaptation_score >= 0.45
        and structure.age >= 5
    ):
        return "life_lineage"
    if (
        structure.complexity >= 0.55
        and structure.stability >= 0.5
        and structure.energy_flow >= 0.45
        and structure.information_retention >= 0.45
        and structure.replication_potential >= 0.4
        and structure.boundary_strength >= 0.45
        and structure.age >= 3
    ):
        return "proto_life"
    if (
        structure.complexity >= 0.45
        and structure.stability >= 0.45
        and structure.energy_flow >= 0.35
        and structure.boundary_strength >= 0.35
    ):
        return "self_maintaining"
    if structure.complexity >= 0.35 and structure.stability >= 0.25:
        return "complex_structure"
    return "inert"


def _maybe_replicate_structure(
    universe: Universe,
    structure: EmergentStructure,
    rng: random.Random,
) -> None:
    if len(universe.structures) >= 80:
        return
    if structure.replication_potential < 0.52 or structure.information_retention < 0.38:
        return
    if structure.boundary_strength < 0.34 or structure.status != "active":
        return
    chance = 0.01
    chance += (structure.replication_potential - 0.52) * 0.12
    chance += (structure.information_retention - 0.38) * 0.08
    chance += max(0.0, structure.adaptation_score - 0.35) * 0.06
    if rng.random() > chance:
        return

    child = EmergentStructure(
        id=new_id("str"),
        name=f"{structure.name}-r{len(universe.structures) + 1}",
        age=0,
        scale=structure.scale,
        substrate=structure.substrate,
        complexity=_mutated_value(structure.complexity, rng, structure.variation_rate),
        stability=_mutated_value(structure.stability, rng, structure.variation_rate),
        energy_flow=_mutated_value(structure.energy_flow, rng, structure.variation_rate),
        information_retention=_mutated_value(
            structure.information_retention,
            rng,
            structure.variation_rate,
        ),
        replication_potential=_mutated_value(
            structure.replication_potential,
            rng,
            structure.variation_rate,
        ),
        variation_rate=_clamp(
            structure.variation_rate + rng.uniform(-0.015, 0.018),
            0.003,
            0.14,
        ),
        boundary_strength=_mutated_value(
            structure.boundary_strength,
            rng,
            structure.variation_rate,
        ),
        adaptation_score=_mutated_value(
            structure.adaptation_score,
            rng,
            structure.variation_rate,
        ),
        status="active",
        classification="inert",
    )
    child.classification = _classify_structure(child)
    universe.structures.append(child)
    _add_event(
        universe,
        "structure_replication",
        f"{structure.name} Replicated",
        f"{structure.name} produced a related structure with variation.",
        {
            "child_id": child.id,
            "child_classification": child.classification,
        },
        "structure",
        structure.id,
    )


def _maybe_spawn_population(universe: Universe, rng: random.Random) -> None:
    populated_sources = {
        population.source_structure_id
        for population in universe.populations
        if population.status != "extinct"
    }
    for structure in universe.structures:
        if structure.id in populated_sources:
            continue
        if structure.status != "active" or structure.classification != "life_lineage":
            continue
        if structure.age < 7:
            continue
        lineage_strength = (
            structure.stability
            + structure.replication_potential
            + structure.adaptation_score
            + structure.boundary_strength
        ) / 4
        if lineage_strength < 0.54:
            continue
        chance = min(0.22, (lineage_strength - 0.54) * 0.5 + 0.04)
        if rng.random() > chance:
            continue

        population = Population(
            id=new_id("pop"),
            name=f"{structure.name} Population",
            source_structure_id=structure.id,
            lineage_id=structure.id,
            age=0,
            size=max(80, int(1_000 * lineage_strength * rng.uniform(0.6, 1.8))),
            diversity=round(_clamp(structure.variation_rate * 4 + rng.uniform(0.05, 0.2)), 3),
            adaptation=round(_clamp(structure.adaptation_score + rng.uniform(-0.05, 0.08)), 3),
            reproduction=round(
                _clamp(structure.replication_potential + rng.uniform(-0.05, 0.08)),
                3,
            ),
            stability=round(_clamp(structure.stability + rng.uniform(-0.05, 0.06)), 3),
            status="active",
        )
        universe.populations.append(population)
        _add_event(
            universe,
            "population_emerged",
            f"{population.name} Emerged",
            f"{structure.name} persisted as a bounded adaptive population.",
            {"size": population.size},
            "population",
            population.id,
        )


def _advance_population(
    universe: Universe,
    population: Population,
    rng: random.Random,
) -> None:
    if population.status == "extinct":
        return

    population.age += 1
    old_size = population.size
    growth_rate = rng.uniform(-0.08, 0.12)
    growth_rate += (population.adaptation - 0.5) * 0.11
    growth_rate += (population.reproduction - 0.5) * 0.1
    growth_rate += (population.stability - 0.5) * 0.07
    growth_rate += (population.diversity - 0.35) * 0.035
    population.size = max(0, int(population.size * (1.0 + growth_rate)))
    population.diversity = _clamp(population.diversity + rng.uniform(-0.015, 0.02))
    population.adaptation = _clamp(population.adaptation + rng.uniform(-0.018, 0.026))
    population.reproduction = _clamp(population.reproduction + rng.uniform(-0.018, 0.024))
    population.stability = _clamp(
        population.stability
        + rng.uniform(-0.024, 0.022)
        + (population.adaptation - 0.5) * 0.012
    )

    if population.size < 50 or population.stability <= 0.06:
        population.size = 0
        population.status = "extinct"
        _add_event(
            universe,
            "population_extinct",
            f"{population.name} Went Extinct",
            f"{population.name} failed to maintain a viable population.",
            {"size": 0, "stability": population.stability},
            "population",
            population.id,
        )
        return

    change_ratio = (population.size - old_size) / old_size if old_size else 0.0
    if change_ratio >= 0.15:
        population.status = "active"
        _add_event(
            universe,
            "population_growth",
            f"{population.name} Grew",
            f"{population.name} expanded as a stable lineage population.",
            {"size_delta": population.size - old_size, "size": population.size},
            "population",
            population.id,
        )
    elif change_ratio <= -0.15:
        population.status = "declining"
        _add_event(
            universe,
            "population_decline",
            f"{population.name} Declined",
            f"{population.name} lost population stability.",
            {"size_delta": population.size - old_size, "size": population.size},
            "population",
            population.id,
        )
    elif population.status == "declining" and population.stability > 0.28:
        population.status = "active"


def _maybe_form_species(universe: Universe, rng: random.Random) -> None:
    species_sources = {
        species.source_population_id
        for species in universe.species
        if species.source_population_id is not None
    }
    for population in universe.populations:
        if population.status == "extinct" or population.id in species_sources:
            continue
        if (
            population.size < 30_000
            or population.adaptation < 0.58
            or population.reproduction < 0.52
            or population.stability < 0.52
            or population.diversity < 0.35
            or population.age < 5
        ):
            continue
        chance = 0.04
        chance += (population.adaptation - 0.58) * 0.16
        chance += (population.reproduction - 0.52) * 0.12
        chance += (population.diversity - 0.35) * 0.08
        if rng.random() > min(0.2, chance):
            continue

        species = Species(
            id=new_id("sp"),
            name=f"{population.name} Species",
            population=population.size,
            adaptability=round(_clamp(population.adaptation), 3),
            intelligence=round(_clamp(0.08 + population.diversity * 0.25), 3),
            cooperation=round(_clamp(0.22 + population.stability * 0.5), 3),
            aggression=round(rng.uniform(0.04, 0.45), 3),
            mutation_rate=round(_clamp(0.012 + population.diversity * 0.08), 3),
            status="stable",
            resilience=round(_clamp(0.25 + population.stability * 0.55), 3),
            environment_affinity=rng.choice(
                ("oceanic", "temperate", "desert", "ice", "volcanic", "orbital")
            ),
            source_population_id=population.id,
        )
        universe.species.append(species)
        _add_event(
            universe,
            "speciation",
            f"{species.name} Formed",
            f"{population.name} differentiated into a stable species.",
            {"species_id": species.id, "population_size": population.size},
            "species",
            species.id,
        )


def _advance_species(universe: Universe, species: Species, rng: random.Random) -> None:
    if species.status == "extinct" or species.extinct:
        species.status = "extinct"
        species.extinct = True
        return

    species.age += 1
    old_population = species.population
    old_intelligence = species.intelligence
    growth_rate = rng.uniform(-0.075, 0.105)
    growth_rate += (species.adaptability - 0.5) * 0.11
    growth_rate += (species.cooperation - 0.5) * 0.075
    growth_rate += (species.resilience - 0.5) * 0.045
    growth_rate -= species.aggression * rng.uniform(0.015, 0.07)

    species.population = max(0, int(species.population * (1.0 + growth_rate)))
    species.intelligence = _clamp(
        species.intelligence
        + rng.uniform(-0.012, 0.028) * species.adaptability
        + (species.cooperation - species.aggression) * 0.004
    )
    species.cooperation = _clamp(
        species.cooperation + rng.uniform(-0.012, 0.014) - species.aggression * 0.002
    )
    species.aggression = _clamp(species.aggression + rng.uniform(-0.012, 0.012))
    species.adaptability = _clamp(species.adaptability + rng.uniform(-0.01, 0.014))
    species.resilience = _clamp(species.resilience + rng.uniform(-0.01, 0.012))

    if rng.random() < species.mutation_rate:
        _mutate_species(universe, species, rng, old_intelligence)

    if rng.random() < 0.045:
        _apply_species_pressure(universe, species, rng)

    if species.population < 500:
        species.population = 0
        species.status = "extinct"
        species.extinct = True
        _add_event(
            universe,
            "extinction",
            f"{species.name} Went Extinct",
            f"{species.name} disappeared after its population fell below recovery levels.",
            {"population": 0},
            "species",
            species.id,
        )
        return

    _update_species_status(species, old_population)
    population_delta = species.population - old_population
    if old_population > 0:
        change_ratio = population_delta / old_population
    else:
        change_ratio = 0.0

    if change_ratio >= 0.12:
        _add_event(
            universe,
            "species_growth",
            f"{species.name} Expanded",
            f"{species.name} found a stronger ecological foothold.",
            {
                "population_delta": population_delta,
                "population": species.population,
                "status": species.status,
            },
            "species",
            species.id,
        )
    elif change_ratio <= -0.12:
        _add_event(
            universe,
            "species_decline",
            f"{species.name} Declined",
            f"{species.name} lost population pressure against its habitat.",
            {
                "population_delta": population_delta,
                "population": species.population,
                "status": species.status,
            },
            "species",
            species.id,
        )


def _mutate_species(
    universe: Universe,
    species: Species,
    rng: random.Random,
    old_intelligence: float,
) -> None:
    adaptability_delta = rng.uniform(-0.035, 0.055)
    intelligence_delta = rng.uniform(-0.02, 0.045)
    cooperation_delta = rng.uniform(-0.025, 0.03)
    aggression_delta = rng.uniform(-0.025, 0.025)

    species.adaptability = _clamp(species.adaptability + adaptability_delta)
    species.intelligence = _clamp(species.intelligence + intelligence_delta)
    species.cooperation = _clamp(species.cooperation + cooperation_delta)
    species.aggression = _clamp(species.aggression + aggression_delta)
    species.mutation_rate = _clamp(
        species.mutation_rate + rng.uniform(-0.006, 0.006),
        0.005,
        0.12,
    )

    _add_event(
        universe,
        "mutation",
        f"{species.name} Mutated",
        f"{species.name} changed enough to alter its evolutionary path.",
        {
            "adaptability_delta": round(adaptability_delta, 4),
            "intelligence_delta": round(species.intelligence - old_intelligence, 4),
            "cooperation_delta": round(cooperation_delta, 4),
        },
        "species",
        species.id,
    )


def _apply_species_pressure(
    universe: Universe,
    species: Species,
    rng: random.Random,
) -> None:
    loss_ratio = rng.uniform(0.08, 0.28) * (1.0 - species.resilience * 0.35)
    loss = int(species.population * loss_ratio)
    species.population = max(0, species.population - loss)
    _add_event(
        universe,
        "species_decline",
        f"{species.name} Faced Ecological Pressure",
        f"{species.name} lost population after a harsh environmental cycle.",
        {"population_delta": -loss, "population": species.population},
        "species",
        species.id,
    )


def _update_species_status(species: Species, old_population: int) -> None:
    if species.population <= 0:
        species.status = "extinct"
        species.extinct = True
        return

    if old_population <= 0:
        species.status = "stable"
        return

    change_ratio = (species.population - old_population) / old_population
    if species.population > 160_000 and species.intelligence > 0.45:
        species.status = "thriving"
    elif change_ratio > 0.07:
        species.status = "growing"
    elif change_ratio < -0.07:
        species.status = "declining"
    else:
        species.status = "stable"


def _advance_civilization(
    universe: Universe,
    civilization: Civilization,
    species_by_id: dict[str, Species],
    rng: random.Random,
) -> None:
    if civilization.status == "collapsed" or civilization.extinct:
        civilization.status = "collapsed"
        civilization.extinct = True
        return

    species = species_by_id.get(civilization.species_id)
    old_population = civilization.population
    old_status = civilization.status
    old_knowledge = civilization.knowledge
    civilization.age += 1

    if species is None or species.status == "extinct":
        civilization.population = int(civilization.population * rng.uniform(0.55, 0.82))
        civilization.stability = _clamp(civilization.stability - rng.uniform(0.08, 0.18))
        civilization.resources = _clamp(civilization.resources - rng.uniform(0.04, 0.1))
    else:
        organization_bonus = (civilization.organization - 0.5) * 0.04
        stability_bonus = (civilization.stability - 0.5) * 0.055
        expansion_cost = civilization.expansion * rng.uniform(0.015, 0.055)
        population_growth = rng.uniform(-0.035, 0.065)
        population_growth += organization_bonus + stability_bonus - expansion_cost
        civilization.population = max(
            0,
            int(civilization.population * (1.0 + population_growth)),
        )
        civilization.knowledge = _clamp(
            civilization.knowledge
            + rng.uniform(0.0, 0.035)
            * (0.65 + civilization.creativity + species.intelligence * 0.5)
        )
        civilization.organization = _clamp(
            civilization.organization + rng.uniform(-0.016, 0.024)
        )
        civilization.creativity = _clamp(
            civilization.creativity + rng.uniform(-0.018, 0.026)
        )
        civilization.expansion = _clamp(
            civilization.expansion
            + rng.uniform(-0.015, 0.026)
            * (0.7 + civilization.knowledge)
        )
        civilization.ethics = _clamp(
            civilization.ethics + rng.uniform(-0.018, 0.02)
        )
        civilization.resources = _clamp(
            civilization.resources
            + rng.uniform(-0.052, 0.045)
            - civilization.expansion * 0.018
            + civilization.organization * 0.01
        )
        civilization.stability = _clamp(
            civilization.stability
            + rng.uniform(-0.045, 0.035)
            + (civilization.organization - 0.5) * 0.028
            + (civilization.ethics - 0.5) * 0.022
            - species.aggression * 0.012
            - civilization.expansion * 0.014
        )

    _maybe_civilization_conflict(universe, civilization, species, rng)
    _update_civilization_status(civilization)

    if civilization.status == "collapsed":
        civilization.extinct = True
        civilization.population = 0
        _add_event(
            universe,
            "civilization_collapse",
            f"{civilization.name} Collapsed",
            f"{civilization.name} could no longer sustain its institutions.",
            {
                "population": 0,
                "stability": civilization.stability,
                "resources": civilization.resources,
            },
            "civilization",
            civilization.id,
        )
        return

    if _civilization_is_growing(civilization, old_population, old_knowledge, old_status):
        _add_event(
            universe,
            "civilization_growth",
            f"{civilization.name} Advanced",
            f"{civilization.name} improved its capacity for long-term development.",
            {
                "population_delta": civilization.population - old_population,
                "knowledge_delta": round(civilization.knowledge - old_knowledge, 4),
                "status": civilization.status,
            },
            "civilization",
            civilization.id,
        )
    elif civilization.status == "declining" and old_status != "declining":
        _add_event(
            universe,
            "civilization_conflict",
            f"{civilization.name} Became Unstable",
            f"{civilization.name} entered a visible period of internal strain.",
            {"status": civilization.status, "stability": civilization.stability},
            "civilization",
            civilization.id,
        )


def _maybe_civilization_conflict(
    universe: Universe,
    civilization: Civilization,
    species: Species | None,
    rng: random.Random,
) -> None:
    species_aggression = species.aggression if species is not None else 0.55
    conflict_chance = 0.02
    conflict_chance += civilization.expansion * 0.09
    conflict_chance += max(0.0, 0.45 - civilization.stability) * 0.12
    conflict_chance += max(0.0, 0.45 - civilization.ethics) * 0.08
    conflict_chance += species_aggression * 0.035

    if rng.random() >= conflict_chance:
        return

    population_loss = int(civilization.population * rng.uniform(0.025, 0.12))
    civilization.population = max(0, civilization.population - population_loss)
    civilization.stability = _clamp(civilization.stability - rng.uniform(0.025, 0.11))
    civilization.resources = _clamp(civilization.resources - rng.uniform(0.015, 0.08))
    _add_event(
        universe,
        "civilization_conflict",
        f"{civilization.name} Faced Conflict",
        f"{civilization.name} lost cohesion during a period of civil tension.",
        {
            "population_delta": -population_loss,
            "stability": civilization.stability,
        },
        "civilization",
        civilization.id,
    )


def _update_civilization_status(civilization: Civilization) -> None:
    if (
        civilization.population < 800
        or civilization.stability <= 0.04
        or civilization.resources <= 0.025
    ):
        civilization.status = "collapsed"
        return

    if civilization.stability < 0.26 or civilization.resources < 0.16:
        civilization.status = "declining"
    elif (
        civilization.knowledge > 0.62
        and civilization.organization > 0.52
        and civilization.stability > 0.48
    ):
        civilization.status = "rising"
    else:
        civilization.status = "stable"


def _civilization_is_growing(
    civilization: Civilization,
    old_population: int,
    old_knowledge: float,
    old_status: str,
) -> bool:
    if civilization.status == "rising" and old_status != "rising":
        return True
    if old_population <= 0:
        return False
    population_ratio = (civilization.population - old_population) / old_population
    return population_ratio >= 0.08 or civilization.knowledge - old_knowledge >= 0.035


def _maybe_spawn_civilizations(universe: Universe, rng: random.Random) -> None:
    civilized_species = {
        item.species_id
        for item in universe.civilizations
        if item.status != "collapsed"
    }
    for species in universe.species:
        if species.status == "extinct" or species.id in civilized_species:
            continue
        if species.civilization_id:
            continue
        if (
            species.population < 90_000
            or species.intelligence < 0.56
            or species.cooperation < 0.48
        ):
            continue

        chance = 0.035
        chance += (species.intelligence - 0.56) * 0.2
        chance += (species.cooperation - 0.48) * 0.14
        chance -= species.aggression * 0.035
        if rng.random() > max(0.01, chance):
            continue

        civilization = Civilization(
            id=new_id("civ"),
            name=f"{species.name} Proto-Civilization",
            species_id=species.id,
            population=max(1_000, int(species.population * rng.uniform(0.16, 0.36))),
            knowledge=round(_clamp(0.08 + species.intelligence * rng.uniform(0.18, 0.3)), 3),
            organization=round(_clamp(0.12 + species.cooperation * rng.uniform(0.3, 0.55)), 3),
            creativity=round(
                _clamp(0.18 + species.mutation_rate * 2.4 + rng.uniform(0.0, 0.22)),
                3,
            ),
            stability=round(rng.uniform(0.36, 0.72), 3),
            expansion=round(rng.uniform(0.01, 0.08), 3),
            ethics=round(
                _clamp(0.16 + species.cooperation * 0.55 - species.aggression * 0.12),
                3,
            ),
            status="rising",
            resources=round(rng.uniform(0.35, 0.82), 3),
        )
        species.civilization_id = civilization.id
        universe.civilizations.append(civilization)
        _add_event(
            universe,
            "proto_civilization",
            f"{civilization.name} Emerged",
            f"{species.name} crossed into early organized civilization.",
            {
                "species_population": species.population,
                "civilization_population": civilization.population,
            },
            "civilization",
            civilization.id,
        )


def _maybe_environment_event(universe: Universe, rng: random.Random) -> None:
    if rng.random() >= universe.config.random_event_chance:
        return

    living_species = [item for item in universe.species if item.status != "extinct"]
    active_civs = [
        item for item in universe.civilizations if item.status != "collapsed"
    ]
    event_type = rng.choice(("quiet_age", "species_growth", "species_decline"))
    if active_civs:
        event_type = rng.choice(
            ("quiet_age", "species_growth", "species_decline", "civilization_growth")
        )

    if event_type == "quiet_age":
        for species in living_species:
            species.cooperation = _clamp(species.cooperation + 0.008)
        for civilization in active_civs:
            civilization.stability = _clamp(civilization.stability + 0.018)
        _add_event(
            universe,
            "quiet_age",
            "Quiet Age",
            "Low external pressure allowed gradual stabilization.",
            {"species": len(living_species), "civilizations": len(active_civs)},
        )
    elif event_type == "species_growth" and living_species:
        species = rng.choice(living_species)
        gain = int(species.population * rng.uniform(0.025, 0.09))
        species.population += gain
        species.status = "growing"
        _add_event(
            universe,
            "species_growth",
            f"{species.name} Benefited From Habitat Shift",
            f"{species.name} gained population after favorable habitat changes.",
            {"population_delta": gain, "population": species.population},
            "species",
            species.id,
        )
    elif event_type == "species_decline" and living_species:
        species = rng.choice(living_species)
        loss = int(species.population * rng.uniform(0.025, 0.1))
        species.population = max(0, species.population - loss)
        species.status = "declining" if species.population else "extinct"
        _add_event(
            universe,
            "species_decline",
            f"{species.name} Lost Ground",
            f"{species.name} contracted after unfavorable ecological pressure.",
            {"population_delta": -loss, "population": species.population},
            "species",
            species.id,
        )
    elif active_civs:
        civilization = rng.choice(active_civs)
        civilization.knowledge = _clamp(civilization.knowledge + 0.025)
        civilization.organization = _clamp(civilization.organization + 0.012)
        _add_event(
            universe,
            "civilization_growth",
            f"{civilization.name} Consolidated Knowledge",
            f"{civilization.name} turned stable conditions into practical knowledge.",
            {
                "knowledge": civilization.knowledge,
                "organization": civilization.organization,
            },
            "civilization",
            civilization.id,
        )


def _add_event(
    universe: Universe,
    event_type: str,
    title: str,
    description: str,
    impact: dict[str, object] | None = None,
    target_kind: str = "universe",
    target_id: str | None = None,
) -> None:
    universe.events.append(
        Event(
            year=universe.age,
            type=event_type,
            title=title,
            description=description,
            impact=impact or {},
            target_kind=target_kind,
            target_id=target_id,
        )
    )


def _mutated_value(value: float, rng: random.Random, variation_rate: float) -> float:
    spread = 0.025 + variation_rate * 0.6
    return _clamp(value + rng.uniform(-spread, spread))


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return round(max(low, min(high, value)), 4)
