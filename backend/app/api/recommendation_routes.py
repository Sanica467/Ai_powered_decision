"""Recommendations and executive summary API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Analysis, Dataset, Prediction, Recommendation, User
from app.auth.dependencies import get_current_user
from app.schemas import (
    RecommendationRequest,
    RecommendationResponse,
    SummaryRequest,
    SummaryResponse,
)
from app.services.gemini_service import executive_summary, generate_recommendations
from app.utils.dataset import load_dataset
from app.utils.logging import get_logger

logger = get_logger("api.recommendations")

router = APIRouter(tags=["Recommendations"])


def _load_user_dataset(db: Session, dataset_id: str, user: User) -> Dataset:
    ds = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == user.id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return ds


@router.post("/recommendations", response_model=RecommendationResponse)
def recommendations(
    payload: RecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ds = _load_user_dataset(db, payload.dataset_id, current_user)

    analysis = None
    if payload.analysis_id:
        analysis = db.query(Analysis).filter(Analysis.id == payload.analysis_id).first()
    if not analysis:
        analysis = db.query(Analysis).filter(Analysis.dataset_id == ds.id).order_by(Analysis.created_at.desc()).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis found. Run /analyze first.")

    prediction = None
    if payload.prediction_id:
        prediction = db.query(Prediction).filter(Prediction.id == payload.prediction_id).first()
    if not prediction:
        prediction = db.query(Prediction).filter(Prediction.dataset_id == ds.id).order_by(Prediction.created_at.desc()).first()

    recs = generate_recommendations(
        analysis.summary,
        analysis.kpis,
        analysis.diagnosis.get("issues", []),
        prediction.predictions if prediction else {},
    )

    rec_record = Recommendation(
        dataset_id=ds.id,
        user_id=current_user.id,
        recommendations={"items": recs},
    )
    db.add(rec_record)
    db.commit()
    db.refresh(rec_record)

    return RecommendationResponse(
        recommendation_id=rec_record.id,
        dataset_id=ds.id,
        recommendations=recs,
        created_at=rec_record.created_at,
    )


@router.post("/summary", response_model=SummaryResponse)
def executive_summary_endpoint(
    payload: SummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ds = _load_user_dataset(db, payload.dataset_id, current_user)

    analysis = None
    if payload.analysis_id:
        analysis = db.query(Analysis).filter(Analysis.id == payload.analysis_id).first()
    if not analysis:
        analysis = db.query(Analysis).filter(Analysis.dataset_id == ds.id).order_by(Analysis.created_at.desc()).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis found. Run /analyze first.")

    prediction = None
    if payload.prediction_id:
        prediction = db.query(Prediction).filter(Prediction.id == payload.prediction_id).first()
    if not prediction:
        prediction = db.query(Prediction).filter(Prediction.dataset_id == ds.id).order_by(Prediction.created_at.desc()).first()

    rec_record = db.query(Recommendation).filter(
        Recommendation.dataset_id == ds.id
    ).order_by(Recommendation.created_at.desc()).first()
    recs = rec_record.recommendations.get("items", []) if rec_record else []

    es = executive_summary(
        analysis.summary,
        analysis.kpis,
        analysis.diagnosis.get("issues", []),
        prediction.predictions if prediction else {},
        recs,
    )

    rec_record = Recommendation(
        dataset_id=ds.id,
        user_id=current_user.id,
        recommendations=rec_record.recommendations if rec_record else {},
        executive_summary=es,
    )
    db.add(rec_record)
    db.commit()
    db.refresh(rec_record)

    return SummaryResponse(
        summary_id=rec_record.id,
        dataset_id=ds.id,
        executive_summary=es,
        created_at=rec_record.created_at,
    )
