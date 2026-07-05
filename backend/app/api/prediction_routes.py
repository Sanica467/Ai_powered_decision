"""Prediction and what-if simulation API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Dataset, Prediction, User
from app.auth.dependencies import get_current_user
from app.schemas import PredictRequest, PredictionResponse, SimulateRequest, SimulateResponse
from app.ml.automl import train_auto_ml
from app.services.gemini_service import what_if_analysis
from app.utils.dataset import load_dataset, suggest_target_columns, detect_feature_types
from app.utils.logging import get_logger

logger = get_logger("api.predict")

router = APIRouter(tags=["Prediction"])


def _load_user_dataset(db: Session, dataset_id: str, user: User) -> Dataset:
    ds = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == user.id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return ds


@router.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ds = _load_user_dataset(db, payload.dataset_id, current_user)
    df = load_dataset(ds.stored_path)

    target = payload.target_column
    if not target:
        suggestions = suggest_target_columns(df, detect_feature_types(df))
        if not suggestions:
            raise HTTPException(status_code=422, detail="No suitable target column found. Please specify one.")
        target = suggestions[0]
    if target not in df.columns:
        raise HTTPException(status_code=422, detail=f"Target column '{target}' not found in dataset")

    try:
        result = train_auto_ml(df, target, horizon=payload.horizon)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    prediction = Prediction(
        dataset_id=ds.id,
        user_id=current_user.id,
        task_type=result["task_type"],
        target_column=target,
        best_model=result["best_model"],
        metrics=result["metrics"],
        feature_importance=result["feature_importance"],
        predictions=result["predictions"],
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    logger.info("Prediction complete: id=%s model=%s task=%s", prediction.id, result["best_model"], result["task_type"])

    return PredictionResponse(
        prediction_id=prediction.id,
        dataset_id=ds.id,
        task_type=result["task_type"],
        target_column=target,
        best_model=result["best_model"],
        metrics=result["metrics"],
        feature_importance=result["feature_importance"],
        predictions=result["predictions"],
        model_comparison=result["model_comparison"],
        created_at=prediction.created_at,
    )


@router.post("/simulate", response_model=SimulateResponse)
def simulate(payload: SimulateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ds = _load_user_dataset(db, payload.dataset_id, current_user)
    pred = db.query(Prediction).filter(
        Prediction.id == payload.prediction_id, Prediction.dataset_id == ds.id
    ).first()
    if not pred:
        raise HTTPException(status_code=404, detail="Prediction not found")

    base = pred.predictions
    # Apply scenario adjustments to the base prediction
    new_pred = dict(base)
    base_value = base.get("next_prediction", 0)
    adjustment = sum(payload.scenario.values())
    new_value = base_value + adjustment
    new_pred["next_prediction"] = new_value
    new_pred["scenario_applied"] = payload.scenario

    revenue_diff = adjustment if "revenue" in str(pred.target_column).lower() or "sales" in str(pred.target_column).lower() else None
    profit_diff = adjustment if "profit" in str(pred.target_column).lower() else None
    risk_diff = -adjustment * 0.1 if adjustment > 0 else None

    explanation = what_if_analysis(payload.scenario, base, new_pred)

    return SimulateResponse(
        new_prediction=new_pred,
        revenue_difference=revenue_diff,
        profit_difference=profit_diff,
        risk_difference=risk_diff,
        gemini_explanation=explanation,
    )
