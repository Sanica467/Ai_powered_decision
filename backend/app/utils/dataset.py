"""Dataset loading and inspection helpers."""
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd

from app.utils.logging import get_logger

logger = get_logger("app.dataset")


def load_dataset(path: str) -> pd.DataFrame:
    """Load a CSV or Excel file into a DataFrame."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    suffix = p.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(p)
    elif suffix in (".xlsx", ".xls"):
        df = pd.read_excel(p, engine="openpyxl")
    else:
        raise ValueError(f"Unsupported file type: {suffix}")
    return df


def detect_feature_types(df: pd.DataFrame) -> dict:
    """Classify columns as categorical, numerical, datetime, or text."""
    types: dict = {"categorical": [], "numerical": [], "datetime": [], "text": [], "boolean": []}
    for col in df.columns:
        series = df[col]
        nunique = series.nunique(dropna=True)
        if pd.api.types.is_bool_dtype(series):
            types["boolean"].append(col)
        elif pd.api.types.is_numeric_dtype(series):
            if nunique <= 15 and nunique / max(len(df), 1) < 0.05:
                types["categorical"].append(col)
            else:
                types["numerical"].append(col)
        elif pd.api.types.is_datetime64_any_dtype(series):
            types["datetime"].append(col)
        else:
            if nunique > len(df) * 0.5:
                types["text"].append(col)
            else:
                types["categorical"].append(col)
    return types


def suggest_target_columns(df: pd.DataFrame, feature_types: dict) -> List[str]:
    """Heuristically suggest target columns for prediction."""
    candidates: List[str] = []
    name_hints = (
        "revenue", "sales", "profit", "churn", "demand", "cost",
        "price", "target", "label", "outcome", "y", "default",
    )
    for col in feature_types.get("numerical", []) + feature_types.get("categorical", []):
        lower = col.lower()
        if any(h in lower for h in name_hints):
            candidates.append(col)
    if not candidates and feature_types.get("numerical"):
        candidates.append(feature_types["numerical"][-1])
    return candidates[:5]


def build_preview(df: pd.DataFrame, rows: int = 10) -> dict:
    """Build a JSON-safe preview of the dataset."""
    head = df.head(rows).copy()
    for col in head.columns:
        if pd.api.types.is_datetime64_any_dtype(head[col]):
            head[col] = head[col].astype(str)
    return {
        "columns": list(df.columns),
        "dtypes": {c: str(df[c].dtype) for c in df.columns},
        "head": head.fillna("").to_dict(orient="records"),
        "shape": list(df.shape),
    }


def compute_missing(df: pd.DataFrame) -> Tuple[int, dict]:
    total = int(df.isna().sum().sum())
    per_col = {c: int(df[c].isna().sum()) for c in df.columns if df[c].isna().sum() > 0}
    return total, per_col


def compute_outliers(df: pd.DataFrame) -> dict:
    """IQR-based outlier counts for numeric columns."""
    out: dict = {}
    for col in df.select_dtypes(include=[np.number]).columns:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        count = int(((df[col] < lower) | (df[col] > upper)).sum())
        if count > 0:
            out[col] = count
    return out
