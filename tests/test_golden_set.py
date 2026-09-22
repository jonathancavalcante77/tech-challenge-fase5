from pathlib import Path

from scripts.build_golden_set import build

from datathon.golden import GOLDEN_SET


def test_golden_set_has_five_explained_recommendations():
    rows = build(Path("config/policy_snapshot.json"))

    assert len(GOLDEN_SET) == len(rows) == 5
    assert len({row["case_id"] for row in rows}) == 5
    assert all(row["recommended_action"] for row in rows)
    assert all(row["segment"] for row in rows)
    assert all(row["decision_makes_sense"] is True for row in rows)
    assert all(len(str(row["rationale"])) > 100 for row in rows)
    assert all(row["posterior_means"] for row in rows)
