import json
from pathlib import Path

import pytest

from universe_lab.batch import format_batch_summary, run_batch, summarize_run_directory
from universe_lab.main import main
from universe_lab.modes import VALID_MODES, create_universe
from universe_lab.reporting import build_stats, format_timeline
from universe_lab.simulator import step_universe, summarize_universe
from universe_lab.storage import branch_universe, load_universe, save_universe


@pytest.mark.parametrize("mode", VALID_MODES)
def test_create_all_modes_generate_universe(mode: str):
    universe = create_universe(mode, f"{mode}-test", seed=101)

    assert universe.mode == mode
    assert universe.name == f"{mode}-test"
    assert universe.age == 0
    assert universe.events
    assert universe.structures or universe.species or universe.civilizations


def test_life_burst_starts_with_emergent_structures():
    universe = create_universe("life_burst", "life", seed=123)

    assert 6 <= len(universe.structures) <= 12
    assert universe.species == []
    assert universe.populations == []
    assert universe.civilizations == []
    assert universe.events[0].type == "structure_formed"
    for structure in universe.structures:
        assert structure.status == "active"
        assert structure.classification in {"inert", "complex_structure"}
        assert 0 <= structure.complexity <= 1
        assert 0 <= structure.stability <= 1
        assert 0 <= structure.energy_flow <= 1
        assert 0 <= structure.information_retention <= 1
        assert 0 <= structure.replication_potential <= 1
        assert 0 < structure.variation_rate <= 1
        assert 0 <= structure.boundary_strength <= 1
        assert 0 <= structure.adaptation_score <= 1


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
    assert universe.structures
    assert len(universe.populations) >= 0
    assert {
        structure.classification for structure in universe.structures
    } <= {
        "inert",
        "complex_structure",
        "self_maintaining",
        "proto_life",
        "life_lineage",
    }
    assert len(universe.civilizations) >= 0
    assert all(species.population >= 0 for species in universe.species)
    assert all(civilization.population >= 0 for civilization in universe.civilizations)
    assert all(
        civilization.status in {"rising", "stable", "declining", "collapsed"}
        for civilization in universe.civilizations
    )


def test_life_burst_step_changes_structure_state():
    universe = create_universe("life_burst", "structure-step", seed=88)
    before = [
        (structure.age, structure.complexity, structure.stability)
        for structure in universe.structures
    ]
    starting_events = len(universe.events)

    step_universe(universe, steps=3)
    after = [
        (structure.age, structure.complexity, structure.stability)
        for structure in universe.structures[: len(before)]
    ]

    assert universe.age == 3
    assert len(universe.events) > starting_events
    assert any(item[0] > 0 for item in after)
    assert before != after


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


@pytest.mark.parametrize("mode", VALID_MODES)
def test_cli_stats_runs_for_all_modes(mode: str, tmp_path: Path, capsys):
    run_path = tmp_path / f"{mode}.json"
    universe = create_universe(mode, f"{mode}-stats", seed=202)
    step_universe(universe, steps=2)
    save_universe(universe, run_path)

    assert main(["stats", "--run", str(run_path)]) == 0
    output = capsys.readouterr().out

    assert f"Universe name: {mode}-stats" in output
    assert f"Mode: {mode}" in output
    assert "Events count by type:" in output


def test_stats_handles_run_without_civilizations(tmp_path: Path, capsys):
    run_path = tmp_path / "no-civs.json"
    universe = create_universe("life_burst", "no-civs", seed=303)
    save_universe(universe, run_path)

    assert main(["stats", "--run", str(run_path)]) == 0
    output = capsys.readouterr().out

    assert "Civilizations total: 0" in output
    assert "Civilizations active: 0" in output
    assert "Civilizations collapsed: 0" in output
    assert "Total civilization population: 0" in output
    assert "Average civilization knowledge: 0.00" in output


def test_timeline_outputs_events(tmp_path: Path, capsys):
    run_path = tmp_path / "timeline.json"
    universe = create_universe("minimal_observer", "timeline", seed=404)
    step_universe(universe, steps=3)
    save_universe(universe, run_path)

    assert main(["timeline", "--run", str(run_path)]) == 0
    output = capsys.readouterr().out

    assert "Timeline for timeline" in output
    assert "- year 0:" in output
    assert any(line.startswith("- year 3:") for line in output.splitlines())


