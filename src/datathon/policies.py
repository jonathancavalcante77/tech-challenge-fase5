"""Políticas de decisão e estado Bayesiano do bandit contextual."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np

from datathon.catalog import ACTION_KEYS
from datathon.features import segment_key


@dataclass(frozen=True)
class PolicyDecision:
    """Resultado explicável de uma decisão da política."""

    action: str
    segment: str
    posterior_means: dict[str, float]
    sampled_values: dict[str, float]
    exploration: bool
    policy_version: str


class Policy(Protocol):
    """Contrato mínimo usado pelo replay e pelo serviço."""

    version: str

    def recommend(self, context: dict[str, object]) -> PolicyDecision:
        """Escolhe uma ação para o contexto."""

    def update(self, context: dict[str, object], action: str, reward: int) -> None:
        """Atualiza o estado com um feedback validado."""


class BaselinePolicy:
    """Regra fixa baseada na melhor ação global observada no treino."""

    def __init__(self, action: str = "mens_email", version: str = "baseline-v1") -> None:
        if action not in ACTION_KEYS:
            raise ValueError(f"Ação desconhecida: {action}")
        self.action = action
        self.version = version

    def recommend(self, context: dict[str, object]) -> PolicyDecision:
        segment = segment_key(context)
        means = {key: 1.0 if key == self.action else 0.0 for key in ACTION_KEYS}
        return PolicyDecision(
            action=self.action,
            segment=segment,
            posterior_means=means,
            sampled_values=means.copy(),
            exploration=False,
            policy_version=self.version,
        )

    def update(self, context: dict[str, object], action: str, reward: int) -> None:
        """Baseline determinístico não aprende com o feedback."""

        if action not in ACTION_KEYS or reward not in (0, 1):
            raise ValueError("Feedback inválido para baseline.")


class ThompsonSamplingPolicy:
    """Thompson Sampling Beta-Bernoulli segmentado por contexto."""

    def __init__(
        self,
        seed: int = 2026,
        prior_alpha: float = 1.0,
        prior_beta: float = 1.0,
        version: str = "ts-contextual-v1",
    ) -> None:
        if prior_alpha <= 0 or prior_beta <= 0:
            raise ValueError("Os parâmetros do prior precisam ser positivos.")
        self.seed = seed
        self.prior_alpha = prior_alpha
        self.prior_beta = prior_beta
        self.version = version
        self._rng = np.random.default_rng(seed)
        self._state: dict[str, dict[str, list[float]]] = {}

    def _segment_state(self, segment: str) -> dict[str, list[float]]:
        return self._state.setdefault(
            segment,
            {key: [self.prior_alpha, self.prior_beta] for key in ACTION_KEYS},
        )

    def recommend(self, context: dict[str, object]) -> PolicyDecision:
        segment = segment_key(context)
        state = self._segment_state(segment)
        means = {key: values[0] / sum(values) for key, values in state.items()}
        samples = {
            key: float(self._rng.beta(values[0], values[1])) for key, values in state.items()
        }
        action = max(ACTION_KEYS, key=lambda key: samples[key])
        exploit_action = max(ACTION_KEYS, key=lambda key: means[key])
        return PolicyDecision(
            action=action,
            segment=segment,
            posterior_means=means,
            sampled_values=samples,
            exploration=action != exploit_action,
            policy_version=self.version,
        )

    def greedy_action(self, context: dict[str, object]) -> str:
        """Escolhe a maior média posterior sem amostragem."""

        state = self._segment_state(segment_key(context))
        return max(ACTION_KEYS, key=lambda key: state[key][0] / sum(state[key]))

    def update(self, context: dict[str, object], action: str, reward: int) -> None:
        if action not in ACTION_KEYS:
            raise ValueError(f"Ação desconhecida: {action}")
        if reward not in (0, 1):
            raise ValueError("A recompensa precisa ser zero ou um.")
        state = self._segment_state(segment_key(context))
        state[action][0] += reward
        state[action][1] += 1 - reward

    def posterior(self) -> dict[str, dict[str, list[float]]]:
        """Copia serializável do estado posterior."""

        return json.loads(json.dumps(self._state))

    def save(self, path: Path) -> None:
        """Salva estado e metadados para a API local."""

        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": self.version,
            "seed": self.seed,
            "prior_alpha": self.prior_alpha,
            "prior_beta": self.prior_beta,
            "posterior": self.posterior(),
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "ThompsonSamplingPolicy":
        """Reidrata uma política salva em disco."""

        payload = json.loads(path.read_text(encoding="utf-8"))
        policy = cls(
            seed=int(payload["seed"]),
            prior_alpha=float(payload["prior_alpha"]),
            prior_beta=float(payload["prior_beta"]),
            version=str(payload["version"]),
        )
        policy._state = {
            str(segment): {
                str(action): [float(values[0]), float(values[1])]
                for action, values in actions.items()
            }
            for segment, actions in payload.get("posterior", {}).items()
        }
        return policy

    def summary(self) -> list[dict[str, object]]:
        """Retorna médias posteriores para a tela operacional."""

        rows: list[dict[str, object]] = []
        for segment, actions in sorted(self._state.items()):
            for action, values in actions.items():
                rows.append(
                    {
                        "segment": segment,
                        "action": action,
                        "alpha": values[0],
                        "beta": values[1],
                        "posterior_mean": values[0] / sum(values),
                    }
                )
        return rows


def build_policy_from_snapshot(path: Path, mode: str = "mutable") -> ThompsonSamplingPolicy:
    """Carrega snapshot ou inicia um prior limpo, respeitando o modo."""

    if path.exists():
        return ThompsonSamplingPolicy.load(path)
    policy = ThompsonSamplingPolicy()
    if mode == "readonly":
        return policy
    policy.save(path)
    return policy
