from datathon.features import context_from_mapping
from datathon.policies import ThompsonSamplingPolicy

GOLDEN_SET = [
    {"recency": 2, "history": 90, "mens": 0, "womens": 0, "newbie": 1, "zip_code": "Urban", "channel": "Web"},
    {"recency": 3, "history": 900, "mens": 1, "womens": 1, "newbie": 0, "zip_code": "Rural", "channel": "Multichannel"},
    {"recency": 8, "history": 250, "mens": 1, "womens": 0, "newbie": 0, "zip_code": "Surburban", "channel": "Phone"},
    {"recency": 5, "history": 180, "mens": 0, "womens": 1, "newbie": 1, "zip_code": "Urban", "channel": "Web"},
    {"recency": 11, "history": 1200, "mens": 1, "womens": 0, "newbie": 0, "zip_code": "Rural", "channel": "Phone"},
]


def test_golden_set_has_five_valid_recommendations():
    policy = ThompsonSamplingPolicy(seed=2026)
    decisions = [policy.recommend(context_from_mapping(item)) for item in GOLDEN_SET]
    assert len(decisions) == 5
    assert all(decision.action for decision in decisions)
    assert all(decision.segment for decision in decisions)
