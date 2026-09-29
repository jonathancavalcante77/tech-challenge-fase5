"""Executa baseline, replay adaptativo e avaliação final."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from datathon.data import load_clean, sha256, stratified_split
from datathon.evaluation import (
    fixed_policy_interval,
    fixed_policy_value,
    policy_value,
    sequential_replay,
)
from datathon.policies import ThompsonSamplingPolicy, fit_policy


def run(data_path: Path, output_path: Path, seed: int) -> dict[str, object]:
    """Executa a avaliação completa e salva um snapshot pequeno."""

    frame = load_clean(data_path)
    train, validation, test = stratified_split(frame, seed=seed)

    best_fixed_action = (
        train.groupby("action")["conversion"].mean().sort_values(ascending=False).index[0]
    )
    baseline_action = "no_email"
    validation_bandit = ThompsonSamplingPolicy(seed=seed)
    fit_policy(validation_bandit, train)
    validation_baseline = fixed_policy_value(validation, baseline_action)
    validation_replay = sequential_replay(validation, validation_bandit)
    selected_policy = (
        "thompson_sampling"
        if validation_replay.estimated_value >= validation_baseline
        else "baseline_no_email"
    )

    baseline_value = fixed_policy_value(test, baseline_action)
    best_fixed_value = fixed_policy_value(test, best_fixed_action)
    bandit = ThompsonSamplingPolicy(seed=seed)
    fit_policy(bandit, train)
    training_fingerprint = bandit.training_fingerprint()
    replay = sequential_replay(test, bandit)

    frozen = ThompsonSamplingPolicy(seed=seed)
    fit_policy(frozen, train)
    frozen_values, matched = policy_value(
        test,
        lambda context: frozen.greedy_action(context),
    )
    selected_value = (
        replay.estimated_value if selected_policy == "thompson_sampling" else baseline_value
    )
    baseline_se, baseline_ci_lower, baseline_ci_upper = fixed_policy_interval(test, baseline_action)
    best_fixed_se, best_fixed_ci_lower, best_fixed_ci_upper = fixed_policy_interval(
        test, best_fixed_action
    )
    summary = {
        "evaluation_protocol": "stratified-shuffled-replay-v2",
        "training_state_sha256": training_fingerprint,
        "logging_propensity": 1 / 3,
        "prior_alpha": bandit.prior_alpha,
        "prior_beta": bandit.prior_beta,
        "dataset_sha256": sha256(data_path),
        "seed": seed,
        "rows": {
            "total": len(frame),
            "train": len(train),
            "validation": len(validation),
            "test": len(test),
        },
        "baseline_action": baseline_action,
        "baseline_value_ips": baseline_value,
        "baseline_standard_error": baseline_se,
        "baseline_ci95": [baseline_ci_lower, baseline_ci_upper],
        "best_fixed_action": best_fixed_action,
        "best_fixed_value_ips": best_fixed_value,
        "best_fixed_standard_error": best_fixed_se,
        "best_fixed_ci95": [best_fixed_ci_lower, best_fixed_ci_upper],
        "validation_baseline_value_ips": validation_baseline,
        "validation_thompson_value_ips": validation_replay.estimated_value,
        "validation_thompson_matched_rows": validation_replay.matched_rows,
        "selected_policy": selected_policy,
        "selected_policy_value_ips": selected_value,
        "selected_lift_vs_baseline": selected_value - baseline_value,
        "selected_lift_vs_best_fixed": selected_value - best_fixed_value,
        "thompson_replay_value_ips": replay.estimated_value,
        "thompson_replay_standard_error": replay.standard_error,
        "thompson_replay_ci95": [replay.ci_lower, replay.ci_upper],
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
