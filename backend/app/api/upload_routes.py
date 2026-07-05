"""Upload and dataset API routes."""
import os
import uuid
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Dataset, UploadedFile, User
from app.auth.dependencies import get_current_user
from app.schemas import MessageResponse, UploadResponse
from app.utils.dataset import build_preview, compute_missing, load_dataset
from app.utils.logging import get_logger

logger = get_logger("api.upload")

router = APIRouter(prefix="/upload", tags=["Upload"])

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate extension
    filename = file.filename or "upload.csv"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}. Allowed: CSV, XLSX, XLS")

    # Validate size
    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds max size of {settings.max_upload_size_mb}MB")
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    # Store file
    stored_name = f"{uuid.uuid4().hex}{ext}"
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_path = upload_dir / stored_name
    stored_path.write_bytes(content)

    # Read with pandas
    try:
        df = load_dataset(str(stored_path))
    except Exception as e:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Could not parse file: {e}")

    if df.empty:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="File contains no data rows")

    missing_total, _ = compute_missing(df)
    duplicates = int(df.duplicated().sum())
    preview = build_preview(df)

    dataset = Dataset(
        user_id=current_user.id,
        filename=filename,
        stored_path=str(stored_path),
        file_type=ext.lstrip("."),
        row_count=len(df),
        column_count=df.shape[1],
        file_size_bytes=len(content),
        preview=preview,
    )
    db.add(dataset)
    db.flush()

    uploaded = UploadedFile(
        dataset_id=dataset.id,
        user_id=current_user.id,
        original_name=filename,
        stored_name=stored_name,
        mime_type=file.content_type,
    )
    db.add(uploaded)
    db.commit()
    db.refresh(dataset)

    logger.info("Dataset uploaded: id=%s rows=%d cols=%d user=%s", dataset.id, len(df), df.shape[1], current_user.id)

    return UploadResponse(
        dataset_id=dataset.id,
        filename=filename,
        file_type=dataset.file_type,
        row_count=dataset.row_count,
        column_count=dataset.column_count,
        missing_values=missing_total,
        duplicates=duplicates,
        file_size_bytes=dataset.file_size_bytes,
        preview=preview,
        columns=list(df.columns),
        created_at=dataset.created_at,
    )


@router.get("/{dataset_id}", response_model=UploadResponse)
def get_dataset(dataset_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return UploadResponse(
        dataset_id=ds.id,
        filename=ds.filename,
        file_type=ds.file_type,
        row_count=ds.row_count,
        column_count=ds.column_count,
        missing_values=ds.preview.get("shape", [0, 0])[0],
        duplicates=0,
        file_size_bytes=ds.file_size_bytes,
        preview=ds.preview,
        columns=ds.preview.get("columns", []),
        created_at=ds.created_at,
    )


@router.delete("/{dataset_id}", response_model=MessageResponse)
def delete_dataset(dataset_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    try:
        if os.path.exists(ds.stored_path):
            os.remove(ds.stored_path)
    except OSError:
        pass
    db.delete(ds)
    db.commit()
    return MessageResponse(message="Dataset deleted")
