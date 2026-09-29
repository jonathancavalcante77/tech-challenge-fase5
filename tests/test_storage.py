import sqlite3

import pytest

from datathon.storage import DecisionStore


def test_feedback_is_idempotent(tmp_path):
    store = DecisionStore(tmp_path / "decisions.db")
    store.save_decision("d1", "mens_email", "recent:mens", "v1", "{}")
    assert store.add_feedback("d1", 1, '{"version":"v2"}') == "updated"
    assert store.add_feedback("d1", 1, '{"version":"v3"}') == "duplicate"
    assert store.policy_state() == '{"version":"v2"}'
    with pytest.raises(ValueError):
        store.add_feedback("d1", 0, '{"version":"v3"}')


def test_unknown_decision_is_rejected(tmp_path):
    store = DecisionStore(tmp_path / "decisions.db")
    with pytest.raises(KeyError):
        store.add_feedback("missing", 1, "{}")


def test_connections_close_after_success_and_failure(tmp_path, monkeypatch):
    connections = []
    connect = sqlite3.connect

    def capture_connection(*args, **kwargs):
        connection = connect(*args, **kwargs)
        connections.append(connection)
        return connection

    monkeypatch.setattr(sqlite3, "connect", capture_connection)
    path = tmp_path / "decisions.db"
    store = DecisionStore(path)
    store.initialize_policy_state("{}")
    store.save_decision("d1", "mens_email", "recent:mens", "v1", "{}")
    assert store.get_decision("d1")["feedback"] is None
    assert store.add_feedback("d1", 1, '{"version":"v2"}') == "updated"
    assert store.add_feedback("d1", 1, "{}") == "duplicate"
    with pytest.raises(ValueError):
        store.add_feedback("d1", 0, "{}")
    with pytest.raises(KeyError):
        store.add_feedback("missing", 1, "{}")
    assert store.policy_state() == '{"version":"v2"}'
    assert store.stats() == {"decisions": 1, "feedbacks": 1}
    for connection in connections:
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            connection.execute("SELECT 1")
    path.rename(tmp_path / "released.db")


def test_failed_policy_write_rolls_back_feedback(tmp_path):
    store = DecisionStore(tmp_path / "decisions.db")
    store.initialize_policy_state('{"version":"v1"}')
    store.save_decision("d1", "mens_email", "recent:mens", "v1", "{}")
    connection = sqlite3.connect(store.path)
    try:
        connection.execute(
            "CREATE TRIGGER reject_policy_update BEFORE UPDATE ON policy_state "
            "BEGIN SELECT RAISE(ABORT, 'policy write failed'); END"
        )
        connection.commit()
    finally:
        connection.close()
    with pytest.raises(sqlite3.IntegrityError, match="policy write failed"):
        store.add_feedback("d1", 1, '{"version":"v2"}')
    assert store.get_decision("d1")["feedback"] is None
    assert store.policy_state() == '{"version":"v1"}'
