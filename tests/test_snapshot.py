import json

import pandas as pd
import pytest
from scripts import build_policy_snapshot

from datathon.data import sha256, stratified_split
from datathon.policies import ThompsonSamplingPolicy, fit_policy


@pytest.fixture
def snapshot_inputs(tmp_path, logged_frame, monkeypatch):
    frame = pd.concat([logged_frame] * 15, ignore_index=True)
    data_path = tmp_path / "dataset.csv"
    frame.to_csv(data_path, index=False)
    monkeypatch.setattr(build_policy_snapshot, "load_clean", lambda _path: frame.copy())
    seed = 73
    train, _, _ = stratified_split(frame, seed=seed)
    trained = ThompsonSamplingPolicy(seed=seed, prior_alpha=2.0, prior_beta=3.0)
    fit_policy(trained, train)
    summary = {
        "selected_policy": "thompson_sampling",
        "evaluation_protocol": "stratified-shuffled-replay-v2",
        "dataset_sha256": sha256(data_path),
        "seed": seed,
        "prior_alpha": 2.0,
        "prior_beta": 3.0,
        "training_state_sha256": trained.training_fingerprint(),
    }
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    return data_path, summary_path, tmp_path / "snapshot.json", summary


def test_snapshot_preserves_evaluated_seed_priors_and_provenance(snapshot_inputs):
    data_path, summary_path, output_path, summary = snapshot_inputs

    built = build_policy_snapshot.build(data_path, summary_path, output_path)
    restored = ThompsonSamplingPolicy.load(output_path)

    assert restored.seed == 73
    assert restored.prior_alpha == 2.0
    assert restored.prior_beta == 3.0
    assert restored.to_payload() == built.to_payload()
    assert restored.training_fingerprint() == summary["training_state_sha256"]
    assert restored.provenance == {
        "dataset_sha256": sha256(data_path),
        "evaluation_protocol": "stratified-shuffled-replay-v2",
        "training_state_sha256": summary["training_state_sha256"],
        "seed": 73,
    }
    observed_updates = sum(
        alpha + beta - 5.0
        for actions in restored.posterior().values()
        for alpha, beta in actions.values()
    )
    assert observed_updates == 36


@pytest.mark.parametrize(
    ("field", "invalid_value", "message"),
    [
        ("selected_policy", "baseline_no_email", "não selecionou Thompson Sampling"),
        ("evaluation_protocol", "stratified-replay-v1", "Protocolo de avaliação incompatível"),
        ("dataset_sha256", "0" * 64, "Dataset diferente"),
        ("training_state_sha256", "0" * 64, "Estado de treino diferente"),
        ("seed", 74, "Estado de treino diferente"),
        ("prior_alpha", 4.0, "Estado de treino diferente"),
    ],
)
def test_incompatible_evaluation_preserves_existing_snapshot(
    snapshot_inputs, field, invalid_value, message
):
    data_path, summary_path, output_path, summary = snapshot_inputs
    build_policy_snapshot.build(data_path, summary_path, output_path)
    previous_snapshot = output_path.read_bytes()
    summary[field] = invalid_value
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        build_policy_snapshot.build(data_path, summary_path, output_path)

    assert output_path.read_bytes() == previous_snapshot
