from datathon.policies import BaselinePolicy, ThompsonSamplingPolicy


def test_baseline_is_deterministic(context):
    policy = BaselinePolicy("mens_email")
    first = policy.recommend(context)
    second = policy.recommend(context)
    assert first.action == second.action == "mens_email"
    assert first.exploration is False


def test_thompson_updates_only_selected_action(context):
    policy = ThompsonSamplingPolicy(seed=7)
    decision = policy.recommend(context)
    before = policy.posterior()
    policy.update(context, decision.action, 1)
    after = policy.posterior()
    segment = decision.segment
    assert after[segment][decision.action][0] == before[segment][decision.action][0] + 1
    assert after[segment][decision.action][1] == before[segment][decision.action][1]


def test_policy_snapshot_round_trip(tmp_path, context):
    path = tmp_path / "policy.json"
    policy = ThompsonSamplingPolicy(seed=11)
    decision = policy.recommend(context)
    policy.update(context, decision.action, 0)
    policy.save(path)
    restored = ThompsonSamplingPolicy.load(path)
    assert restored.posterior() == policy.posterior()
    assert restored.version == policy.version