def test_timeline_limit_outputs_recent_events_in_year_order(tmp_path: Path, capsys):
    run_path = tmp_path / "timeline-limit.json"
    universe = create_universe("life_burst", "timeline-limit", seed=505)
    step_universe(universe, steps=8)
    save_universe(universe, run_path)

    assert main(["timeline", "--run", str(run_path), "--limit", "4"]) == 0
    output = capsys.readouterr().out
    event_lines = [line for line in output.splitlines() if line.startswith("- year")]
    years = [int(line.split(":", maxsplit=1)[0].removeprefix("- year ")) for line in event_lines]

    assert len(event_lines) == 4
    assert years == sorted(years)


def test_json_load_then_stats_are_reasonable(tmp_path: Path):
    run_path = tmp_path / "stats-round-trip.json"
    universe = create_universe("civilization_seeds", "stats-round-trip", seed=606)
    step_universe(universe, steps=5)
    save_universe(universe, run_path)

    loaded = load_universe(run_path)
    stats = build_stats(loaded)

    assert stats["universe_name"] == "stats-round-trip"
    assert stats["age"] == 5
    assert stats["species_total"] == len(loaded.species)
    assert stats["species_active"] + stats["species_extinct"] == len(loaded.species)
    assert stats["civilizations_total"] == len(loaded.civilizations)
    assert (
        stats["civilizations_active"] + stats["civilizations_collapsed"]
        == len(loaded.civilizations)
    )
    assert stats["events_total"] == len(loaded.events)
    assert stats["events_count_by_type"]


def test_format_timeline_handles_empty_events():
    universe = create_universe("life_burst", "empty-events", seed=707)
    universe.events = []

    output = format_timeline(universe)

    assert "- no events recorded" in output


def test_export_generates_analysis_json(tmp_path: Path):
    run_path = tmp_path / "run.json"
    export_path = tmp_path / "nested" / "export.json"
    universe = create_universe("life_burst", "export-test", seed=808)
    step_universe(universe, steps=4)
    save_universe(universe, run_path)

    assert main(["export", "--run", str(run_path), "--out", str(export_path)]) == 0

    exported = json.loads(export_path.read_text(encoding="utf-8"))
    assert export_path.exists()
    assert set(exported) >= {
        "universe",
        "species_summary",
        "civilization_summary",
        "event_summary",
        "timeline",
    }
    assert exported["universe"]["name"] == "export-test"
    assert exported["species_summary"]["total"] == len(universe.species)
    assert exported["civilization_summary"]["total"] == len(universe.civilizations)
    assert exported["event_summary"]["total"] == len(universe.events)
    assert exported["timeline"] == sorted(
        exported["timeline"],
        key=lambda event: event["year"],
    )


def test_report_generates_markdown(tmp_path: Path):
    run_path = tmp_path / "report-run.json"
    report_path = tmp_path / "docs" / "report.md"
    universe = create_universe("minimal_observer", "report-test", seed=909)
    step_universe(universe, steps=3)
    save_universe(universe, run_path)

    assert main(["report", "--run", str(run_path), "--out", str(report_path)]) == 0

    report = report_path.read_text(encoding="utf-8")
    assert "# Universe Report: report-test" in report
    assert "## Basic Info" in report
    assert "## Recent Timeline" in report
    assert "## Civilization Overview" in report
    assert "- none" in report


def test_compare_two_branches_outputs_differences(tmp_path: Path, capsys):
    run_a_path = tmp_path / "a.json"
    run_b_path = tmp_path / "b.json"
    universe = create_universe("civilization_seeds", "compare-a", seed=1001)
    step_universe(universe, steps=5)
    save_universe(universe, run_a_path)
    branch_universe(run_a_path, "compare-b", run_b_path)
    branch = load_universe(run_b_path)
    step_universe(branch, steps=4)
    save_universe(branch, run_b_path)

    assert (
        main(
            [
                "compare",
                "--run-a",
                str(run_a_path),
                "--run-b",
                str(run_b_path),
            ]
        )
        == 0
    )
    output = capsys.readouterr().out

    assert "Universe Comparison" in output
    assert "A: compare-a" in output
    assert "B: compare-b" in output
    assert "Differences (B - A):" in output
    assert "Species active:" in output
    assert "Civilizations active:" in output
    assert "Events total:" in output
    assert "Event type count differences (B - A):" in output
    assert "Conclusion:" in output


def test_batch_generates_requested_run_files(tmp_path: Path):
    results = run_batch(
        mode="life_burst",
        count=3,
        steps=2,
        prefix="batch_unit",
        run_dir=tmp_path,
    )

    assert len(results) == 3
    assert [result.name for result in results] == [
        "batch_unit_001",
        "batch_unit_002",
        "batch_unit_003",
    ]
    for result in results:
        assert result.path.exists()
        loaded = load_universe(result.path)
        assert loaded.age == 2
        assert result.age == 2


