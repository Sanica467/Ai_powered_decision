"""Multi-agent orchestration for DecisionAI.

Each agent wraps a focused responsibility. The orchestrator coordinates them
into the full analysis pipeline.
"""
from dataclasses import dataclass
from typing import Any, Dict, List

import pandas as pd

from app.ml.automl import train_auto_ml
from app.services.analysis_service import (
    build_dataset_summary,
    compute_health_score,
    compute_kpis,
    compute_quality_score,
    detect_business_context,
    detect_issues,
)
from app.services.gemini_service import (
    business_diagnosis,
    executive_summary,
    generate_recommendations,
    root_cause_analysis,
)
from app.utils.dataset import detect_feature_types, suggest_target_columns
from app.utils.logging import get_logger

logger = get_logger("app.agents")


@dataclass
class AgentResult:
    agent: str
    result: Dict[str, Any]


class DataAgent:
    """Understands and profiles the dataset."""

    name = "Data Agent"

    def run(self, df: pd.DataFrame) -> AgentResult:
        logger.info("%s: profiling dataset", self.name)
        summary = build_dataset_summary(df)
        context = detect_business_context(df, detect_feature_types(df))
        targets = suggest_target_columns(df, detect_feature_types(df))
        quality = compute_quality_score(summary)
        return AgentResult(
            agent=self.name,
            result={
                "summary": summary,
                "business_context": context,
                "target_suggestions": targets,
                "quality_score": quality,
            },
        )


class BusinessAnalystAgent:
    """Computes KPIs, health score, and detects business issues."""

    name = "Business Analyst Agent"

    def run(self, df: pd.DataFrame, data_result: Dict[str, Any]) -> AgentResult:
        logger.info("%s: computing KPIs and diagnosis", self.name)
        kpis = compute_kpis(df, data_result["business_context"])
        health = compute_health_score(kpis)
        issues = detect_issues(df, data_result["summary"], kpis, data_result["business_context"])
        return AgentResult(
            agent=self.name,
            result={
                "kpis": kpis,
                "health_score": health,
                "issues": issues,
            },
        )


class MLEngineerAgent:
    """Runs the AutoML pipeline."""

    name = "ML Engineer Agent"

    def run(self, df: pd.DataFrame, target_column: str, horizon: int = 12) -> AgentResult:
        logger.info("%s: running AutoML for target=%s", self.name, target_column)
        ml_result = train_auto_ml(df, target_column, horizon=horizon)
        return AgentResult(agent=self.name, result=ml_result)


class RiskAnalystAgent:
    """Performs root cause analysis on detected issues."""

    name = "Risk Analyst Agent"

    def run(
        self,
        summary: Dict[str, Any],
        kpis: Dict[str, Any],
        issues: List[Dict[str, Any]],
        feature_importance: Dict[str, Any],
    ) -> AgentResult:
        logger.info("%s: root cause analysis", self.name)
        rca = root_cause_analysis(summary, kpis, issues, feature_importance)
        return AgentResult(agent=self.name, result=rca)


class StrategyAgent:
    """Generates business recommendations."""

    name = "Strategy Agent"

    def run(
        self,
        summary: Dict[str, Any],
        kpis: Dict[str, Any],
        issues: List[Dict[str, Any]],
        predictions: Dict[str, Any],
    ) -> AgentResult:
        logger.info("%s: generating recommendations", self.name)
        recs = generate_recommendations(summary, kpis, issues, predictions)
        return AgentResult(agent=self.name, result={"recommendations": recs})


class ExecutiveReportAgent:
    """Generates the executive summary."""

    name = "Executive Report Agent"

    def run(
        self,
        summary: Dict[str, Any],
        kpis: Dict[str, Any],
        issues: List[Dict[str, Any]],
        predictions: Dict[str, Any],
        recommendations: List[Dict[str, Any]],
    ) -> AgentResult:
        logger.info("%s: generating executive summary", self.name)
        es = executive_summary(summary, kpis, issues, predictions, recommendations)
        return AgentResult(agent=self.name, result=es)


class Orchestrator:
    """Coordinates all agents into the full analysis pipeline."""

    def __init__(self):
        self.data_agent = DataAgent()
        self.business_agent = BusinessAnalystAgent()
        self.ml_agent = MLEngineerAgent()
        self.risk_agent = RiskAnalystAgent()
        self.strategy_agent = StrategyAgent()
        self.report_agent = ExecutiveReportAgent()

    def run_full_pipeline(
        self, df: pd.DataFrame, target_column: str, horizon: int = 12
    ) -> Dict[str, Any]:
        """Execute the complete DecisionAI pipeline."""
        logger.info("Orchestrator: starting full pipeline")

        data_res = self.data_agent.run(df)
        biz_res = self.business_agent.run(df, data_res.result)
        ml_res = self.ml_agent.run(df, target_column, horizon)
        risk_res = self.risk_agent.run(
            data_res.result["summary"],
            biz_res.result["kpis"],
            biz_res.result["issues"],
            ml_res.result.get("feature_importance", {}),
        )
        strategy_res = self.strategy_agent.run(
            data_res.result["summary"],
            biz_res.result["kpis"],
            biz_res.result["issues"],
            ml_res.result.get("predictions", {}),
        )
        report_res = self.report_agent.run(
            data_res.result["summary"],
            biz_res.result["kpis"],
            biz_res.result["issues"],
            ml_res.result.get("predictions", {}),
            strategy_res.result.get("recommendations", []),
        )

        logger.info("Orchestrator: pipeline complete")
        return {
            "data": data_res.result,
            "business": biz_res.result,
            "ml": ml_res.result,
            "risk": risk_res.result,
            "strategy": strategy_res.result,
            "executive": report_res.result,
        }
