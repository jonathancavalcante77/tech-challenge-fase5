"""Avaliação offline com replay e estimadores de política."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

from datathon.catalog import ACTION_KEYS
from datathon.features import FEATURE_COLUMNS
from datathon.policies import Policy


@dataclass(frozen=True)
class ReplayResult:
    """Métricas de uma execução de replay randomizado."""

    estimated_value: float
    matched_rows: int
    total_rows: int
    exploration_rate: float
    cumulative_values: list[float]
    action_counts: dict[str, int]


def sequential_replay(frame: pd.DataFrame, policy: Policy, seed: int = 2026) -> ReplayResult:
    """Executa replay: só atualiza a política quando a ação foi observada."""

    required = {"action", "conversion"}
    if not required.issubset(frame.columns):
        raise ValueError(f"Colunas de replay ausentes: {sorted(required - set(frame.columns))}")
    rng = np.random.default_rng(seed)
    del rng  # A aleatoriedade da política é encapsulada nela e tem seed próprio.
    matched = 0
    weighted_reward = 0.0
    explorations = 0
    cumulative: list[float] = []
    counts = {key: 0 for key in ACTION_KEYS}
    for row in frame.itertuples(index=False):
        values = row._asdict()
        context = {column: values[column] for column in FEATURE_COLUMNS}
        decision = policy.recommend(context)
        counts[decision.action] += 1
        explorations += int(decision.exploration)
        if decision.action == values["action"]:
            matched += 1
            weighted_reward += len(ACTION_KEYS) * float(values["conversion"])
            policy.update(context, decision.action, int(values["conversion"]))
        cumulative.append(weighted_reward / max(len(cumulative) + 1, 1))
    total = len(frame)
    return ReplayResult(
        estimated_value=weighted_reward / max(total, 1),
        matched_rows=matched,
        total_rows=total,
        exploration_rate=explorations / max(total, 1),
        cumulative_values=cumulative,
        action_counts=counts,
    )


def fixed_policy_value(frame: pd.DataFrame, action: str) -> float:
    """Estima o valor de uma regra fixa por replay IPS uniforme."""

    if action not in ACTION_KEYS:
        raise ValueError(f"Ação desconhecida: {action}")
    matched = frame.loc[frame["action"] == action, "conversion"]
    return float(len(ACTION_KEYS) * matched.sum() / max(len(frame), 1))


def policy_value(
    frame: pd.DataFrame,
    policy_action: Callable[[dict[str, object]], str],
    propensity: float = 1 / 3,
) -> tuple[float, int]:
    """Calcula IPS para uma política congelada no conjunto de teste."""

    if not 0 < propensity <= 1:
        raise ValueError("A propensão precisa estar entre zero e um.")
    total = 0.0
    matched = 0
    for row in frame.itertuples(index=False):
        values = row._asdict()
        context = {column: values[column] for column in FEATURE_COLUMNS}
        if policy_action(context) == values["action"]:
            total += float(values["conversion"]) / propensity
            matched += 1
    return total / max(len(frame), 1), matched
