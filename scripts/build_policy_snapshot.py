"""Gera o snapshot treinado vinculado à configuração e à seleção avaliadas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from datathon.data import load_clean, sha256, stratified_split
from datathon.policies import ThompsonSamplingPolicy, fit_policy


def build(data_path: Path, summary_path: Path, output_path: Path) -> ThompsonSamplingPolicy:
    """Reconstitui somente o treino e rejeita um resumo incompatível com a API."""

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary["selected_policy"] != "thompson_sampling":
        raise ValueError("A avaliação não selecionou Thompson Sampling; snapshot não publicado.")
    if summary["evaluation_protocol"] != "stratified-shuffled-replay-v2":
        raise ValueError("Protocolo de avaliação incompatível; execute novamente o experimento.")
    frame = load_clean(data_path)
    if sha256(data_path) != summary["dataset_sha256"]:
        raise ValueError("Dataset diferente daquele registrado na avaliação.")
    train, _, _ = stratified_split(frame, seed=int(summary["seed"]))
    policy = ThompsonSamplingPolicy(
        seed=int(summary["seed"]),
        prior_alpha=float(summary["prior_alpha"]),
        prior_beta=float(summary["prior_beta"]),
        version="ts-contextual-v2-snapshot",
    )
    fit_policy(policy, train)
    if policy.training_fingerprint() != summary["training_state_sha256"]:
        raise ValueError("Estado de treino diferente daquele registrado na avaliação.")
    policy.provenance = {
        key: summary[key]
        for key in ("dataset_sha256", "evaluation_protocol", "training_state_sha256", "seed")
    }
    policy.save(output_path)
    return policy


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/raw/hillstrom.csv"))
    parser.add_argument("--summary", type=Path, default=Path("artifacts/experiment_summary.json"))
    parser.add_argument("--output", type=Path, default=Path("config/policy_snapshot.json"))
    args = parser.parse_args()
    build(args.data, args.summary, args.output)
    print(f"Snapshot salvo em {args.output}")


if __name__ == "__main__":
    main()
