"""Registra os resultados do experimento no MLflow quando disponível."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, default=Path("artifacts/experiment_summary.json"))
    parser.add_argument(
        "--tracking-uri", default=os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlruns/mlflow.db")
    )
    return parser.parse_args()


def execution_key(summary: dict[str, object]) -> str:
    """Identifica o conteúdo integral da evidência, independentemente da formatação."""

    canonical = json.dumps(
        summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def track_experiment(summary_path: Path, tracking_uri: str) -> str:
    """Registra uma evidência completa ou reutiliza seu registro finalizado."""

    from mlflow.tracking import MlflowClient

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    artifact_location = None
    if tracking_uri.startswith("sqlite:///"):
        database_path = Path(tracking_uri.removeprefix("sqlite:///"))
        database_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_location = (database_path.parent / "artifacts").resolve().as_uri()
    client = MlflowClient(tracking_uri=tracking_uri)
    experiment = client.get_experiment_by_name("adaptive-offers")
    experiment_id = (
        experiment.experiment_id
        if experiment is not None
        else client.create_experiment("adaptive-offers", artifact_location=artifact_location)
    )
    key = execution_key(summary)
    existing = client.search_runs(
        experiment_ids=[experiment_id],
        filter_string=f"tags.execution_key = '{key}' AND attributes.status = 'FINISHED'",
        max_results=1,
    )
    if existing:
        run_id = existing[0].info.run_id
        print(f"Execução já registrada no MLflow: {run_id}")
        return run_id
    run = client.create_run(
        experiment_id,
        tags={
            "mlflow.runName": f"ts-seed-{summary['seed']}",
            "execution_key": key,
            "dataset_sha256": summary["dataset_sha256"],
            "decision_rule": summary["selected_policy"],
            "evaluation_protocol": summary["evaluation_protocol"],
            "training_state_sha256": summary["training_state_sha256"],
        },
    )
    run_id = run.info.run_id
    try:
        params = {
            "algorithm": "thompson_sampling_beta_bernoulli",
            "seed": summary["seed"],
            "n_arms": 3,
            "prior_alpha": summary["prior_alpha"],
            "prior_beta": summary["prior_beta"],
            "selected_policy": summary["selected_policy"],
            "logging_propensity": summary["logging_propensity"],
        }
        metrics = {
            "baseline_value_ips": summary["baseline_value_ips"],
            "best_fixed_value_ips": summary["best_fixed_value_ips"],
            "validation_baseline_value_ips": summary["validation_baseline_value_ips"],
            "validation_thompson_value_ips": summary["validation_thompson_value_ips"],
            "thompson_replay_value_ips": summary["thompson_replay_value_ips"],
            "thompson_frozen_value_ips": summary["thompson_frozen_value_ips"],
            "lift_replay": summary["lift_replay"],
            "selected_lift_vs_baseline": summary["selected_lift_vs_baseline"],
            "selected_lift_vs_best_fixed": summary["selected_lift_vs_best_fixed"],
            "exploration_rate": summary["thompson_exploration_rate"],
            "thompson_ci95_lower": summary["thompson_replay_ci95"][0],
            "thompson_ci95_upper": summary["thompson_replay_ci95"][1],
        }
        for name, value in params.items():
            client.log_param(run_id, name, value)
        for name, value in metrics.items():
            client.log_metric(run_id, name, value)
        client.log_artifact(run_id, str(summary_path))
        client.set_terminated(run_id, status="FINISHED")
    except Exception:
        client.set_terminated(run_id, status="FAILED")
        raise
    print(f"Execução registrada no MLflow: {run_id}")
    return run_id


def main() -> None:
    args = parse_args()
    try:
        track_experiment(args.summary, args.tracking_uri)
    except ModuleNotFoundError as error:
        if error.name != "mlflow":
            raise
        print("MLflow não está instalado; o resumo local foi preservado.")


if __name__ == "__main__":
    main()
