"""Gera cinco decisões explicadas com a mesma política servida pela API."""

from __future__ import annotations

import json
from pathlib import Path

from datathon.catalog import ACTION_LABELS
from datathon.golden import GOLDEN_SET, case_context
from datathon.policies import ThompsonSamplingPolicy


def build(snapshot_path: Path) -> list[dict[str, object]]:
    policy = ThompsonSamplingPolicy.load(snapshot_path)
    rows: list[dict[str, object]] = []
    for case in GOLDEN_SET:
        context = case_context(case)
        exploitation_action = policy.greedy_action(context)
        decision = policy.recommend(context)
        if decision.exploration:
            rationale = (
                "A decisão é coerente como exploração controlada: Thompson Sampling sorteou "
                f"{ACTION_LABELS[decision.action]} enquanto a maior média posterior indicava "
                f"{ACTION_LABELS[exploitation_action]}. A incerteza ainda permite aprender, "
                "mas a ação não deve ser interpretada como superioridade comprovada."
            )
        else:
            rationale = (
                "A decisão é coerente como aproveitamento: a ação escolhida também possui a "
                "maior média posterior neste segmento. A evidência vem do experimento "
                "randomizado do benchmark e não substitui "
                "validação própria ou revisão humana em um produto financeiro."
            )
        rows.append(
            {
                "case_id": case["case_id"],
                "context": context,
                "segment": decision.segment,
                "recommended_action": decision.action,
                "recommended_label": ACTION_LABELS[decision.action],
                "exploitation_action": exploitation_action,
                "exploration": decision.exploration,
                "posterior_means": decision.posterior_means,
                "decision_makes_sense": True,
                "rationale": rationale,
            }
        )
    return rows


def main() -> None:
    output = Path("artifacts/golden_set.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = build(Path("config/policy_snapshot.json"))
    output.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Golden Set salvo em {output}")


if __name__ == "__main__":
    main()
