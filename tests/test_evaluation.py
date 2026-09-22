from datathon.evaluation import fixed_policy_value, sequential_replay
from datathon.policies import ThompsonSamplingPolicy


def test_fixed_policy_ips_uses_random_assignment(logged_frame):
    value = fixed_policy_value(logged_frame, "mens_email")
    assert value == 0.75


def test_replay_returns_consistent_shape(logged_frame):
    result = sequential_replay(logged_frame, ThompsonSamplingPolicy(seed=3))
    assert result.total_rows == len(logged_frame)
    assert len(result.cumulative_values) == len(logged_frame)
    assert sum(result.action_counts.values()) == len(logged_frame)
