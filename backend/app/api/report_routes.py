"""Report generation and download API routes."""
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Analysis, Dataset, Prediction, Recommendation, Report, User
from app.auth.dependencies import get_current_user
from app.schemas import ReportRequest, ReportResponse
from app.reports.report_service import generate_pdf_report
from app.utils.logging import get_logger

logger = get_logger("api.report")

router = APIRouter(tags=["Reports"])


@router.post("/report", response_model=ReportResponse)
def create_report(
    payload: ReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ds = db.query(Dataset).filter(Dataset.id == payload.dataset_id, Dataset.user_id == current_user.id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")

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
    recommendations = rec_record.recommendations.get("items", []) if rec_record else []
    executive = rec_record.executive_summary if rec_record else {}

    report_data = generate_pdf_report(
        dataset_id=ds.id,
        summary=analysis.summary,
        kpis=analysis.kpis,
        issues=analysis.diagnosis.get("issues", []),
        root_causes=analysis.root_causes or {},
        predictions=prediction.__dict__ if prediction else {},
        recommendations=recommendations,
        executive=executive,
        quality_score=analysis.quality_score,
        health_score=analysis.health_score,
    )

    report = Report(
        dataset_id=ds.id,
        user_id=current_user.id,
        file_path=report_data["file_path"],
        download_url=report_data["download_url"],
        file_size_bytes=report_data["file_size_bytes"],
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    logger.info("Report created: id=%s file=%s", report.id, report_data["filename"])

    return ReportResponse(
        report_id=report.id,
        dataset_id=ds.id,
        download_url=report.download_url,
        file_size_bytes=report.file_size_bytes,
        created_at=report.created_at,
    )


@router.get("/reports/download/{filename}")
def download_report(filename: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = db.query(Report).filter(Report.download_url.like(f"%{filename}")).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report file missing")
    return FileResponse(
        report.file_path,
        media_type="application/pdf",
        filename=filename,
    )


@router.get("/reports", response_model=list)
def list_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    reports = db.query(Report).filter(Report.user_id == current_user.id).order_by(Report.created_at.desc()).all()
    return [
        {
            "report_id": r.id,
            "dataset_id": r.dataset_id,
            "download_url": r.download_url,
            "file_size_bytes": r.file_size_bytes,
            "created_at": r.created_at.isoformat(),
        }
        for r in reports
    ]
