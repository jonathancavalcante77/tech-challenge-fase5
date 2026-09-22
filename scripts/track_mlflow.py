"""Registra os resultados do experimento no MLflow quando disponível."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    summary_path = Path("artifacts/experiment_summary.json")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    try:
        import mlflow
    except ImportError:
        print("MLflow não está instalado; o resumo local foi preservado.")
        return
    Path("mlruns").mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri("sqlite:///mlruns/mlflow.db")
    mlflow.set_experiment("adaptive-offers")
    with mlflow.start_run(run_name=f"ts-seed-{summary['seed']}"):
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
            }
        )
        mlflow.log_artifact(str(summary_path))
    print("Execução registrada no MLflow local.")


if __name__ == "__main__":
    main()
