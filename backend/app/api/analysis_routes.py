"""Analysis, diagnosis, and root cause API routes."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents import BusinessAnalystAgent, DataAgent, RiskAnalystAgent
from app.database import get_db
from app.models import Analysis, Dataset, User
from app.auth.dependencies import get_current_user
from app.schemas import (
    AnalysisResponse,
    AnalyzeRequest,
    DiagnosisRequest,
    DiagnosisResponse,
    RootCauseRequest,
    RootCauseResponse,
)
from app.services.analysis_service import (
    build_dataset_summary,
    compute_health_score,
    compute_kpis,
    compute_quality_score,
    detect_business_context,
    detect_issues,
)
from app.services.gemini_service import root_cause_analysis
from app.utils.dataset import detect_feature_types, load_dataset, suggest_target_columns
from app.utils.logging import get_logger

logger = get_logger("api.analysis")

router = APIRouter(tags=["Analysis"])


def _load_user_dataset(db: Session, dataset_id: str, user: User) -> Dataset:
    ds = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == user.id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return ds


@router.post("/analyze", response_model=AnalysisResponse)
def analyze(payload: AnalyzeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ds = _load_user_dataset(db, payload.dataset_id, current_user)
    df = load_dataset(ds.stored_path)

    data_agent = DataAgent()
    biz_agent = BusinessAnalystAgent()

    data_res = data_agent.run(df)
    biz_res = biz_agent.run(df, data_res.result)

    summary = data_res.result["summary"]
    kpis = biz_res.result["kpis"]
    quality = data_res.result["quality_score"]
    health = biz_res.result["health_score"]
    issues = biz_res.result["issues"]

    analysis = Analysis(
        dataset_id=ds.id,
        user_id=current_user.id,
        analysis_type="full",
        summary=summary,
        kpis=kpis,
        quality_score=quality,
        health_score=health,
        diagnosis={"issues": issues},
        root_causes={},
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    logger.info("Analysis complete: id=%s quality=%.1f health=%.1f", analysis.id, quality, health)

    return AnalysisResponse(
        analysis_id=analysis.id,
        dataset_id=ds.id,
        summary=summary,
        kpis=kpis,
        quality_score=quality,
        health_score=health,
        feature_types=data_res.result["summary"]["feature_types"],
        target_suggestions=data_res.result["target_suggestions"],
        created_at=analysis.created_at,
    )


@router.post("/diagnosis", response_model=DiagnosisResponse)
def diagnosis(payload: DiagnosisRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ds = _load_user_dataset(db, payload.dataset_id, current_user)

    analysis = None
    if payload.analysis_id:
        analysis = db.query(Analysis).filter(Analysis.id == payload.analysis_id, Analysis.dataset_id == ds.id).first()
    if not analysis:
        # Run a fresh analysis
        df = load_dataset(ds.stored_path)
        summary = build_dataset_summary(df)
        context = detect_business_context(df, detect_feature_types(df))
        kpis = compute_kpis(df, context)
        issues = detect_issues(df, summary, kpis, context)
        analysis = Analysis(
            dataset_id=ds.id,
            user_id=current_user.id,
            analysis_type="diagnosis",
            summary=summary,
            kpis=kpis,
            quality_score=compute_quality_score(summary),
            health_score=compute_health_score(kpis),
            diagnosis={"issues": issues},
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
    else:
        issues = analysis.diagnosis.get("issues", [])

    return DiagnosisResponse(
        analysis_id=analysis.id,
        dataset_id=ds.id,
        issues=issues,
        created_at=analysis.created_at,
    )


@router.post("/root-cause", response_model=RootCauseResponse)
def root_cause(payload: RootCauseRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ds = _load_user_dataset(db, payload.dataset_id, current_user)

    analysis = None
    if payload.analysis_id:
        analysis = db.query(Analysis).filter(Analysis.id == payload.analysis_id, Analysis.dataset_id == ds.id).first()
    if not analysis:
        df = load_dataset(ds.stored_path)
        summary = build_dataset_summary(df)
        context = detect_business_context(df, detect_feature_types(df))
        kpis = compute_kpis(df, context)
        issues = detect_issues(df, summary, kpis, context)
        analysis = Analysis(
            dataset_id=ds.id,
            user_id=current_user.id,
            analysis_type="root_cause",
            summary=summary,
            kpis=kpis,
            quality_score=compute_quality_score(summary),
            health_score=compute_health_score(kpis),
            diagnosis={"issues": issues},
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)

    rca = root_cause_analysis(
        analysis.summary,
        analysis.kpis,
        analysis.diagnosis.get("issues", []),
        {},
    )
    analysis.root_causes = rca
    db.commit()

    return RootCauseResponse(
        analysis_id=analysis.id,
        dataset_id=ds.id,
        root_causes=rca.get("root_causes", []),
        confidence=rca.get("confidence", 0),
        evidence=rca.get("evidence", []),
        business_explanation=rca.get("business_explanation", ""),
        created_at=analysis.created_at,
    )
