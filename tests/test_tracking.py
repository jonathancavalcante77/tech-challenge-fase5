import json
from pathlib import Path

import pytest
from mlflow.tracking import MlflowClient
from scripts.track_mlflow import execution_key, track_experiment


@pytest.fixture
def tracking_evidence(tmp_path):
    summary = {
        "evaluation_protocol": "stratified-shuffled-replay-v2",
        "training_state_sha256": "b" * 64,
        "prior_alpha": 1.0,
        "prior_beta": 1.0,
        "logging_propensity": 1 / 3,
        "dataset_sha256": "a" * 64,
        "seed": 2026,
        "selected_policy": "thompson_sampling",
        "baseline_value_ips": 0.007,
        "best_fixed_value_ips": 0.015,
        "validation_baseline_value_ips": 0.006,
        "validation_thompson_value_ips": 0.009,
        "thompson_replay_value_ips": 0.014,
        "thompson_frozen_value_ips": 0.015,
        "lift_replay": 0.007,
        "selected_lift_vs_baseline": 0.007,
        "selected_lift_vs_best_fixed": -0.001,
        "thompson_exploration_rate": 0.18,
        "thompson_replay_ci95": [0.010, 0.018],
    }
    path = tmp_path / "experiment_summary.json"
    path.write_text(json.dumps(summary), encoding="utf-8")
    uri = f"sqlite:///{(tmp_path / 'mlflow.db').as_posix()}"
    return path, summary, uri


def test_identical_evidence_reuses_finished_run(tracking_evidence):
    path, summary, uri = tracking_evidence
    first = track_experiment(path, uri)
    reordered = dict(reversed(list(summary.items())))
    path.write_text(json.dumps(reordered, indent=4), encoding="utf-8")
    second = track_experiment(path, uri)

    client = MlflowClient(tracking_uri=uri)
    run = client.get_run(first)
    runs = client.search_runs([run.info.experiment_id])
    assert first == second
    assert len(runs) == 1
    assert run.info.status == "FINISHED"
    assert run.data.tags["execution_key"] == execution_key(summary)


def test_changed_evidence_creates_new_run(tracking_evidence):
    path, summary, uri = tracking_evidence
    first = track_experiment(path, uri)
    summary["thompson_replay_value_ips"] = 0.017
    path.write_text(json.dumps(summary), encoding="utf-8")
    second = track_experiment(path, uri)

    client = MlflowClient(tracking_uri=uri)
    assert first != second
    assert client.get_run(first).data.metrics["thompson_replay_value_ips"] == 0.014
    assert client.get_run(second).data.metrics["thompson_replay_value_ips"] == 0.017
    assert (
        client.get_run(first).data.tags["execution_key"]
        != client.get_run(second).data.tags["execution_key"]
    )


def test_failed_run_does_not_prevent_retry(tracking_evidence, tmp_path):
    path, summary, uri = tracking_evidence
    client = MlflowClient(tracking_uri=uri)
    experiment_id = client.create_experiment(
        "adaptive-offers", artifact_location=(tmp_path / "artifacts").as_uri()
    )
    failed = client.create_run(experiment_id, tags={"execution_key": execution_key(summary)})
    client.set_terminated(failed.info.run_id, status="FAILED")

    retried = track_experiment(path, uri)

    assert retried != failed.info.run_id
    assert client.get_run(retried).info.status == "FINISHED"
    assert client.get_run(failed.info.run_id).info.status == "FAILED"
    assert len(client.search_runs([experiment_id])) == 2


def test_finished_run_has_exact_metrics_and_artifact(tracking_evidence, tmp_path):
    path, summary, uri = tracking_evidence
    run_id = track_experiment(path, uri)
    client = MlflowClient(tracking_uri=uri)
    run = client.get_run(run_id)

    assert run.data.metrics["baseline_value_ips"] == summary["baseline_value_ips"]
    assert run.data.metrics["thompson_replay_value_ips"] == summary["thompson_replay_value_ips"]
    assert run.data.params["seed"] == str(summary["seed"])
    assert {item.path for item in client.list_artifacts(run_id)} == {path.name}
    destination = tmp_path / "download"
    destination.mkdir()
    artifact = client.download_artifacts(run_id, path.name, str(destination))
    assert json.loads(Path(artifact).read_text(encoding="utf-8")) == summary
