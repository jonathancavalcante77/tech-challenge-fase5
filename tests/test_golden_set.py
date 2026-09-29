from dataclasses import replace
from pathlib import Path

import pytest
from scripts.build_golden_set import build

from datathon.golden import GOLDEN_SET, assess_recommendation, case_context
from datathon.policies import ThompsonSamplingPolicy


def test_golden_set_has_five_explained_recommendations():
    rows = build(Path("config/policy_snapshot.json"))

    assert len(GOLDEN_SET) == len(rows) == 5
    assert len({row["case_id"] for row in rows}) == 5
    assert all(row["recommended_action"] for row in rows)
    assert all(row["segment"] for row in rows)
    assert all(row["decision_makes_sense"] is True for row in rows)
    assert all(len(str(row["rationale"])) > 100 for row in rows)
    assert all(row["posterior_means"] for row in rows)
    assert all(all(row["checks"].values()) for row in rows)


@pytest.mark.parametrize("defect", ["action", "segment", "probability", "exploration", "untrained"])
def test_golden_assessment_rejects_incoherent_recommendations(defect):
    case = GOLDEN_SET[0]
    policy = ThompsonSamplingPolicy.load(Path("config/policy_snapshot.json"))
    decision = policy.recommend(case_context(case))
    assert all(assess_recommendation(case, decision, True).values())

    if defect == "action":
        decision = replace(decision, action="approve_credit")
    elif defect == "segment":
        decision = replace(decision, segment="old:womens")
    elif defect == "probability":
        decision = replace(decision, posterior_means={"mens_email": float("nan")})
    elif defect == "exploration":
        decision = replace(decision, exploration=not decision.exploration)

    assert not all(assess_recommendation(case, decision, defect != "untrained").values())
