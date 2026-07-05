"""Dataset analysis service: summary, KPIs, quality/health scores, diagnosis."""
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from app.utils.dataset import compute_missing, compute_outliers, detect_feature_types
from app.utils.logging import get_logger

logger = get_logger("app.analysis")


def _classify_kpi(value: float, good_direction: str = "up") -> str:
    """Classify a KPI value into Healthy / Needs Attention / Critical."""
    if pd.isna(value):
        return "Needs Attention"
    if good_direction == "up":
        if value >= 70:
            return "Healthy"
        if value >= 40:
            return "Needs Attention"
        return "Critical"
    else:
        if value <= 30:
            return "Healthy"
        if value <= 60:
            return "Needs Attention"
        return "Critical"


def build_dataset_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate a comprehensive dataset summary."""
    feature_types = detect_feature_types(df)
    total_missing, per_col_missing = compute_missing(df)
    duplicates = int(df.duplicated().sum())
    outliers = compute_outliers(df)

    return {
        "row_count": int(len(df)),
        "column_count": int(df.shape[1]),
        "feature_types": feature_types,
        "missing_values": {
            "total": total_missing,
            "per_column": per_col_missing,
            "percentage": round(total_missing / (df.size) * 100, 2) if df.size else 0,
        },
        "duplicates": duplicates,
        "outliers": outliers,
        "numeric_stats": {
            c: {
                "mean": float(df[c].mean()) if pd.notna(df[c].mean()) else None,
                "std": float(df[c].std()) if pd.notna(df[c].std()) else None,
                "min": float(df[c].min()) if pd.notna(df[c].min()) else None,
                "max": float(df[c].max()) if pd.notna(df[c].max()) else None,
                "median": float(df[c].median()) if pd.notna(df[c].median()) else None,
            }
            for c in df.select_dtypes(include=[np.number]).columns
        },
        "categorical_stats": {
            c: {"unique": int(df[c].nunique()), "top": str(df[c].mode().iloc[0]) if not df[c].mode().empty else None}
            for c in feature_types.get("categorical", [])
            if c in df.columns
        },
    }


def detect_business_context(df: pd.DataFrame, feature_types: dict) -> Dict[str, Any]:
    """Detect the likely business domain and key columns."""
    cols_lower = {c.lower(): c for c in df.columns}
    domain = "general"
    detected = {}

    financial_hints = ["revenue", "profit", "cost", "expense", "margin", "ebitda"]
    sales_hints = ["sales", "units", "quantity", "order", "transaction"]
    customer_hints = ["customer", "client", "churn", "retention", "segment"]
    inventory_hints = ["inventory", "stock", "warehouse", "sku", "supply"]
    regional_hints = ["region", "country", "city", "state", "location", "market"]

    def _find(hints: list) -> list:
        return [cols_lower[h] for h in hints if h in cols_lower]

    detected["financial_columns"] = _find(financial_hints)
    detected["sales_columns"] = _find(sales_hints)
    detected["customer_columns"] = _find(customer_hints)
    detected["inventory_columns"] = _find(inventory_hints)
    detected["regional_columns"] = _find(regional_hints)

    if detected["financial_columns"] and detected["sales_columns"]:
        domain = "retail / sales"
    elif detected["financial_columns"]:
        domain = "finance"
    elif detected["customer_columns"]:
        domain = "customer analytics"
    elif detected["inventory_columns"]:
        domain = "supply chain"

    detected["domain"] = domain
    return detected


def compute_kpis(df: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, Any]:
    """Compute business KPIs and classify each."""
    kpis: Dict[str, Any] = {}
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    def _trend(col: str) -> Dict[str, Any]:
        if col not in df.columns:
            return {}
        series = df[col].dropna()
        if len(series) < 2:
            return {"value": float(series.sum()) if len(series) else 0, "trend": "stable"}
        first_half = series.iloc[: len(series) // 2].mean()
        second_half = series.iloc[len(series) // 2 :].mean()
        if first_half == 0:
            change = 0
        else:
            change = ((second_half - first_half) / abs(first_half)) * 100
        trend = "up" if change > 5 else ("down" if change < -5 else "stable")
        return {
            "current": float(series.iloc[-1]) if len(series) else 0,
            "total": float(series.sum()),
            "average": float(series.mean()),
            "change_pct": round(change, 2),
            "trend": trend,
        }

    for hint, label in [
        (["revenue", "sales", "income"], "revenue_trend"),
        (["profit", "margin", "net"], "profit_trend"),
        (["sales", "units", "quantity", "orders"], "sales_trend"),
        (["customer", "users", "subscribers"], "customer_growth"),
        (["inventory", "stock"], "inventory_health"),
        (["cost", "expense", "operational"], "operational_cost"),
    ]:
        for col in df.columns:
            if any(h in col.lower() for h in hint):
                kpis[label] = _trend(col)
                break

    if not kpis and numeric_cols:
        kpis["primary_metric"] = _trend(numeric_cols[0])

    # Regional performance
    regional_cols = context.get("regional_columns", [])
    if regional_cols and numeric_cols:
        region_col = regional_cols[0]
        metric = numeric_cols[0]
        if region_col in df.columns and metric in df.columns:
            grouped = df.groupby(region_col)[metric].sum().sort_values(ascending=False)
            kpis["regional_performance"] = {
                str(k): float(v) for k, v in grouped.head(10).items()
            }

    return kpis


def compute_quality_score(summary: Dict[str, Any]) -> float:
    """Compute a 0-100 dataset quality score."""
    row_count = summary.get("row_count", 0)
    if row_count == 0:
        return 0.0
    missing_pct = summary["missing_values"]["percentage"]
    dup_pct = (summary["duplicates"] / row_count) * 100 if row_count else 0
    outlier_count = sum(summary.get("outliers", {}).values())
    outlier_pct = (outlier_count / row_count) * 100 if row_count else 0

    score = 100.0
    score -= min(missing_pct * 2, 40)
    score -= min(dup_pct * 2, 20)
    score -= min(outlier_pct * 0.5, 20)
    if row_count < 100:
        score -= 10
    return round(max(0.0, min(100.0, score)), 2)


def compute_health_score(kpis: Dict[str, Any]) -> float:
    """Compute a 0-100 business health score from KPIs."""
    scores = []
    for key, val in kpis.items():
        if not isinstance(val, dict) or "change_pct" not in val:
            continue
        change = val["change_pct"]
        if "cost" in key or "expense" in key:
            change = -change  # cost going down is good
        if change > 10:
            scores.append(90)
        elif change > 0:
            scores.append(70)
        elif change > -10:
            scores.append(50)
        else:
            scores.append(25)
    if not scores:
        return 50.0
    return round(float(np.mean(scores)), 2)


def detect_issues(
    df: pd.DataFrame, summary: Dict[str, Any], kpis: Dict[str, Any], context: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Detect business issues and return structured diagnoses."""
    issues: List[Dict[str, Any]] = []

    for kpi_name, val in kpis.items():
        if not isinstance(val, dict) or "trend" not in val:
            continue
        if val["trend"] == "down":
            severity = "Critical" if val.get("change_pct", 0) < -20 else "Needs Attention"
            issues.append({
                "issue": f"Declining {kpi_name.replace('_', ' ')}",
                "severity": severity,
                "business_impact": f"{kpi_name} changed by {val.get('change_pct', 0)}%",
                "confidence": 0.8,
                "affected_department": _department_for_kpi(kpi_name),
                "affected_region": "All" if "regional" not in kpi_name else "Multiple",
            })

    # Outlier-driven anomalies
    for col, count in summary.get("outliers", {}).items():
        if count > len(df) * 0.05:
            issues.append({
                "issue": f"Anomalies detected in {col}",
                "severity": "Needs Attention",
                "business_impact": f"{count} outlier values in {col} may skew analysis",
                "confidence": 0.7,
                "affected_department": "Data Operations",
                "affected_region": "All",
            })

    # Missing data issue
    if summary["missing_values"]["percentage"] > 10:
        issues.append({
            "issue": "High missing data rate",
            "severity": "Critical" if summary["missing_values"]["percentage"] > 25 else "Needs Attention",
            "business_impact": f"{summary['missing_values']['percentage']}% of values missing",
            "confidence": 0.9,
            "affected_department": "Data Engineering",
            "affected_region": "All",
        })

    if not issues:
        issues.append({
            "issue": "No significant issues detected",
            "severity": "Healthy",
            "business_impact": "All KPIs within expected ranges",
            "confidence": 0.6,
            "affected_department": "All",
            "affected_region": "All",
        })

    return issues


def _department_for_kpi(kpi: str) -> str:
    mapping = {
        "revenue": "Sales",
        "profit": "Finance",
        "sales": "Sales",
        "customer": "Customer Success",
        "inventory": "Supply Chain",
        "operational": "Operations",
    }
    for key, dept in mapping.items():
        if key in kpi:
            return dept
    return "Operations"
