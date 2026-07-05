"""ML package."""
from app.ml.automl import detect_task_type, predict_targets, train_auto_ml

__all__ = ["detect_task_type", "predict_targets", "train_auto_ml"]