def test_batch_allows_zero_steps(tmp_path: Path):
    results = run_batch(
        mode="minimal_observer",
        count=1,
        steps=0,
        prefix="zero_step",
        run_dir=tmp_path,
    )

    loaded = load_universe(results[0].path)
    assert loaded.age == 0
    assert loaded.events


def test_batch_rejects_invalid_count(tmp_path: Path):
    with pytest.raises(ValueError, match="count"):
        run_batch(
            mode="life_burst",
            count=0,
            steps=1,
            prefix="bad_batch",
            run_dir=tmp_path,
        )


def test_summary_reads_multiple_runs_and_aggregates(tmp_path: Path):
    run_batch(
        mode="life_burst",
        count=4,
        steps=3,
        prefix="summary_unit",
        run_dir=tmp_path,
    )

    summary = summarize_run_directory(tmp_path, "summary_unit")

    assert summary["runs_count"] == 4
    assert summary["modes_involved"] == ["life_burst"]
    assert summary["average_age"] == 3.0
    assert summary["average_active_structures"] > 0
    assert summary["average_events_per_run"] >= 4.0
    assert summary["event_counts_by_type"]
    assert "most active species" in summary["interesting_runs"]
    assert "most events" in summary["interesting_runs"]


def test_summary_without_matching_files_is_friendly(tmp_path: Path, capsys):
    summary = summarize_run_directory(tmp_path, "missing_batch")
    text = format_batch_summary(summary)

    assert summary["runs_count"] == 0
    assert "No runs found for prefix 'missing_batch'" in text
    assert (
        main(
            [
                "summary",
                "--runs",
                str(tmp_path),
                "--prefix",
                "missing_batch",
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert "No runs found for prefix 'missing_batch'" in output


def test_summary_out_generates_markdown(tmp_path: Path, capsys):
    run_batch(
        mode="civilization_seeds",
        count=2,
        steps=2,
        prefix="summary_out",
        run_dir=tmp_path,
    )
    out_path = tmp_path / "docs" / "summary.md"

    assert (
        main(
            [
                "summary",
                "--runs",
                str(tmp_path),
                "--prefix",
                "summary_out",
                "--out",
                str(out_path),
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    report = out_path.read_text(encoding="utf-8")

    assert out_path.exists()
    assert "summary report:" in output
    assert "# Batch Summary: summary_out" in report
    assert "## Overview" in report
    assert "## Event Counts" in report
    assert "## Interesting Runs" in report


def test_old_json_without_structures_or_populations_loads(tmp_path: Path):
    run_path = tmp_path / "old-run.json"
    universe = create_universe("civilization_seeds", "old-run", seed=1111)
    data = universe.to_dict()
    data.pop("structures")
    data.pop("populations")
    run_path.write_text(json.dumps(data), encoding="utf-8")

    loaded = load_universe(run_path)

    assert loaded.structures == []
    assert loaded.populations == []
    assert len(loaded.civilizations) == 3


def test_show_stats_export_report_summary_handle_complexity_layers(
    tmp_path: Path,
    capsys,
):
    run_path = tmp_path / "complex.json"
    export_path = tmp_path / "complex-export.json"
    report_path = tmp_path / "complex-report.md"
    universe = create_universe("life_burst", "complex", seed=1212)
    step_universe(universe, steps=5)
    save_universe(universe, run_path)

    assert main(["show", "--run", str(run_path)]) == 0
    show_output = capsys.readouterr().out
    assert "Structures:" in show_output
    assert "Populations:" in show_output

    assert main(["stats", "--run", str(run_path)]) == 0
    stats_output = capsys.readouterr().out
    assert "Structures total:" in stats_output
    assert "Populations total:" in stats_output

    assert main(["export", "--run", str(run_path), "--out", str(export_path)]) == 0
    exported = json.loads(export_path.read_text(encoding="utf-8"))
    assert "structure_summary" in exported
    assert "population_summary" in exported
    assert "structures" in exported
    assert "populations" in exported

    assert main(["report", "--run", str(run_path), "--out", str(report_path)]) == 0
    report = report_path.read_text(encoding="utf-8")
    assert "## Structure Summary" in report
    assert "## Population Summary" in report

    summary = summarize_run_directory(tmp_path, "complex")
    assert summary["runs_count"] >= 1
    assert "average_active_structures" in summary
    assert "average_active_populations" in summary
