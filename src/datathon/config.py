"""Configurações carregadas de variáveis de ambiente."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Configuração operacional do serviço e dos experimentos."""

    data_path: Path = Path(os.getenv("DATA_PATH", "data/raw/hillstrom.csv"))
    state_path: Path = Path(os.getenv("STATE_PATH", "state/policy.json"))
    database_path: Path = Path(os.getenv("DATABASE_PATH", "state/decisions.db"))
    policy_mode: str = os.getenv("POLICY_MODE", "mutable")
    app_env: str = os.getenv("APP_ENV", "local")
    mlflow_tracking_uri: str = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlruns/mlflow.db")

    def ensure_directories(self) -> None:
        """Cria somente os diretórios locais necessários ao funcionamento."""

        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
