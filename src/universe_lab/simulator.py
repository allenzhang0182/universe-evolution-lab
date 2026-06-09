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
    living_species = sum(1 for item in universe.species if not item.extinct)
    living_civilizations = sum(1 for item in universe.civilizations if not item.extinct)
    return {
        "name": universe.name,
        "mode": universe.mode,
        "turn": universe.turn,
        "species": len(universe.species),
        "living_species": living_species,
        "civilizations": len(universe.civilizations),
        "living_civilizations": living_civilizations,
        "events": len(universe.events),
    }


def _step_once(universe: Universe) -> None:
    universe.turn += 1
    rng = random.Random(universe.seed + universe.turn * 7919)

    species_by_id = {item.id: item for item in universe.species}
    for species in universe.species:
        _advance_species(universe, species, rng)

    for civilization in universe.civilizations:
        _advance_civilization(universe, civilization, species_by_id, rng)

    _maybe_spawn_civilizations(universe, rng)
    _maybe_global_event(universe, rng)


def _advance_species(universe: Universe, species: Species, rng: random.Random) -> None:
    if species.extinct:
        return

    species.age += 1
    growth = rng.uniform(-0.06, 0.13)
    growth += (species.adaptability - 0.5) * 0.08
    growth += (species.resilience - 0.5) * 0.05
    growth -= species.aggression * rng.uniform(0.0, 0.035)

    old_population = species.population
    species.population = max(0, int(species.population * (1.0 + growth)))
    species.intelligence = _clamp(
        species.intelligence + rng.uniform(-0.015, 0.035) * species.adaptability
    )
    species.adaptability = _clamp(species.adaptability + rng.uniform(-0.01, 0.015))
    species.resilience = _clamp(species.resilience + rng.uniform(-0.012, 0.012))

    if old_population and species.population > old_population * 1.35:
        universe.events.append(
            Event(
                turn=universe.turn,
                type="population_bloom",
                description=f"{species.name} expanded rapidly in {species.environment_affinity} habitats.",
                target_kind="species",
                target_id=species.id,
                impact={"population": species.population - old_population},
            )
        )

    if rng.random() < 0.055:
        loss_ratio = rng.uniform(0.18, 0.52) * (1.0 - species.resilience * 0.45)
        loss = int(species.population * loss_ratio)
        species.population = max(0, species.population - loss)
        universe.events.append(
            Event(
                turn=universe.turn,
                type="biosphere_shock",
                description=f"{species.name} suffered a biosphere shock.",
                target_kind="species",
                target_id=species.id,
                impact={"population": -loss},
            )
        )

    if species.population < 500:
        species.extinct = True
        species.population = 0
        universe.events.append(
            Event(
                turn=universe.turn,
                type="extinction",
                description=f"{species.name} vanished from the record.",
                target_kind="species",
                target_id=species.id,
            )
        )


def _advance_civilization(
    universe: Universe,
    civilization: Civilization,
    species_by_id: dict[str, Species],
    rng: random.Random,
) -> None:
    if civilization.extinct:
        return

    species = species_by_id.get(civilization.species_id)
    civilization.age += 1

    if species is None or species.extinct:
        civilization.population = int(civilization.population * rng.uniform(0.55, 0.82))
        civilization.stability = _clamp(civilization.stability - rng.uniform(0.08, 0.18))
    else:
        resource_pressure = 1.0 if civilization.resources > 0.18 else 0.74
        population_growth = rng.uniform(-0.03, 0.08) * resource_pressure
        population_growth += (civilization.stability - 0.5) * 0.035
        civilization.population = max(
            0,
            int(civilization.population * (1.0 + population_growth)),
        )
        civilization.technology = _clamp(
            civilization.technology
            + rng.uniform(0.0, 0.045) * (0.55 + species.intelligence)
        )
        civilization.culture = _clamp(civilization.culture + rng.uniform(-0.02, 0.025))
        civilization.stability = _clamp(
            civilization.stability
            + rng.uniform(-0.035, 0.035)
            + (civilization.culture - species.aggression) * 0.01
        )
        civilization.expansion = _clamp(
            civilization.expansion + rng.uniform(-0.01, 0.03) * civilization.resources
        )
        civilization.resources = _clamp(
            civilization.resources
            + rng.uniform(-0.05, 0.045)
            - civilization.expansion * 0.018
        )

    _maybe_civilization_event(universe, civilization, rng)

    if civilization.population < 800 or civilization.stability <= 0.03:
        civilization.extinct = True
        civilization.population = 0
        universe.events.append(
            Event(
                turn=universe.turn,
                type="civilization_collapse",
                description=f"{civilization.name} collapsed.",
                target_kind="civilization",
                target_id=civilization.id,
            )
        )


