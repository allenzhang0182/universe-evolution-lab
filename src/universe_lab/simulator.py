"""Turn-based simulation rules for the MVP."""

from __future__ import annotations

import random

from .models import Civilization, Event, Species, Universe, new_id, utc_now


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
    living_species = sum(1 for item in universe.species if item.status != "extinct")
    living_civilizations = sum(
        1 for item in universe.civilizations if item.status != "collapsed"
    )
    return {
        "name": universe.name,
        "mode": universe.mode,
        "turn": universe.turn,
        "age": universe.age,
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


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return round(max(low, min(high, value)), 4)
