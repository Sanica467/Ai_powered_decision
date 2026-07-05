"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: Optional[str] = None
    role: Optional[str] = Field(default="analyst", pattern="^(analyst|admin|viewer)$")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class RefreshRequest(BaseModel):
    refresh_token: str


# ---------------------------------------------------------------------------
# Dataset / Upload
# ---------------------------------------------------------------------------
class UploadResponse(BaseModel):
    dataset_id: str
    filename: str
    file_type: str
    row_count: int
    column_count: int
    missing_values: int
    duplicates: int
    file_size_bytes: int
    preview: Dict[str, Any]
    columns: List[str]
    created_at: datetime


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
class AnalyzeRequest(BaseModel):
    dataset_id: str


class AnalysisResponse(BaseModel):
    analysis_id: str
    dataset_id: str
    summary: Dict[str, Any]
    kpis: Dict[str, Any]
    quality_score: float
    health_score: float
    feature_types: Dict[str, Any]
    target_suggestions: List[str]
    created_at: datetime


class DiagnosisRequest(BaseModel):
    dataset_id: str
    analysis_id: Optional[str] = None


class DiagnosisResponse(BaseModel):
    analysis_id: str
    dataset_id: str
    issues: List[Dict[str, Any]]
    created_at: datetime


class RootCauseRequest(BaseModel):
    dataset_id: str
    analysis_id: Optional[str] = None


class RootCauseResponse(BaseModel):
    analysis_id: str
    dataset_id: str
    root_causes: List[Dict[str, Any]]
    confidence: float
    evidence: List[str]
    business_explanation: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Prediction / AutoML
# ---------------------------------------------------------------------------
class PredictRequest(BaseModel):
    dataset_id: str
    target_column: Optional[str] = None
    horizon: int = Field(default=12, ge=1, le=60)


class PredictionResponse(BaseModel):
    prediction_id: str
    dataset_id: str
    task_type: str
    target_column: str
    best_model: str
    metrics: Dict[str, Any]
    feature_importance: Dict[str, Any]
    predictions: Dict[str, Any]
    model_comparison: List[Dict[str, Any]]
    created_at: datetime


# ---------------------------------------------------------------------------
# Recommendations / Summary
# ---------------------------------------------------------------------------
class RecommendationRequest(BaseModel):
    dataset_id: str
    analysis_id: Optional[str] = None
    prediction_id: Optional[str] = None


class RecommendationResponse(BaseModel):
    recommendation_id: str
    dataset_id: str
    recommendations: List[Dict[str, Any]]
    created_at: datetime


class SummaryRequest(BaseModel):
    dataset_id: str
    analysis_id: Optional[str] = None
    prediction_id: Optional[str] = None


class SummaryResponse(BaseModel):
    summary_id: str
    dataset_id: str
    executive_summary: Dict[str, Any]
    created_at: datetime


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    dataset_id: str
    question: str = Field(min_length=1, max_length=2000)
    history: List[Dict[str, str]] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    context_used: List[str]
    suggested_questions: List[str]
    follow_up_questions: List[str]
    created_at: datetime


# ---------------------------------------------------------------------------
# What-If Simulation
# ---------------------------------------------------------------------------
class SimulateRequest(BaseModel):
    dataset_id: str
    prediction_id: str
    scenario: Dict[str, float] = Field(default_factory=dict)


class SimulateResponse(BaseModel):
    new_prediction: Dict[str, Any]
    revenue_difference: Optional[float] = None
    profit_difference: Optional[float] = None
    risk_difference: Optional[float] = None
    gemini_explanation: str


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
class ReportRequest(BaseModel):
    dataset_id: str
    analysis_id: Optional[str] = None
    prediction_id: Optional[str] = None


class ReportResponse(BaseModel):
    report_id: str
    dataset_id: str
    download_url: str
    file_size_bytes: int
    created_at: datetime


# ---------------------------------------------------------------------------
# Generic
# ---------------------------------------------------------------------------
class MessageResponse(BaseModel):
    message: str
    detail: Optional[Any] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[Any] = None
