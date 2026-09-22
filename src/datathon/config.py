"""Configurações carregadas de variáveis de ambiente."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class PolicyMode(StrEnum):
    """Modos operacionais aceitos pelo serviço."""

    MUTABLE = "mutable"
    READONLY = "readonly"


@dataclass(frozen=True)
class Settings:
    """Configuração operacional do serviço e dos experimentos."""

    data_path: Path = Path(os.getenv("DATA_PATH", "data/raw/hillstrom.csv"))
    state_path: Path = Path(os.getenv("STATE_PATH", "state/policy.json"))
    snapshot_path: Path = Path(os.getenv("SNAPSHOT_PATH", "config/policy_snapshot.json"))
    database_path: Path = Path(os.getenv("DATABASE_PATH", "state/decisions.db"))
    policy_mode: PolicyMode | str = os.getenv("POLICY_MODE", PolicyMode.MUTABLE)
    app_env: str = os.getenv("APP_ENV", "local")
    mlflow_tracking_uri: str = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlruns/mlflow.db")

    def __post_init__(self) -> None:
        try:
            mode = PolicyMode(self.policy_mode)
        except ValueError as error:
            accepted = ", ".join(item.value for item in PolicyMode)
            raise ValueError(f"POLICY_MODE inválido. Valores aceitos: {accepted}.") from error
        object.__setattr__(self, "policy_mode", mode)

    @classmethod
    def from_env(cls) -> "Settings":
        """Lê a configuração no momento de criação da aplicação."""

        return cls(
            data_path=Path(os.getenv("DATA_PATH", "data/raw/hillstrom.csv")),
            state_path=Path(os.getenv("STATE_PATH", "state/policy.json")),
            snapshot_path=Path(os.getenv("SNAPSHOT_PATH", "config/policy_snapshot.json")),
            database_path=Path(os.getenv("DATABASE_PATH", "state/decisions.db")),
            policy_mode=os.getenv("POLICY_MODE", PolicyMode.MUTABLE),
            app_env=os.getenv("APP_ENV", "local"),
            mlflow_tracking_uri=os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlruns/mlflow.db"),
        )

    def ensure_directories(self) -> None:
        """Cria somente os diretórios locais necessários ao funcionamento."""

        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
