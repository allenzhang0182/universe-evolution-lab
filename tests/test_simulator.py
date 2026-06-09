from pathlib import Path

from universe_lab.main import main
from universe_lab.modes import create_universe
from universe_lab.simulator import step_universe, summarize_universe
from universe_lab.storage import branch_universe, load_universe, save_universe


def test_life_burst_creation_has_life_seeds():
    universe = create_universe("life_burst", "test", seed=123)

    assert universe.mode == "life_burst"
    assert 6 <= len(universe.species) <= 10
    assert universe.civilizations == []
    assert universe.events[0].type == "genesis"


def test_civilization_seeds_creation_has_civilizations():
    universe = create_universe("civilization_seeds", "civs", seed=456)

    assert universe.mode == "civilization_seeds"
    assert len(universe.civilizations) >= 3
    assert all(species.civilization_id for species in universe.species)


def test_minimal_observer_marks_observer_limited():
    universe = create_universe("minimal_observer", "watch", seed=789)

    assert universe.config.observer_limited is True
    assert universe.events[0].type == "observation_started"


def test_step_advances_turn_and_preserves_valid_counts():
    universe = create_universe("civilization_seeds", "run", seed=42)

    step_universe(universe, steps=5)
    summary = summarize_universe(universe)

    assert summary["turn"] == 5
    assert summary["living_species"] <= summary["species"]
    assert summary["living_civilizations"] <= summary["civilizations"]
    assert all(species.population >= 0 for species in universe.species)
    assert all(civilization.population >= 0 for civilization in universe.civilizations)
    assert len(universe.events) >= 1


def test_storage_round_trip_and_branch(tmp_path: Path):
    run_path = tmp_path / "original.json"
    universe = create_universe("life_burst", "original", seed=7)
    save_universe(universe, run_path)

    loaded = load_universe(run_path)
    branch, branch_path = branch_universe(run_path, "branch", tmp_path / "branch.json")

    assert loaded.name == "original"
    assert loaded.seed == 7
    assert branch.name == "branch"
    assert branch.branch_of == loaded.id
    assert branch_path.exists()
    assert branch.events[-1].type == "branch_created"


def test_cli_create_step_show_and_branch(tmp_path: Path, capsys):
    run_path = tmp_path / "cli.json"
    branch_path = tmp_path / "cli-branch.json"

    assert main(["create", "--mode", "life_burst", "--name", "cli", "--seed", "99", "--output", str(run_path)]) == 0
    assert run_path.exists()

    assert main(["step", "--run", str(run_path), "--steps", "3"]) == 0
    stepped = load_universe(run_path)
    assert stepped.turn == 3

    assert main(["show", "--run", str(run_path), "--events", "2"]) == 0
    output = capsys.readouterr().out
    assert "mode=life_burst" in output
    assert "Recent events:" in output

    assert main(["branch", "--run", str(run_path), "--name", "cli branch", "--output", str(branch_path)]) == 0
    assert load_universe(branch_path).branch_of == stepped.id
