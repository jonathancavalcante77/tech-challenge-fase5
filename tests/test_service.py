from concurrent.futures import ThreadPoolExecutor

from datathon.policies import ThompsonSamplingPolicy
from datathon.service import RecommendationService


def test_feedback_is_applied_once_under_concurrency(tmp_path, snapshot_path, context):
    service = RecommendationService(
        tmp_path / "policy.json",
        snapshot_path,
        tmp_path / "decisions.db",
        "mutable",
    )
    decision = service.recommend(context)
    before = service.policy.posterior()[decision["segment"]][decision["action"]].copy()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(
            executor.map(lambda _: service.feedback(decision["decision_id"], 1), range(2))
        )

    statuses = sorted(result["status"] for result in results)
    after = service.policy.posterior()[decision["segment"]][decision["action"]]
    assert statuses == ["duplicate", "updated"]
    assert after[0] == before[0] + 1
    assert after[1] == before[1]


def test_sqlite_state_recovers_when_json_mirror_is_missing(tmp_path, snapshot_path, context):
    state_path = tmp_path / "policy.json"
    database_path = tmp_path / "decisions.db"
    service = RecommendationService(state_path, snapshot_path, database_path, "mutable")
    decision = service.recommend(context)
    service.feedback(decision["decision_id"], 1)
    learned_state = service.policy.posterior()
    state_path.unlink()

    restored = RecommendationService(state_path, snapshot_path, database_path, "mutable")
    assert restored.policy.posterior() == learned_state


def test_readonly_uses_snapshot_even_when_mutable_state_exists(tmp_path, snapshot_path, context):
    state_path = tmp_path / "policy.json"
    database_path = tmp_path / "decisions.db"
    mutable = RecommendationService(state_path, snapshot_path, database_path, "mutable")
    decision = mutable.recommend(context)
    mutable.feedback(decision["decision_id"], 1)
    state_before = state_path.read_bytes()

    readonly = RecommendationService(state_path, snapshot_path, database_path, "readonly")

    assert readonly.policy.posterior() == ThompsonSamplingPolicy.load(snapshot_path).posterior()
    assert readonly.policy.posterior() != mutable.policy.posterior()
    readonly.recommend(context)
    assert state_path.read_bytes() == state_before
    assert readonly.store.stats() == {"decisions": 1, "feedbacks": 1}
