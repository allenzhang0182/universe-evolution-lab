"""Initial universe factories for the supported simulation modes."""

from __future__ import annotations

import random
from typing import Callable

from .models import (
    Civilization,
    Event,
    SimulationConfig,
    Species,
    Universe,
    new_id,
)


VALID_MODES = ("life_burst", "civilization_seeds", "minimal_observer")

_SPECIES_ROOTS = (
    "Aster",
    "Luma",
    "Nere",
    "Orin",
    "Sol",
    "Veya",
    "Kora",
    "Ixo",
    "Mara",
    "Tala",
)
_CIV_SUFFIXES = ("Hearth", "Concord", "Array", "League", "Kinship")
_ENVIRONMENTS = ("oceanic", "temperate", "desert", "ice", "volcanic", "orbital")


def create_universe(mode: str, name: str, seed: int | None = None) -> Universe:
    factories: dict[str, Callable[[str, int], Universe]] = {
        "life_burst": create_life_burst,
        "civilization_seeds": create_civilization_seeds,
        "minimal_observer": create_minimal_observer,
    }
    if mode not in factories:
        choices = ", ".join(VALID_MODES)
        raise ValueError(f"Unknown mode '{mode}'. Expected one of: {choices}")
    resolved_seed = seed if seed is not None else random.SystemRandom().randrange(1, 10**9)
    return factories[mode](name, resolved_seed)


def create_life_burst(name: str, seed: int) -> Universe:
    rng = random.Random(seed)
    config = SimulationConfig(mode="life_burst", name=name, seed=seed)
    species = [_random_species(rng, i) for i in range(rng.randint(6, 10))]
    universe = _base_universe(name, "life_burst", seed, config, species)
    universe.events.append(
        Event(
            turn=0,
            type="genesis",
            description=f"{len(species)} life seeds emerged across young worlds.",
        )
    )
    return universe


def create_civilization_seeds(name: str, seed: int) -> Universe:
    rng = random.Random(seed)
    config = SimulationConfig(mode="civilization_seeds", name=name, seed=seed)
    species_count = rng.randint(3, 5)
    species = [_random_species(rng, i, mature=True) for i in range(species_count)]
    civilizations: list[Civilization] = []

    for index, item in enumerate(species):
        civ = _random_civilization(rng, item, index)
        item.civilization_id = civ.id
        civilizations.append(civ)

    universe = _base_universe(
        name,
        "civilization_seeds",
        seed,
        config,
        species,
        civilizations,
    )
    universe.events.append(
        Event(
            turn=0,
            type="civilization_seed",
            description=f"{len(civilizations)} primitive civilizations entered history.",
        )
    )
    return universe


def create_minimal_observer(name: str, seed: int) -> Universe:
    rng = random.Random(seed)
    config = SimulationConfig(
        mode="minimal_observer",
        name=name,
        seed=seed,
        random_event_chance=0.18,
        observer_limited=True,
    )
    species = [_random_species(rng, i) for i in range(rng.randint(2, 4))]
    universe = _base_universe(name, "minimal_observer", seed, config, species)
    universe.events.append(
        Event(
            turn=0,
            type="observation_started",
            description="An observer protocol began with no direct interventions allowed.",
        )
    )
    return universe


def _base_universe(
    name: str,
    mode: str,
    seed: int,
    config: SimulationConfig,
    species: list[Species],
    civilizations: list[Civilization] | None = None,
) -> Universe:
    return Universe(
        id=new_id("uni"),
        name=name,
        mode=mode,
        turn=0,
        seed=seed,
        config=config,
        species=species,
        civilizations=civilizations or [],
    )


def _random_species(rng: random.Random, index: int, mature: bool = False) -> Species:
    root = rng.choice(_SPECIES_ROOTS)
    suffix = rng.choice(("ans", "ites", "ari", "ori", "ae", "im"))
    intelligence_base = rng.uniform(0.08, 0.32)
    population = rng.randint(4_000, 80_000)

    if mature:
        intelligence_base = rng.uniform(0.42, 0.68)
        population = rng.randint(80_000, 900_000)

    return Species(
        id=new_id("sp"),
        name=f"{root}{suffix}-{index + 1}",
        population=population,
        adaptability=round(rng.uniform(0.2, 0.9), 3),
        intelligence=round(intelligence_base, 3),
        aggression=round(rng.uniform(0.05, 0.85), 3),
        resilience=round(rng.uniform(0.2, 0.9), 3),
        environment_affinity=rng.choice(_ENVIRONMENTS),
    )


def _random_civilization(
    rng: random.Random,
    species: Species,
    index: int,
) -> Civilization:
    civ_name = f"{species.name} {rng.choice(_CIV_SUFFIXES)}"
    return Civilization(
        id=new_id("civ"),
        name=civ_name,
        species_id=species.id,
        population=max(1_000, int(species.population * rng.uniform(0.35, 0.9))),
        technology=round(rng.uniform(0.04, 0.22), 3),
        culture=round(rng.uniform(0.25, 0.75), 3),
        stability=round(rng.uniform(0.35, 0.85), 3),
        expansion=round(rng.uniform(0.02, 0.18), 3),
        resources=round(rng.uniform(0.25, 0.85), 3),
        age=rng.randint(3, 40),
    )
