"""Transformações determinísticas usadas no treino e na inferência."""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

FEATURE_COLUMNS = (
    "recency",
    "history",
    "mens",
    "womens",
    "newbie",
    "zip_code",
    "channel",
)


def recency_bucket(value: int | float) -> str:
    """Agrupa meses desde a última compra em faixas interpretáveis."""

    numeric = int(value)
    if numeric <= 3:
        return "recent"
    if numeric <= 6:
        return "middle"
    return "old"


def affinity(mens: int | float, womens: int | float) -> str:
    """Identifica afinidade de categoria sem inferir gênero da pessoa."""

    if bool(mens) and bool(womens):
        return "mixed"
    if bool(mens):
        return "mens"
    if bool(womens):
        return "womens"
    return "none"


def segment_key(context: Mapping[str, object]) -> str:
    """Produz uma chave estável para a política contextual."""

    return f"{recency_bucket(float(context['recency']))}:{affinity(context['mens'], context['womens'])}"


def prepare_context(frame: pd.DataFrame) -> pd.DataFrame:
    """Aplica a mesma limpeza de contexto para dados históricos."""

    missing = set(FEATURE_COLUMNS).difference(frame.columns)
    if missing:
        raise ValueError(f"Features ausentes: {sorted(missing)}")
    prepared = frame.loc[:, list(FEATURE_COLUMNS)].copy()
    prepared["recency"] = pd.to_numeric(prepared["recency"], errors="raise")
    prepared["history"] = pd.to_numeric(prepared["history"], errors="raise")
    prepared["mens"] = pd.to_numeric(prepared["mens"], errors="raise").astype(int)
    prepared["womens"] = pd.to_numeric(prepared["womens"], errors="raise").astype(int)
    prepared["newbie"] = pd.to_numeric(prepared["newbie"], errors="raise").astype(int)
    for column in ["zip_code", "channel"]:
        prepared[column] = prepared[column].astype(str)
    return prepared


def context_from_mapping(payload: Mapping[str, object]) -> dict[str, object]:
    """Valida e normaliza o payload recebido pela API."""

    frame = prepare_context(pd.DataFrame([dict(payload)]))
    return frame.iloc[0].to_dict()
