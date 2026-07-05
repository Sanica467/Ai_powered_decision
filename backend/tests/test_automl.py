"""Unit tests for the AutoML pipeline."""
import numpy as np
import pandas as pd
import pytest

from app.ml.automl import detect_task_type, train_auto_ml


def _regression_df():
    rng = np.random.RandomState(42)
    n = 100
    return pd.DataFrame({
        "feature_a": rng.randn(n),
        "feature_b": rng.randn(n) * 2,
        "feature_c": rng.randint(0, 10, n),
        "revenue": rng.randn(n) * 10 + 50,
    })


def _classification_df():
    rng = np.random.RandomState(42)
    n = 100
    x = rng.randn(n)
    y = (x + rng.randn(n) * 0.5 > 0).astype(int)
    return pd.DataFrame({"feature_a": x, "feature_b": rng.randn(n), "churn": y})


def test_detect_task_type_regression():
    df = _regression_df()
    assert detect_task_type(df, "revenue") == "regression"


def test_detect_task_type_classification():
    df = _classification_df()
    assert detect_task_type(df, "churn") == "classification"


def test_train_auto_ml_regression():
    df = _regression_df()
    result = train_auto_ml(df, "revenue")
    assert result["task_type"] == "regression"
    assert result["best_model"] is not None
    assert "rmse" in result["metrics"]
    assert "r2" in result["metrics"]
    assert len(result["model_comparison"]) >= 3
    assert "next_prediction" in result["predictions"]


def test_train_auto_ml_classification():
    df = _classification_df()
    result = train_auto_ml(df, "churn")
    assert result["task_type"] == "classification"
    assert "accuracy" in result["metrics"]
    assert "f1" in result["metrics"]
    assert len(result["model_comparison"]) >= 3


def test_train_auto_ml_invalid_target():
    df = _regression_df()
    with pytest.raises(ValueError):
        train_auto_ml(df, "nonexistent_column")


def test_train_auto_ml_feature_importance():
    df = _regression_df()
    result = train_auto_ml(df, "revenue")
    fi = result["feature_importance"]
    assert isinstance(fi, dict)
    assert len(fi) > 0
