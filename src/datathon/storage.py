"""Persistência local de decisões e feedback com idempotência."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path


class DecisionStore:
    """Pequeno repositório SQLite para a demonstração local."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=30)
        try:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA busy_timeout = 30000")
            connection.execute("PRAGMA journal_mode = WAL")
            with connection:
                yield connection
        finally:
            # O contexto nativo controla a transação, mas não fecha a conexão.
            connection.close()

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
                CREATE TABLE IF NOT EXISTS policy_state (
                    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                    payload_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )

    def save_decision(
        self, decision_id: str, action: str, segment: str, policy_version: str, context_json: str
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO decisions VALUES (?, ?, ?, ?, ?, ?, NULL)",
                (
                    decision_id,
                    datetime.now(UTC).isoformat(),
                    action,
                    segment,
                    policy_version,
                    context_json,
                ),
            )

    def policy_state(self) -> str | None:
        """Retorna o estado transacional da política, quando disponível."""

        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM policy_state WHERE singleton = 1"
            ).fetchone()
        return None if row is None else str(row["payload_json"])

    def initialize_policy_state(self, payload_json: str) -> None:
        """Registra o snapshot inicial sem substituir aprendizado existente."""

        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO policy_state (singleton, payload_json, updated_at)
                VALUES (1, ?, ?)
                """,
                (payload_json, datetime.now(UTC).isoformat()),
            )

    def add_feedback(self, decision_id: str, reward: int, policy_state: str) -> str:
        """Confirma feedback e novo estado da política na mesma transação."""

        if reward not in (0, 1):
            raise ValueError("O feedback precisa ser zero ou um.")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT feedback FROM decisions WHERE decision_id = ?", (decision_id,)
            ).fetchone()
            if row is None:
                raise KeyError("Decisão não encontrada.")
            if row["feedback"] is not None:
                if int(row["feedback"]) == reward:
                    return "duplicate"
                raise ValueError("A decisão já possui feedback diferente.")
            updated = connection.execute(
                "UPDATE decisions SET feedback = ? WHERE decision_id = ? AND feedback IS NULL",
                (reward, decision_id),
            )
            if updated.rowcount != 1:
                raise RuntimeError("O feedback foi alterado por outra execução.")
            connection.execute(
                """
                INSERT INTO policy_state (singleton, payload_json, updated_at)
                VALUES (1, ?, ?)
                ON CONFLICT(singleton) DO UPDATE SET
                    payload_json = excluded.payload_json,
                    updated_at = excluded.updated_at
                """,
                (policy_state, datetime.now(UTC).isoformat()),
            )
        return "updated"

    def get_decision(self, decision_id: str) -> sqlite3.Row | None:
        with self._connect() as connection:
            return connection.execute(
                "SELECT * FROM decisions WHERE decision_id = ?", (decision_id,)
            ).fetchone()

    def stats(self) -> dict[str, int]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS decisions, SUM(feedback IS NOT NULL) AS feedbacks FROM decisions"
            ).fetchone()
        return {"decisions": int(row["decisions"] or 0), "feedbacks": int(row["feedbacks"] or 0)}
