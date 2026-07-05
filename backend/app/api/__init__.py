"""API package - aggregates all route routers."""
from fastapi import APIRouter

from app.api.auth_routes import router as auth_router
from app.api.analysis_routes import router as analysis_router
from app.api.chat_routes import router as chat_router
from app.api.prediction_routes import router as prediction_router
from app.api.recommendation_routes import router as recommendation_router
from app.api.report_routes import router as report_router
from app.api.upload_routes import router as upload_router


def get_api_router() -> APIRouter:
    """Return the aggregated API router with all sub-routers mounted."""
    api = APIRouter()
    api.include_router(auth_router)
    api.include_router(upload_router)
    api.include_router(analysis_router)
    api.include_router(prediction_router)
    api.include_router(recommendation_router)
    api.include_router(chat_router)
    api.include_router(report_router)
    return api
