"""Registra os resultados do experimento no MLflow quando disponível."""

from __future__ import annotations

import argparse
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


def main() -> None:
    args = parse_args()
    summary_path = args.summary
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    try:
        import mlflow
    except ImportError:
        print("MLflow não está instalado; o resumo local foi preservado.")
        return
    if args.tracking_uri.startswith("sqlite:///"):
        Path(args.tracking_uri.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(args.tracking_uri)
    mlflow.set_experiment("adaptive-offers")
    execution_key = f"{summary['dataset_sha256']}:{summary['seed']}:{summary['selected_policy']}"
    existing = mlflow.search_runs(
        experiment_names=["adaptive-offers"],
        filter_string=f"tags.execution_key = '{execution_key}'",
        max_results=1,
    )
    if not existing.empty:
        print(f"Execução já registrada no MLflow: {existing.iloc[0]['run_id']}")
        return
    with mlflow.start_run(run_name=f"ts-seed-{summary['seed']}") as run:
        mlflow.set_tags(
            {
                "execution_key": execution_key,
                "dataset_sha256": summary["dataset_sha256"],
                "decision_rule": "thompson_sampling",
            }
        )
        mlflow.log_params(
            {
                "algorithm": "thompson_sampling_beta_bernoulli",
                "seed": summary["seed"],
                "n_arms": 3,
                "prior_alpha": 1.0,
                "prior_beta": 1.0,
                "selected_policy": summary["selected_policy"],
            }
        )
        mlflow.log_metrics(
            {
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
        )
        mlflow.log_artifact(str(summary_path))
    print(f"Execução registrada no MLflow: {run.info.run_id}")


if __name__ == "__main__":
    main()
