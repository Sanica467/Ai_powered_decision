"""AutoML pipeline: task detection, multi-model training, comparison, prediction."""
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor, RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

from app.utils.dataset import detect_feature_types
from app.utils.logging import get_logger

logger = get_logger("ml")

try:
    from xgboost import XGBClassifier, XGBRegressor
    _XGB = True
except ImportError:  # pragma: no cover
    _XGB = False

try:
    from lightgbm import LGBMClassifier, LGBMRegressor
    _LGBM = True
except ImportError:  # pragma: no cover
    _LGBM = False


def detect_task_type(df: pd.DataFrame, target: str) -> str:
    """Determine if the prediction task is regression, classification, or time series."""
    if target not in df.columns:
        raise ValueError(f"Target column '{target}' not found in dataset")
    series = df[target].dropna()
    nunique = series.nunique()
    if pd.api.types.is_numeric_dtype(series) and nunique > 15:
        # Check for datetime index -> time series
        datetime_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
        if datetime_cols or any("date" in c.lower() or "time" in c.lower() for c in df.columns):
            return "time_series"
        return "regression"
    return "classification"


def _preprocess(df: pd.DataFrame, target: str) -> Tuple[pd.DataFrame, pd.Series, Dict[str, Any]]:
    """Preprocess: encode categoricals, fill missing, return X, y, and metadata."""
    feature_types = detect_feature_types(df)
    encoders: Dict[str, LabelEncoder] = {}
    df = df.copy()

    for col in df.columns:
        if col == target:
            continue
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].astype("int64") // 10**9
        elif df[col].dtype == object or isinstance(df[col].dtype, pd.CategoricalDtype):
            df[col] = df[col].fillna("missing").astype(str)
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col])
            encoders[col] = le
        elif pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(df[col].median())
        else:
            # Fallback: convert to string and label-encode
            df[col] = df[col].fillna("missing").astype(str)
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col])
            encoders[col] = le

    y = df[target]
    X = df.drop(columns=[target])

    # Encode target if classification
    if not pd.api.types.is_numeric_dtype(y):
        le_y = LabelEncoder()
        y = pd.Series(le_y.fit_transform(y.astype(str)), index=y.index, name=target)
    else:
        y = y.fillna(y.median())

    return X, y, {"encoders": {k: "LabelEncoder" for k in encoders}, "feature_names": list(X.columns)}


def _get_models(task: str) -> Dict[str, Any]:
    if task == "classification":
        models: Dict[str, Any] = {
            "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42),
            "GradientBoosting": GradientBoostingClassifier(random_state=42),
            "DecisionTree": DecisionTreeClassifier(random_state=42),
            "LogisticRegression": LogisticRegression(max_iter=1000, random_state=42),
        }
        if _XGB:
            models["XGBoost"] = XGBClassifier(use_label_encoder=False, eval_metric="logloss", random_state=42, verbosity=0)
        if _LGBM:
            models["LightGBM"] = LGBMClassifier(random_state=42, verbose=-1)
    else:
        models = {
            "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42),
            "GradientBoosting": GradientBoostingRegressor(random_state=42),
            "DecisionTree": DecisionTreeRegressor(random_state=42),
            "LinearRegression": LinearRegression(),
        }
        if _XGB:
            models["XGBoost"] = XGBRegressor(random_state=42, verbosity=0)
        if _LGBM:
            models["LightGBM"] = LGBMRegressor(random_state=42, verbose=-1)
    return models


