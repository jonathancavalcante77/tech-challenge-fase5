"""Serviço de recomendação que integra política, snapshot e SQLite."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from pathlib import Path

from datathon.features import context_from_mapping
from datathon.policies import ThompsonSamplingPolicy
from datathon.storage import DecisionStore


class RecommendationService:
    """Orquestra recomendação e atualização do estado local."""

    def __init__(self, state_path: Path, database_path: Path, mode: str = "mutable") -> None:
        self.mode = mode
        self.state_path = state_path
        self.policy = ThompsonSamplingPolicy.load(state_path) if state_path.exists() else ThompsonSamplingPolicy()
        self.store = DecisionStore(database_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    def recommend(self, payload: dict[str, object]) -> dict[str, object]:
        context = context_from_mapping(payload)
        decision = self.policy.recommend(context)
        decision_id = str(uuid.uuid4())
        if self.mode != "readonly":
            self.store.save_decision(
                decision_id,
                decision.action,
                decision.segment,
                decision.policy_version,
                json.dumps(context, ensure_ascii=False),
            )
        result = asdict(decision)
        result["decision_id"] = decision_id
        result["mode"] = self.mode
        return result

    def feedback(self, decision_id: str, reward: int) -> dict[str, object]:
        if self.mode == "readonly":
            raise PermissionError("O modo público é somente leitura e não atualiza a política.")
        row = self.store.get_decision(decision_id)
        if row is None:
            raise KeyError("Decisão não encontrada.")
        status = self.store.add_feedback(decision_id, reward)
        if status == "updated":
            self.policy.update(json.loads(row["context_json"]), row["action"], reward)
            self.policy.save(self.state_path)
        return {"decision_id": decision_id, "status": status, "policy_version": self.policy.version}

    def metadata(self) -> dict[str, object]:
        return {
            "policy_version": self.policy.version,
            "mode": self.mode,
            "learning_enabled": self.mode != "readonly",
            "state_segments": len(self.policy.summary()),
            "store": self.store.stats(),
        }
