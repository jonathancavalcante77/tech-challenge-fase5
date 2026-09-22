"""Gera o snapshot congelado usado na publicação somente leitura."""

from __future__ import annotations

from pathlib import Path

from datathon.data import load_clean, stratified_split
from datathon.features import FEATURE_COLUMNS
from datathon.policies import ThompsonSamplingPolicy


def main() -> None:
    frame = load_clean(Path("data/raw/hillstrom.csv"))
    train, _, _ = stratified_split(frame, seed=2026)
    policy = ThompsonSamplingPolicy(seed=2026, version="ts-contextual-v1-snapshot")
    for row in train.itertuples(index=False):
        values = row._asdict()
        policy.update(
            {column: values[column] for column in FEATURE_COLUMNS},
            values["action"],
            int(values["conversion"]),
        )
    policy.save(Path("config/policy_snapshot.json"))
    print("Snapshot salvo em config/policy_snapshot.json")


if __name__ == "__main__":
    main()
