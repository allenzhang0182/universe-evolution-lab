"""Initial universe factories for the supported simulation modes."""

from __future__ import annotations

import random
from typing import Callable

from .models import (
    Civilization,
    EmergentStructure,
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
_STRUCTURE_ROOTS = (
    "Lattice",
    "Veil",
    "Current",
    "Matrix",
    "Field",
    "Cluster",
    "Filament",
    "Phase",
)
_SCALES = ("micro", "local", "planetary", "stellar", "cosmic")
_SUBSTRATES = (
    "mineral",
    "chemical",
    "organic",
    "informational",
    "quantum",
    "gravitational",
    "cosmic",
    "unknown",
)


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
    structures = [_random_structure(rng, i) for i in range(rng.randint(6, 12))]
    universe = _base_universe(
        name,
        "life_burst",
        seed,
        config,
        structures=structures,
    )
    universe.events.append(
        Event(
            year=0,
            type="structure_formed",
            title="Complexity Field Initialized",
            description=f"{len(structures)} non-living structures formed in varied environments.",
            impact={"structures": len(structures)},
        )
    )
    return universe


def create_civilization_seeds(name: str, seed: int) -> Universe:
    rng = random.Random(seed)
    config = SimulationConfig(mode="civilization_seeds", name=name, seed=seed)
    species = [_random_species(rng, i, mature=True) for i in range(3)]
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
            year=0,
            type="civilization_growth",
            title="Civilization Seeds Established",
            description="Three early civilizations began developing independently.",
            impact={"civilizations": len(civilizations)},
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
            year=0,
            type="quiet_age",
            title="Observation Began",
            description="An observer protocol began with no direct interventions allowed.",
            impact={"observer_limited": True},
        )
    )
    return universe


def _base_universe(
    name: str,
    mode: str,
    seed: int,
    config: SimulationConfig,
    species: list[Species] | None = None,
    civilizations: list[Civilization] | None = None,
    structures: list[EmergentStructure] | None = None,
) -> Universe:
    return Universe(
        id=new_id("uni"),
        name=name,
        mode=mode,
        turn=0,
        age=0,
        seed=seed,
        config=config,
        structures=structures or [],
        species=species or [],
        civilizations=civilizations or [],
    )


def _random_structure(rng: random.Random, index: int) -> EmergentStructure:
    base_complexity = rng.uniform(0.16, 0.42)
    stability = rng.uniform(0.18, 0.52)
    classification = (
        "complex_structure"
        if base_complexity >= 0.35 and stability >= 0.25
        else "inert"
    )
    return EmergentStructure(
        id=new_id("str"),
        name=f"{rng.choice(_STRUCTURE_ROOTS)}-{index + 1}",
        age=0,
        scale=rng.choice(_SCALES),
        substrate=rng.choice(_SUBSTRATES),
        complexity=round(base_complexity, 3),
        stability=round(stability, 3),
        energy_flow=round(rng.uniform(0.08, 0.42), 3),
        information_retention=round(rng.uniform(0.05, 0.4), 3),
        replication_potential=round(rng.uniform(0.02, 0.32), 3),
        variation_rate=round(rng.uniform(0.015, 0.09), 3),
        boundary_strength=round(rng.uniform(0.08, 0.42), 3),
        adaptation_score=round(rng.uniform(0.02, 0.3), 3),
        status="active",
        classification=classification,
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
        cooperation=round(rng.uniform(0.15, 0.85), 3),
        aggression=round(rng.uniform(0.05, 0.85), 3),
        mutation_rate=round(rng.uniform(0.01, 0.09), 3),
        status="stable" if mature else "alive",
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
        knowledge=round(rng.uniform(0.12, 0.45), 3),
        organization=round(rng.uniform(0.2, 0.72), 3),
        creativity=round(rng.uniform(0.2, 0.8), 3),
        stability=round(rng.uniform(0.35, 0.85), 3),
        expansion=round(rng.uniform(0.02, 0.18), 3),
        ethics=round(rng.uniform(0.18, 0.85), 3),
        status=rng.choice(("rising", "stable", "stable")),
        resources=round(rng.uniform(0.25, 0.85), 3),
        age=rng.randint(3, 40),
    )
