from pathlib import Path

import pandas as pd
import pytest

from datathon.data import clean_data, download_dataset, load_raw, sha256, stratified_split


@pytest.fixture
def raw_frame():
    return pd.DataFrame(
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
                "visit": 1,
                "conversion": 1,
                "spend": 10,
            }
        ]
    )


def test_existing_dataset_checksum_is_enforced(tmp_path):
    path = tmp_path / "dataset.csv"
    path.write_text("invalid", encoding="utf-8")
    with pytest.raises(ValueError, match="Checksum inválido"):
        download_dataset(path, expected_sha256="0" * 64)


def test_clean_data_rejects_conversion_without_visit(raw_frame):
    raw_frame["visit"] = 0
    with pytest.raises(ValueError, match="conversion não pode ocorrer"):
        clean_data(raw_frame)


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("recency", 0),
        ("recency", 13),
        ("recency", 1.5),
        ("history", -1),
        ("history", float("inf")),
        ("history", None),
        ("mens", 2),
        ("womens", -1),
        ("newbie", 0.5),
        ("visit", 2),
        ("conversion", -1),
        ("spend", -1),
        ("zip_code", "Unknown"),
        ("channel", "Unknown"),
        ("segment", "Unknown"),
        ("history_segment", None),
    ],
)
def test_clean_data_rejects_invalid_domains(raw_frame, column, value):
    raw_frame[column] = value
    with pytest.raises(ValueError, match=column):
        clean_data(raw_frame)


def test_clean_data_preserves_distinct_observations_with_identical_values(raw_frame):
    duplicated_profiles = pd.concat([raw_frame, raw_frame], ignore_index=True)

    cleaned = clean_data(duplicated_profiles)

    assert len(cleaned) == 2
    assert cleaned["action"].tolist() == ["mens_email", "mens_email"]
    pd.testing.assert_frame_equal(
        duplicated_profiles, pd.concat([raw_frame, raw_frame], ignore_index=True)
    )


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


def test_split_partitions_are_disjoint_and_keep_stratified_counts(logged_frame):
    expanded = pd.concat([logged_frame] * 30, ignore_index=True)
    expanded["record_id"] = range(len(expanded))

    train, validation, test = stratified_split(expanded)

    partitions = (train, validation, test)
    identifiers = [set(part["record_id"]) for part in partitions]
    assert set.union(*identifiers) == set(expanded["record_id"])
    assert sum(len(part) for part in partitions) == len(expanded)
    assert identifiers[0].isdisjoint(identifiers[1])
    assert identifiers[0].isdisjoint(identifiers[2])
    assert identifiers[1].isdisjoint(identifiers[2])
    for action, total in expanded["action"].value_counts().items():
        expected_train = int(total * 0.6)
        expected_validation = int(total * 0.2)
        assert [int((part["action"] == action).sum()) for part in partitions] == [
            expected_train,
            expected_validation,
            total - expected_train - expected_validation,
        ]


def test_split_mixes_logged_actions_for_sequential_replay(logged_frame):
    expanded = pd.concat([logged_frame] * 30, ignore_index=True)

    for part in stratified_split(expanded):
        action_runs = int(part["action"].ne(part["action"].shift()).sum())
        assert action_runs > part["action"].nunique()
