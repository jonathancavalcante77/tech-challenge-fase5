"""Persistência local de decisões e feedback com idempotência."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path


class DecisionStore:
    """Pequeno repositório SQLite para a demonstração local."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS decisions (
                    decision_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    action TEXT NOT NULL,
                    segment TEXT NOT NULL,
                    policy_version TEXT NOT NULL,
                    context_json TEXT NOT NULL,
                    feedback INTEGER
                );
                """
            )

    def save_decision(self, decision_id: str, action: str, segment: str, policy_version: str, context_json: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO decisions VALUES (?, ?, ?, ?, ?, ?, NULL)",
                (decision_id, datetime.now(UTC).isoformat(), action, segment, policy_version, context_json),
            )

    def add_feedback(self, decision_id: str, reward: int) -> str:
        if reward not in (0, 1):
            raise ValueError("O feedback precisa ser zero ou um.")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT feedback FROM decisions WHERE decision_id = ?", (decision_id,)
            ).fetchone()
            if row is None:
                raise KeyError("Decisão não encontrada.")
            if row["feedback"] is not None:
                if int(row["feedback"]) == reward:
                    return "duplicate"
                raise ValueError("A decisão já possui feedback diferente.")
            connection.execute("UPDATE decisions SET feedback = ? WHERE decision_id = ?", (reward, decision_id))
        return "updated"

    def get_decision(self, decision_id: str) -> sqlite3.Row | None:
        with self._connect() as connection:
            return connection.execute("SELECT * FROM decisions WHERE decision_id = ?", (decision_id,)).fetchone()

    def stats(self) -> dict[str, int]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS decisions, SUM(feedback IS NOT NULL) AS feedbacks FROM decisions"
            ).fetchone()
        return {"decisions": int(row["decisions"] or 0), "feedbacks": int(row["feedbacks"] or 0)}
