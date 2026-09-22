import pytest

from datathon.config import PolicyMode, Settings


def test_policy_mode_is_validated():
    assert Settings(policy_mode="readonly").policy_mode is PolicyMode.READONLY
    with pytest.raises(ValueError, match="POLICY_MODE inválido"):
        Settings(policy_mode="read-only")
