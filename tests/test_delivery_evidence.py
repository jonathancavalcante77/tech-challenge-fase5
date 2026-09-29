import json
from pathlib import Path


def test_versioned_results_match_the_selected_policy():
    summary = json.loads(Path("artifacts/experiment_summary.json").read_text(encoding="utf-8"))
    source = json.loads(Path("data/source.json").read_text(encoding="utf-8"))

    assert summary["dataset_sha256"] == source["sha256"]
    assert summary["selected_policy"] == "thompson_sampling"
    assert summary["selected_policy_value_ips"] == summary["thompson_replay_value_ips"]
    assert summary["selected_lift_vs_baseline"] > 0
    assert summary["evaluation_protocol"] == "stratified-shuffled-replay-v2"
    assert summary["selected_lift_vs_best_fixed"] == (
        summary["selected_policy_value_ips"] - summary["best_fixed_value_ips"]
    )
    assert summary["thompson_replay_ci95"][0] <= summary["thompson_replay_value_ips"]
    assert summary["thompson_replay_value_ips"] <= summary["thompson_replay_ci95"][1]


def test_notebooks_are_executed_without_errors():
    for path in (Path("notebooks/01_eda.ipynb"), Path("notebooks/02_baseline_vs_bandit.ipynb")):
        notebook = json.loads(path.read_text(encoding="utf-8"))
        code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
        outputs = [output for cell in code_cells for output in cell.get("outputs", [])]

        assert code_cells
        assert all(cell.get("execution_count") is not None for cell in code_cells)
        assert all(cell.get("outputs") for cell in code_cells)
        assert not any(output.get("output_type") == "error" for output in outputs)


def test_golden_set_artifact_contains_explanations():
    rows = json.loads(Path("artifacts/golden_set.json").read_text(encoding="utf-8"))

    assert len(rows) == 5
    assert all(row["decision_makes_sense"] is True for row in rows)
    assert all(row["recommended_action"] in row["posterior_means"] for row in rows)
    assert all(len(row["rationale"]) > 100 for row in rows)