def _maybe_spawn_civilizations(universe: Universe, rng: random.Random) -> None:
    civilized_species = {
        item.species_id for item in universe.civilizations if not item.extinct
    }
    for species in universe.species:
        if species.extinct or species.id in civilized_species or species.civilization_id:
            continue
        if species.population < 45_000 or species.intelligence < 0.45:
            continue

        chance = 0.04 + (species.intelligence - 0.45) * 0.18
        if rng.random() > chance:
            continue

        civilization = Civilization(
            id=new_id("civ"),
            name=f"{species.name} First Society",
            species_id=species.id,
            population=max(1_000, int(species.population * rng.uniform(0.18, 0.42))),
            technology=round(rng.uniform(0.02, 0.08), 3),
            culture=round(rng.uniform(0.25, 0.7), 3),
            stability=round(rng.uniform(0.35, 0.78), 3),
            expansion=round(rng.uniform(0.0, 0.07), 3),
            resources=round(rng.uniform(0.35, 0.85), 3),
        )
        species.civilization_id = civilization.id
        universe.civilizations.append(civilization)
        universe.events.append(
            Event(
                turn=universe.turn,
                type="civilization_emerged",
                description=f"{civilization.name} emerged from {species.name}.",
                target_kind="civilization",
                target_id=civilization.id,
            )
        )


def _maybe_civilization_event(
    universe: Universe,
    civilization: Civilization,
    rng: random.Random,
) -> None:
    if rng.random() < 0.05 + civilization.technology * 0.02:
        universe.events.append(
            Event(
                turn=universe.turn,
                type="discovery",
                description=f"{civilization.name} made a useful discovery.",
                target_kind="civilization",
                target_id=civilization.id,
                impact={"technology": round(civilization.technology, 3)},
            )
        )

    if civilization.resources < 0.16 and rng.random() < 0.3:
        civilization.stability = _clamp(civilization.stability - rng.uniform(0.03, 0.12))
        universe.events.append(
            Event(
                turn=universe.turn,
                type="resource_crisis",
                description=f"{civilization.name} entered a resource crisis.",
                target_kind="civilization",
                target_id=civilization.id,
                impact={"stability": round(civilization.stability, 3)},
            )
        )

    if civilization.stability > 0.82 and civilization.resources > 0.45:
        if rng.random() < 0.08:
            universe.events.append(
                Event(
                    turn=universe.turn,
                    type="golden_age",
                    description=f"{civilization.name} entered a golden age.",
                    target_kind="civilization",
                    target_id=civilization.id,
                )
            )


def _maybe_global_event(universe: Universe, rng: random.Random) -> None:
    if rng.random() >= universe.config.random_event_chance:
        return

    event_type = rng.choice(("quiet_era", "stellar_weather", "resource_windfall"))
    if event_type == "quiet_era":
        for civilization in universe.civilizations:
            if not civilization.extinct:
                civilization.stability = _clamp(civilization.stability + 0.025)
        description = "A quiet era slightly stabilized active civilizations."
    elif event_type == "stellar_weather":
        for species in universe.species:
            if not species.extinct:
                loss = int(species.population * rng.uniform(0.01, 0.06))
                species.population = max(0, species.population - loss)
        description = "Stellar weather disturbed several biospheres."
    else:
        for civilization in universe.civilizations:
            if not civilization.extinct:
                civilization.resources = _clamp(civilization.resources + 0.08)
        description = "A resource windfall improved active civilization reserves."

    universe.events.append(
        Event(turn=universe.turn, type=event_type, description=description)
    )


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return round(max(low, min(high, value)), 4)
