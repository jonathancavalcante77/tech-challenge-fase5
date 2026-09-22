"""Executa baseline, replay adaptativo e avaliação final."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from datathon.data import load_clean, sha256, stratified_split
from datathon.evaluation import fixed_policy_value, policy_value, sequential_replay
from datathon.features import FEATURE_COLUMNS
from datathon.policies import ThompsonSamplingPolicy


def fit_policy(policy: ThompsonSamplingPolicy, frame) -> None:
    """Inicializa a política com os resultados observados no treino."""

    for row in frame.itertuples(index=False):
        values = row._asdict()
        context = {column: values[column] for column in FEATURE_COLUMNS}
        policy.update(context, values["action"], int(values["conversion"]))


def run(data_path: Path, output_path: Path, seed: int) -> dict[str, object]:
    """Executa a avaliação completa e salva um snapshot pequeno."""

    frame = load_clean(data_path)
    train, validation, test = stratified_split(frame, seed=seed)

    best_fixed_action = (
        train.groupby("action")["conversion"].mean().sort_values(ascending=False).index[0]
    )
    baseline_action = "no_email"
    baseline_value = fixed_policy_value(test, baseline_action)
    best_fixed_value = fixed_policy_value(test, best_fixed_action)
    bandit = ThompsonSamplingPolicy(seed=seed)
    fit_policy(bandit, train)
    replay = sequential_replay(test, bandit, seed=seed)

    frozen = ThompsonSamplingPolicy(seed=seed)
    fit_policy(frozen, train)
    validation_baseline = fixed_policy_value(validation, baseline_action)
    validation_ts, validation_matched = policy_value(
        validation,
        lambda context: frozen.greedy_action(context),
    )
    selected_policy = "thompson_frozen" if validation_ts >= validation_baseline else "baseline_no_email"
    frozen_values, matched = policy_value(
        test,
        lambda context: frozen.greedy_action(context),
    )
    selected_value = frozen_values if selected_policy == "thompson_frozen" else baseline_value
    summary = {
        "dataset_sha256": sha256(data_path),
        "seed": seed,
        "rows": {"total": len(frame), "train": len(train), "test": len(test)},
        "baseline_action": baseline_action,
        "baseline_value_ips": baseline_value,
        "best_fixed_action": best_fixed_action,
        "best_fixed_value_ips": best_fixed_value,
        "validation_baseline_value_ips": validation_baseline,
        "validation_thompson_value_ips": validation_ts,
        "validation_thompson_matched_rows": validation_matched,
        "selected_policy": selected_policy,
        "selected_policy_value_ips": selected_value,
        "selected_lift_vs_baseline": selected_value - baseline_value,
        "selected_lift_vs_best_fixed": selected_value - best_fixed_value,
        "thompson_replay_value_ips": replay.estimated_value,
        "thompson_frozen_value_ips": frozen_values,
        "thompson_replay_matched_rows": replay.matched_rows,
        "thompson_frozen_matched_rows": matched,
        "thompson_exploration_rate": replay.exploration_rate,
        "lift_replay": replay.estimated_value - baseline_value,
        "lift_replay_vs_best_fixed": replay.estimated_value - best_fixed_value,
        "action_counts": replay.action_counts,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/raw/hillstrom.csv"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/experiment_summary.json"))
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    summary = run(args.data, args.output, args.seed)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
