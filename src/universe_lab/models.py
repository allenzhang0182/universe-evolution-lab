"""Core dataclasses for the universe evolution lab."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def new_id(prefix: str) -> str:
    """Return a short stable-looking identifier for saved objects."""
    return f"{prefix}_{uuid4().hex[:10]}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Event:
    turn: int
    type: str
    description: str
    target_kind: str = "universe"
    target_id: str | None = None
    impact: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        return cls(
            turn=int(data.get("turn", 0)),
            type=str(data.get("type", "unknown")),
            description=str(data.get("description", "")),
            target_kind=str(data.get("target_kind", "universe")),
            target_id=data.get("target_id"),
            impact=dict(data.get("impact", {})),
        )


@dataclass
class Species:
    id: str
    name: str
    population: int
    adaptability: float
    intelligence: float
    aggression: float
    resilience: float
    environment_affinity: str
    age: int = 0
    extinct: bool = False
    civilization_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Species":
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            population=int(data.get("population", 0)),
            adaptability=float(data.get("adaptability", 0.5)),
            intelligence=float(data.get("intelligence", 0.1)),
            aggression=float(data.get("aggression", 0.3)),
            resilience=float(data.get("resilience", 0.5)),
            environment_affinity=str(data.get("environment_affinity", "temperate")),
            age=int(data.get("age", 0)),
            extinct=bool(data.get("extinct", False)),
            civilization_id=data.get("civilization_id"),
        )


@dataclass
class Civilization:
    id: str
    name: str
    species_id: str
    population: int
    technology: float
    culture: float
    stability: float
    expansion: float
    resources: float
    age: int = 0
    extinct: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Civilization":
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            species_id=str(data["species_id"]),
            population=int(data.get("population", 0)),
            technology=float(data.get("technology", 0.0)),
            culture=float(data.get("culture", 0.5)),
            stability=float(data.get("stability", 0.5)),
            expansion=float(data.get("expansion", 0.0)),
            resources=float(data.get("resources", 0.5)),
            age=int(data.get("age", 0)),
            extinct=bool(data.get("extinct", False)),
        )


@dataclass
class SimulationConfig:
    mode: str
    name: str
    seed: int
    random_event_chance: float = 0.22
    max_events: int = 250
    observer_limited: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SimulationConfig":
        return cls(
            mode=str(data.get("mode", "life_burst")),
            name=str(data.get("name", "unnamed")),
            seed=int(data.get("seed", 0)),
            random_event_chance=float(data.get("random_event_chance", 0.22)),
            max_events=int(data.get("max_events", 250)),
            observer_limited=bool(data.get("observer_limited", False)),
        )


@dataclass
class Universe:
    id: str
    name: str
    mode: str
    turn: int
    seed: int
    config: SimulationConfig
    species: list[Species] = field(default_factory=list)
    civilizations: list[Civilization] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    branch_of: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "mode": self.mode,
            "turn": self.turn,
            "seed": self.seed,
            "config": self.config.to_dict(),
            "species": [item.to_dict() for item in self.species],
            "civilizations": [item.to_dict() for item in self.civilizations],
            "events": [item.to_dict() for item in self.events],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "branch_of": self.branch_of,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Universe":
        config_data = data.get("config") or {}
        if "mode" not in config_data:
            config_data["mode"] = data.get("mode", "life_burst")
        if "name" not in config_data:
            config_data["name"] = data.get("name", "unnamed")
        if "seed" not in config_data:
            config_data["seed"] = data.get("seed", 0)

        return cls(
            id=str(data["id"]),
            name=str(data.get("name", "unnamed")),
            mode=str(data.get("mode", config_data["mode"])),
            turn=int(data.get("turn", 0)),
            seed=int(data.get("seed", config_data["seed"])),
            config=SimulationConfig.from_dict(config_data),
            species=[Species.from_dict(item) for item in data.get("species", [])],
            civilizations=[
                Civilization.from_dict(item)
                for item in data.get("civilizations", [])
            ],
            events=[Event.from_dict(item) for item in data.get("events", [])],
            created_at=str(data.get("created_at", utc_now())),
            updated_at=str(data.get("updated_at", utc_now())),
            branch_of=data.get("branch_of"),
        )
