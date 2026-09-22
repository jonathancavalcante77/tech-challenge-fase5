"""Ingestão, validação e divisão reproduzível da base Hillstrom."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from urllib.request import urlretrieve

import pandas as pd

from datathon.catalog import DATASET_TO_ACTION

DATASET_URL = (
    "http://www.minethatdata.com/"
    "Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv"
)
SOURCE_MANIFEST = Path(__file__).resolve().parents[2] / "data" / "source.json"
REQUIRED_COLUMNS = {
    "recency",
    "history_segment",
    "history",
    "mens",
    "womens",
    "zip_code",
    "newbie",
    "channel",
    "segment",
    "visit",
    "conversion",
    "spend",
}


def source_manifest(path: Path = SOURCE_MANIFEST) -> dict[str, object]:
    """Carrega a referência versionada da fonte pública."""

    return json.loads(path.read_text(encoding="utf-8"))


def download_dataset(path: Path, expected_sha256: str | None = None) -> Path:
    """Baixa a base por arquivo temporário e valida sua integridade."""

    path.parent.mkdir(parents=True, exist_ok=True)
    expected = expected_sha256 or str(source_manifest()["sha256"])
    if path.exists():
        actual = sha256(path)
        if actual != expected:
            raise ValueError(
                f"Checksum inválido para {path}: esperado {expected}, obtido {actual}."
            )
        return path

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".download", dir=path.parent
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        urlretrieve(DATASET_URL, temporary_path)
        actual = sha256(temporary_path)
        if actual != expected:
            raise ValueError(
                f"Checksum inválido no download: esperado {expected}, obtido {actual}."
            )
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)
    return path


def sha256(path: Path) -> str:
    """Calcula o checksum do arquivo usado na execução."""

    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_raw(path: Path) -> pd.DataFrame:
    """Carrega e verifica o schema da base bruta."""

    frame = pd.read_csv(path)
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {sorted(missing)}")
    if frame["segment"].map(DATASET_TO_ACTION.get).isna().any():
        raise ValueError("A coluna segment contém ações desconhecidas.")
    return frame


def clean_data(frame: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicatas e garante tipos e domínios válidos sem vazamento."""

    # Features anonimizadas podem coincidir em clientes diferentes; a ausência
    # de identificador não autoriza remover observações com o mesmo perfil.
    clean = frame.copy().reset_index(drop=True)
    numeric = ["recency", "history", "mens", "womens", "newbie", "visit", "conversion", "spend"]
    for column in numeric:
        clean[column] = pd.to_numeric(clean[column], errors="raise")
    if not clean["conversion"].isin([0, 1]).all():
        raise ValueError("conversion precisa ser binária.")
    if (clean["conversion"] > clean["visit"]).any():
        raise ValueError("conversion não pode ocorrer sem visit.")
    clean["action"] = clean["segment"].map(DATASET_TO_ACTION)
    clean["action_index"] = clean["action"].map(
        {key: i for i, key in enumerate(DATASET_TO_ACTION.values())}
    )
    return clean


def load_clean(path: Path) -> pd.DataFrame:
    """Baixa, carrega e limpa a base em uma chamada."""

    return clean_data(load_raw(download_dataset(path)))


def stratified_split(
    frame: pd.DataFrame,
    seed: int = 2026,
    train_fraction: float = 0.6,
    validation_fraction: float = 0.2,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Separa dados por ação com as mesmas proporções em cada partição."""

    if not 0 < train_fraction < 1 or not 0 < validation_fraction < 1:
        raise ValueError("As frações precisam estar entre zero e um.")
    if train_fraction + validation_fraction >= 1:
        raise ValueError("Treino e validação devem deixar dados para teste.")
    pieces: list[tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]] = []
    for _, group in frame.groupby("action", sort=True):
        shuffled = group.sample(frac=1, random_state=seed).reset_index(drop=True)
        train_end = int(len(shuffled) * train_fraction)
        validation_end = train_end + int(len(shuffled) * validation_fraction)
        pieces.append(
            (
                shuffled.iloc[:train_end],
                shuffled.iloc[train_end:validation_end],
                shuffled.iloc[validation_end:],
            )
        )
    return tuple(pd.concat(parts, ignore_index=True) for parts in zip(*pieces, strict=True))  # type: ignore[return-value]
