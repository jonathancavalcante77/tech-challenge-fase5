from pathlib import Path

import pandas as pd
import pytest

from datathon.data import clean_data, download_dataset, load_raw, sha256, stratified_split


def test_existing_dataset_checksum_is_enforced(tmp_path):
    path = tmp_path / "dataset.csv"
    path.write_text("invalid", encoding="utf-8")
    with pytest.raises(ValueError, match="Checksum inválido"):
        download_dataset(path, expected_sha256="0" * 64)


def test_clean_data_rejects_conversion_without_visit():
    frame = pd.DataFrame(
        [
            {
                "recency": 1,
                "history_segment": "1) $0 - $100",
                "history": 20,
                "mens": 1,
                "womens": 0,
                "zip_code": "Urban",
                "newbie": 1,
                "channel": "Web",
                "segment": "Mens E-Mail",
                "visit": 0,
                "conversion": 1,
                "spend": 10,
            }
        ]
    )
    with pytest.raises(ValueError, match="conversion não pode ocorrer"):
        clean_data(frame)


def test_checksum_is_stable(tmp_path):
    path = tmp_path / "content.txt"
    path.write_text("adaptive-offers", encoding="utf-8")
    assert sha256(path) == "cad5be16ad526d0eca8878505166958efec737a29c2313a825d4a212c93e33f6"


def test_download_is_validated_before_becoming_visible(tmp_path, monkeypatch):
    content = b"verified-content"
    expected_path = tmp_path / "expected.bin"
    expected_path.write_bytes(content)

    def fake_retrieve(_url, destination):
        Path(destination).write_bytes(content)

    monkeypatch.setattr("datathon.data.urlretrieve", fake_retrieve)
    destination = tmp_path / "dataset.csv"
    download_dataset(destination, expected_sha256=sha256(expected_path))

    assert destination.read_bytes() == content
    assert not list(tmp_path.glob("*.download"))


def test_unknown_historical_action_is_rejected(tmp_path):
    path = tmp_path / "dataset.csv"
    pd.DataFrame(
        [
            {
                "recency": 1,
                "history_segment": "1) $0 - $100",
                "history": 20,
                "mens": 1,
                "womens": 0,
                "zip_code": "Urban",
                "newbie": 1,
                "channel": "Web",
                "segment": "Unknown",
                "visit": 0,
                "conversion": 0,
                "spend": 0,
            }
        ]
    ).to_csv(path, index=False)

    with pytest.raises(ValueError, match="ações desconhecidas"):
        load_raw(path)


def test_stratified_split_is_reproducible(logged_frame):
    expanded = pd.concat([logged_frame] * 15, ignore_index=True)
    first = stratified_split(expanded, seed=2026)
    second = stratified_split(expanded, seed=2026)

    assert [len(part) for part in first] == [len(part) for part in second]
    for left, right in zip(first, second, strict=True):
        pd.testing.assert_frame_equal(left, right)
        assert set(left["action"]) == set(expanded["action"])
