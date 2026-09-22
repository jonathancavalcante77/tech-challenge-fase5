import pytest

from datathon.storage import DecisionStore


def test_feedback_is_idempotent(tmp_path):
    store = DecisionStore(tmp_path / "decisions.db")
    store.save_decision("d1", "mens_email", "recent:mens", "v1", "{}")
    assert store.add_feedback("d1", 1) == "updated"
    assert store.add_feedback("d1", 1) == "duplicate"
    with pytest.raises(ValueError):
        store.add_feedback("d1", 0)


def test_unknown_decision_is_rejected(tmp_path):
    store = DecisionStore(tmp_path / "decisions.db")
    with pytest.raises(KeyError):
        store.add_feedback("missing", 1)
