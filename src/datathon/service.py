"""Serviço de recomendação que integra política, snapshot e SQLite."""

from __future__ import annotations

import json
import logging
import threading
import uuid
from dataclasses import asdict
from pathlib import Path

from datathon.config import PolicyMode
from datathon.features import context_from_mapping, segment_key
from datathon.policies import ThompsonSamplingPolicy, load_trained_policy
from datathon.storage import DecisionStore

LOGGER = logging.getLogger(__name__)


class UnsupportedContextError(ValueError):
    """Contexto sem evidência disponível na política servida."""


class RecommendationService:
    """Orquestra recomendação e atualização do estado local."""

    def __init__(
        self,
        state_path: Path,
        snapshot_path: Path,
        database_path: Path,
        mode: PolicyMode | str = PolicyMode.MUTABLE,
    ) -> None:
        self.mode = PolicyMode(mode)
        self.state_path = state_path
        self.snapshot_path = snapshot_path
        self.store = DecisionStore(database_path)
        self._lock = threading.RLock()
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        stored_state = self.store.policy_state() if self.mode is PolicyMode.MUTABLE else None
        if self.mode is PolicyMode.READONLY:
            self.policy = ThompsonSamplingPolicy.load(snapshot_path)
        elif stored_state is not None:
            self.policy = ThompsonSamplingPolicy.from_json(stored_state)
        else:
            self.policy = load_trained_policy(state_path, snapshot_path)
            if self.mode is PolicyMode.MUTABLE:
                self.store.initialize_policy_state(self.policy.to_json())
                self.policy.save(self.state_path)

    def recommend(self, payload: dict[str, object]) -> dict[str, object]:
        with self._lock:
            context = context_from_mapping(payload)
            if segment_key(context) not in self.policy.posterior():
                raise UnsupportedContextError(
                    "Não há dados de treino para este perfil. "
                    "A recomendação requer histórico em pelo menos uma categoria."
                )
            decision = self.policy.recommend(context)
            decision_id = str(uuid.uuid4())
            if self.mode is PolicyMode.MUTABLE:
                self.store.save_decision(
                    decision_id,
                    decision.action,
                    decision.segment,
                    decision.policy_version,
                    json.dumps(context, ensure_ascii=False),
                )
        result = asdict(decision)
        result["decision_id"] = decision_id
        result["mode"] = self.mode.value
        result["decision_rule"] = "thompson_sampling"
        return result

    def feedback(self, decision_id: str, reward: int) -> dict[str, object]:
        if self.mode is PolicyMode.READONLY:
            raise PermissionError("O modo público é somente leitura e não atualiza a política.")
        with self._lock:
            row = self.store.get_decision(decision_id)
            if row is None:
                raise KeyError("Decisão não encontrada.")
            if row["feedback"] is not None:
                if int(row["feedback"]) == reward:
                    return {
                        "decision_id": decision_id,
                        "status": "duplicate",
                        "policy_version": self.policy.version,
                    }
                raise ValueError("A decisão já possui feedback diferente.")
            previous_state = self.policy.to_json()
            self.policy.update(json.loads(row["context_json"]), row["action"], reward)
            try:
                status = self.store.add_feedback(decision_id, reward, self.policy.to_json())
            except Exception:
                self.policy = ThompsonSamplingPolicy.from_json(previous_state)
                raise
            try:
                self.policy.save(self.state_path)
            except OSError:
                LOGGER.exception("O espelho JSON não foi atualizado; o SQLite preservou o estado.")
        return {
            "decision_id": decision_id,
            "status": status,
            "policy_version": self.policy.version,
        }

    def metadata(self) -> dict[str, object]:
        return {
            "policy_version": self.policy.version,
            "mode": self.mode.value,
            "decision_rule": "thompson_sampling",
            "learning_enabled": self.mode is PolicyMode.MUTABLE,
            "training_provenance": self.policy.provenance.copy(),
            "state_segments": len(self.policy.posterior()),
            "store": self.store.stats(),
        }
