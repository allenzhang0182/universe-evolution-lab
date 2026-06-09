from pathlib import Path

import pytest

from universe_lab.main import main
from universe_lab.modes import VALID_MODES, create_universe
from universe_lab.simulator import step_universe, summarize_universe
from universe_lab.storage import branch_universe, load_universe, save_universe


@pytest.mark.parametrize("mode", VALID_MODES)
def test_create_all_modes_generate_universe(mode: str):
    universe = create_universe(mode, f"{mode}-test", seed=101)

    assert universe.mode == mode
    assert universe.name == f"{mode}-test"
    assert universe.age == 0
    assert universe.events
    assert universe.species


def test_life_burst_species_have_evolution_fields():
    universe = create_universe("life_burst", "life", seed=123)

    assert 6 <= len(universe.species) <= 10
    assert universe.civilizations == []
    for species in universe.species:
        assert species.population > 0
        assert 0 <= species.adaptability <= 1
        assert 0 <= species.intelligence <= 1
        assert 0 <= species.cooperation <= 1
        assert 0 <= species.aggression <= 1
        assert 0 < species.mutation_rate <= 1
        assert species.status in {"alive", "stable", "growing", "declining"}


def test_civilization_seeds_create_three_distinct_civilizations():
    universe = create_universe("civilization_seeds", "civs", seed=456)

    assert len(universe.civilizations) == 3
    assert all(species.civilization_id for species in universe.species)
    for civilization in universe.civilizations:
        assert civilization.population > 0
        assert 0 <= civilization.knowledge <= 1
        assert 0 <= civilization.organization <= 1
        assert 0 <= civilization.creativity <= 1
        assert 0 <= civilization.stability <= 1
        assert 0 <= civilization.expansion <= 1
        assert 0 <= civilization.ethics <= 1
        assert civilization.status in {"rising", "stable", "declining"}


@pytest.mark.parametrize("mode", VALID_MODES)
def test_step_increases_age_and_events(mode: str):
    universe = create_universe(mode, "run", seed=42)
    starting_age = universe.age
    starting_events = len(universe.events)

    step_universe(universe, steps=5)
    summary = summarize_universe(universe)

    assert universe.age == starting_age + 5
    assert summary["age"] == universe.age
    assert len(universe.events) >= starting_events + 5
    assert all(event.year <= universe.age for event in universe.events)


def test_life_burst_long_run_remains_valid_and_may_spawn_civilization():
    universe = create_universe("life_burst", "long-life", seed=77)

    step_universe(universe, steps=90)

    assert universe.age == 90
    assert len(universe.civilizations) >= 0
    assert all(species.population >= 0 for species in universe.species)
    assert all(civilization.population >= 0 for civilization in universe.civilizations)
    assert all(
        civilization.status in {"rising", "stable", "declining", "collapsed"}
        for civilization in universe.civilizations
    )


def test_branch_copies_history_with_new_name_and_id(tmp_path: Path):
    run_path = tmp_path / "original.json"
    branch_path = tmp_path / "branch.json"
    universe = create_universe("civilization_seeds", "original", seed=7)
    step_universe(universe, steps=8)
    save_universe(universe, run_path)
    loaded = load_universe(run_path)

    branch, saved_branch_path = branch_universe(run_path, "branch", branch_path)

    assert saved_branch_path == branch_path
    assert branch.name == "branch"
    assert branch.id != loaded.id
    assert branch.branch_of == loaded.id
    assert branch.age == loaded.age
    assert branch.turn == loaded.turn
    assert len(branch.species) == len(loaded.species)
    assert len(branch.civilizations) == len(loaded.civilizations)
    assert [event.to_dict() for event in branch.events[:-1]] == [
        event.to_dict() for event in loaded.events
    ]
    assert branch.events[-1].type == "branch_created"


def test_json_save_load_preserves_data(tmp_path: Path):
    run_path = tmp_path / "round-trip.json"
    universe = create_universe("minimal_observer", "observer", seed=9)
    step_universe(universe, steps=3)

    save_universe(universe, run_path)
    loaded = load_universe(run_path)

    assert loaded.to_dict() == universe.to_dict()


def test_cli_create_step_show_and_branch(tmp_path: Path, capsys):
    run_path = tmp_path / "cli.json"
    branch_path = tmp_path / "cli-branch.json"

    assert (
        main(
            [
                "create",
                "--mode",
                "life_burst",
                "--name",
                "cli",
                "--seed",
                "99",
                "--output",
                str(run_path),
            ]
        )
        == 0
    )
    assert run_path.exists()

    assert main(["step", "--run", str(run_path), "--steps", "3"]) == 0
    stepped = load_universe(run_path)
    assert stepped.age == 3

    assert main(["show", "--run", str(run_path)]) == 0
    output = capsys.readouterr().out
    assert "Universe name: cli" in output
    assert "Mode: life_burst" in output
    assert "Age: 3" in output
    assert "Recent events:" in output

    assert (
        main(
            [
                "branch",
                "--run",
                str(run_path),
                "--name",
                "cli branch",
                "--output",
                str(branch_path),
            ]
        )
        == 0
    )
    assert load_universe(branch_path).branch_of == stepped.id