def _compute_metrics(y_true, y_pred, task: str) -> Dict[str, Any]:
    if task == "classification":
        return {
            "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
            "precision": round(float(precision_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
            "recall": round(float(recall_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
            "f1": round(float(f1_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
        }
    mse = float(mean_squared_error(y_true, y_pred))
    return {
        "rmse": round(float(np.sqrt(mse)), 4),
        "mae": round(float(mean_absolute_error(y_true, y_pred)), 4),
        "r2": round(float(r2_score(y_true, y_pred)), 4),
    }


def _feature_importance(model, feature_names: List[str]) -> Dict[str, float]:
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    elif hasattr(model, "coef_"):
        importances = np.abs(model.coef_).ravel()
        if importances.shape[0] != len(feature_names):
            return {}
    else:
        return {}
    pairs = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)
    return {name: round(float(imp), 6) for name, imp in pairs[:20]}


def train_auto_ml(
    df: pd.DataFrame,
    target_column: str,
    horizon: int = 12,
) -> Dict[str, Any]:
    """Run the full AutoML pipeline and return results."""
    start = time.time()
    task = detect_task_type(df, target_column)
    logger.info("AutoML: task=%s target=%s", task, target_column)

    X, y, meta = _preprocess(df, target_column)
    if len(X) < 10:
        raise ValueError("Dataset too small for training (minimum 10 rows required)")

    test_size = 0.2 if len(X) > 50 else 0.15
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42,
        stratify=y if task == "classification" and y.nunique() > 1 else None,
    )

    models = _get_models(task)
    comparison: List[Dict[str, Any]] = []
    best_model_name: Optional[str] = None
    best_model_obj: Any = None
    best_score: float = -np.inf
    best_metrics: Dict[str, Any] = {}

    for name, model in models.items():
        try:
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            metrics = _compute_metrics(y_test, preds, task)
            score = metrics.get("f1", metrics.get("r2", 0))
            comparison.append({"model": name, "metrics": metrics})
            if score > best_score:
                best_score = score
                best_model_name = name
                best_model_obj = model
                best_metrics = metrics
            logger.info("AutoML: %s trained, score=%.4f", name, score)
        except Exception as e:  # noqa: BLE001
            logger.warning("AutoML: %s failed: %s", name, e)
            comparison.append({"model": name, "metrics": {}, "error": str(e)})

    if best_model_obj is None:
        raise RuntimeError("All models failed to train")

    fi = _feature_importance(best_model_obj, meta["feature_names"])

    # Generate predictions
    if task == "time_series":
        predictions = _forecast(best_model_obj, X, horizon)
    elif task == "classification":
        proba = best_model_obj.predict_proba(X.tail(1)) if hasattr(best_model_obj, "predict_proba") else None
        predictions = {
            "next_prediction": float(best_model_obj.predict(X.tail(1))[0]),
            "probabilities": (
                {str(i): round(float(p), 4) for i, p in enumerate(proba[0])}
                if proba is not None else {}
            ),
        }
    else:
        predictions = {
            "next_prediction": float(best_model_obj.predict(X.tail(1))[0]),
            "forecast": [float(v) for v in best_model_obj.predict(X.tail(horizon))],
        }

    elapsed = round(time.time() - start, 2)
    logger.info("AutoML complete: best=%s score=%.4f (%.2fs)", best_model_name, best_score, elapsed)

    return {
        "task_type": task,
        "target_column": target_column,
        "best_model": best_model_name,
        "metrics": best_metrics,
        "feature_importance": fi,
        "predictions": predictions,
        "model_comparison": comparison,
        "feature_names": meta["feature_names"],
        "training_time_seconds": elapsed,
    }


def _forecast(model, X: pd.DataFrame, horizon: int) -> Dict[str, Any]:
    """Simple time-series forecast using the last known feature row."""
    last_row = X.tail(1)
    forecast = []
    for _ in range(horizon):
        pred = float(model.predict(last_row)[0])
        forecast.append(pred)
    return {
        "next_prediction": forecast[0] if forecast else 0,
        "forecast": forecast,
        "horizon": horizon,
    }


def predict_targets(df: pd.DataFrame, target_column: str, horizon: int = 12) -> Dict[str, Any]:
    """Convenience wrapper for the /predict endpoint."""
    return train_auto_ml(df, target_column, horizon=horizon)
