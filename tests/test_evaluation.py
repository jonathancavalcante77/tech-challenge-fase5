import pytest

from datathon.evaluation import (
    fixed_policy_interval,
    fixed_policy_value,
    policy_value,
    sequential_replay,
)
from datathon.policies import ThompsonSamplingPolicy


def test_fixed_policy_ips_uses_random_assignment(logged_frame):
    value = fixed_policy_value(logged_frame, "mens_email")
    assert value == 0.75


def test_replay_returns_consistent_shape(logged_frame):
    result = sequential_replay(logged_frame, ThompsonSamplingPolicy(seed=3))
    assert result.total_rows == len(logged_frame)
    assert len(result.cumulative_values) == len(logged_frame)
    assert sum(result.action_counts.values()) == len(logged_frame)
    assert result.ci_lower <= result.estimated_value <= result.ci_upper


def test_frozen_policy_ips_matches_fixed_estimator(logged_frame):
    value, matched = policy_value(logged_frame, lambda _context: "mens_email")
    standard_error, lower, upper = fixed_policy_interval(logged_frame, "mens_email")

    assert value == fixed_policy_value(logged_frame, "mens_email")
    assert matched == 2
    assert standard_error > 0
    assert lower <= value <= upper


def test_evaluation_rejects_invalid_inputs(logged_frame):
    with pytest.raises(ValueError, match="Ação desconhecida"):
        fixed_policy_value(logged_frame, "unknown")
    with pytest.raises(ValueError, match="propensão"):
        policy_value(logged_frame, lambda _context: "mens_email", propensity=0)
    with pytest.raises(ValueError, match="Colunas de replay ausentes"):
        sequential_replay(logged_frame.drop(columns="conversion"), ThompsonSamplingPolicy())
