"""Unit tests for dataset utilities and analysis service."""
import numpy as np
import pandas as pd

from app.utils.dataset import (
    build_preview,
    compute_missing,
    compute_outliers,
    detect_feature_types,
    suggest_target_columns,
)
from app.services.analysis_service import (
    build_dataset_summary,
    compute_health_score,
    compute_kpis,
    compute_quality_score,
    detect_business_context,
    detect_issues,
)


def _sample_df():
    return pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=20, freq="D"),
        "revenue": np.arange(100, 120, dtype=float),
        "profit": np.arange(50, 70, dtype=float),
        "region": ["North", "South"] * 10,
        "customer_count": np.arange(10, 30, dtype=float),
    })


def test_detect_feature_types():
    df = _sample_df()
    types = detect_feature_types(df)
    assert "revenue" in types["numerical"]
    assert "region" in types["categorical"]
    assert "date" in types["datetime"]


def test_suggest_target_columns():
    df = _sample_df()
    types = detect_feature_types(df)
    suggestions = suggest_target_columns(df, types)
    assert "revenue" in suggestions


def test_build_preview():
    df = _sample_df()
    preview = build_preview(df, rows=5)
    assert preview["shape"] == [20, 5]
    assert len(preview["head"]) == 5
    assert "columns" in preview


def test_compute_missing():
    df = _sample_df()
    df.loc[0, "revenue"] = np.nan
    total, per_col = compute_missing(df)
    assert total == 1
    assert "revenue" in per_col


def test_build_dataset_summary():
    df = _sample_df()
    summary = build_dataset_summary(df)
    assert summary["row_count"] == 20
    assert summary["column_count"] == 5
    assert "feature_types" in summary


def test_detect_business_context():
    df = _sample_df()
    types = detect_feature_types(df)
    ctx = detect_business_context(df, types)
    assert "revenue" in ctx["financial_columns"]
    assert "region" in ctx["regional_columns"]


def test_compute_kpis():
    df = _sample_df()
    types = detect_feature_types(df)
    ctx = detect_business_context(df, types)
    kpis = compute_kpis(df, ctx)
    assert "revenue_trend" in kpis or "primary_metric" in kpis


def test_compute_quality_score():
    df = _sample_df()
    summary = build_dataset_summary(df)
    score = compute_quality_score(summary)
    assert 0 <= score <= 100


def test_compute_health_score():
    df = _sample_df()
    types = detect_feature_types(df)
    ctx = detect_business_context(df, types)
    kpis = compute_kpis(df, ctx)
    score = compute_health_score(kpis)
    assert 0 <= score <= 100


def test_detect_issues():
    df = _sample_df()
    summary = build_dataset_summary(df)
    types = detect_feature_types(df)
    ctx = detect_business_context(df, types)
    kpis = compute_kpis(df, ctx)
    issues = detect_issues(df, summary, kpis, ctx)
    assert isinstance(issues, list)
    assert len(issues) >= 1
    assert "issue" in issues[0]
    assert "severity" in issues[0]
