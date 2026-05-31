"""Dataset, preprocessing, and ML inference path tests."""

import numpy as np

from app.state_store import state_store
from ml import preprocess
from ml.predictor import prediction_service
from ml.registry import registry
from sim.dataset_loader import HybridTrafficDatasetLoader


class FakeFeatureScaler:
    """Feature scaler test double."""

    def transform(self, matrix):
        assert matrix.shape == (1, 41)
        return matrix


class FakeTargetScaler:
    """Target scaler test double."""

    def inverse_transform(self, value):
        return value


class FakeModel:
    """Keras model test double."""

    def predict(self, model_input, verbose=0):
        assert model_input.shape == (1, 60, 41)
        return np.asarray([[123.0]])


def test_dataset_loader_normalizes_data_team_csv():
    loader = HybridTrafficDatasetLoader()
    metadata = loader.get_dataset_metadata()
    assert metadata.rows > 0
    assert metadata.intersections == 4

    rows = loader.get_rows()
    assert rows[0].intersection_id == "INT-001"
    assert {row.intersection_id for row in rows[:8]} == {
        "INT-001",
        "INT-002",
        "INT-003",
        "INT-004",
    }


def test_feature_vector_matches_manifest_width():
    state = state_store.get_state("INT-001")
    assert state is not None
    features = preprocess.build_feature_vector(state)
    matrix = preprocess.features_to_matrix(features)
    assert matrix.shape == (1, 41)


def test_lstm_prediction_path_uses_sequence_and_horizon_scaler():
    registry.clear()
    registry.set_artifacts(
        models={"15m": FakeModel(), "2h": FakeModel(), "4h": FakeModel()},
        scalers={
            "feat": FakeFeatureScaler(),
            "target": {
                "15m": FakeTargetScaler(),
                "2h": FakeTargetScaler(),
                "4h": FakeTargetScaler(),
            },
        },
        config={"seq_len": 60},
    )
    registry.set_fallback_mode(False)

    result = prediction_service.predict("INT-001", "15m")
    assert result.source == "lstm"
    assert result.predicted_vehicle_count == 123

    registry.clear()
