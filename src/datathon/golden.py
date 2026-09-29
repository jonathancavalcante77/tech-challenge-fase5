"""Casos de referência usados para explicar decisões da política."""

from __future__ import annotations

import math

from datathon.catalog import ACTION_KEYS
from datathon.policies import PolicyDecision

GOLDEN_SET = (
    {
        "case_id": "recent_mens_web",
        "recency": 2,
        "history": 420.0,
        "mens": 1,
        "womens": 0,
        "newbie": 0,
        "zip_code": "Urban",
        "channel": "Web",
    },
    {
        "case_id": "recent_womens_multichannel",
        "recency": 3,
        "history": 610.0,
        "mens": 0,
        "womens": 1,
        "newbie": 0,
        "zip_code": "Surburban",
        "channel": "Multichannel",
    },
    {
        "case_id": "middle_mixed_web",
        "recency": 5,
        "history": 780.0,
        "mens": 1,
        "womens": 1,
        "newbie": 0,
        "zip_code": "Urban",
        "channel": "Web",
    },
    {
        "case_id": "old_mens_phone",
        "recency": 9,
        "history": 260.0,
        "mens": 1,
        "womens": 0,
        "newbie": 1,
        "zip_code": "Rural",
        "channel": "Phone",
    },
    {
        "case_id": "old_womens_web",
        "recency": 11,
        "history": 330.0,
        "mens": 0,
        "womens": 1,
        "newbie": 1,
        "zip_code": "Urban",
        "channel": "Web",
    },
)

CASE_EXPECTATIONS = {
    "recent_mens_web": {
        "segment": "recent:mens",
        "reason": "Compra recente na categoria masculina; comparar as campanhas nesse segmento, sem inferir gênero.",
    },
    "recent_womens_multichannel": {
        "segment": "recent:womens",
        "reason": "Afinidade feminina recente não obriga campanha feminina; a resposta experimental e sua incerteza orientam a escolha.",
    },
    "middle_mixed_web": {
        "segment": "middle:mixed",
        "reason": "Compras nas duas categorias e recência intermediária exigem o segmento misto, sem escolher por um rótulo demográfico.",
    },
    "old_mens_phone": {
        "segment": "old:mens",
        "reason": "Recência antiga deve usar o segmento antigo; o canal Phone é histórico e não altera a campanha de e-mail avaliada.",
    },
    "old_womens_web": {
        "segment": "old:womens",
        "reason": "Histórico feminino antigo não impõe gênero nem elegibilidade; qualquer ação do catálogo precisa respeitar a amostragem.",
    },
}


def assess_recommendation(
    case: dict[str, object], decision: PolicyDecision, trained_segment: bool
) -> dict[str, bool]:
    """Avalia coerência pelos critérios fixos dos casos, sem impor oferta determinística."""

    expected = CASE_EXPECTATIONS[str(case["case_id"])]
    means_valid = set(decision.posterior_means) == set(ACTION_KEYS) and all(
        math.isfinite(value) and 0 <= value <= 1 for value in decision.posterior_means.values()
    )
    samples_valid = set(decision.sampled_values) == set(ACTION_KEYS) and all(
        math.isfinite(value) and 0 <= value <= 1 for value in decision.sampled_values.values()
    )
    return {
        "catalog_action": decision.action in ACTION_KEYS,
        "expected_segment": decision.segment == expected["segment"],
        "trained_segment": trained_segment,
        "valid_posterior_means": means_valid,
        "valid_samples": samples_valid,
        "sampling_consistency": samples_valid
        and decision.action == max(ACTION_KEYS, key=decision.sampled_values.__getitem__),
        "exploration_consistency": means_valid
        and decision.exploration
        == (decision.action != max(ACTION_KEYS, key=decision.posterior_means.__getitem__)),
    }


def case_context(case: dict[str, object]) -> dict[str, object]:
    """Remove o identificador editorial antes da inferência."""

    return {key: value for key, value in case.items() if key != "case_id"}
