"""Google Gemini API integration service."""
import json
from typing import Any, Dict, List, Optional

from app.config import settings
from app.prompts import (
    SYSTEM_PROMPT,
    chat_prompt,
    dataset_summary_prompt,
    diagnosis_prompt,
    executive_summary_prompt,
    recommendations_prompt,
    root_cause_prompt,
    suggest_questions_prompt,
    what_if_prompt,
)
from app.utils.logging import get_logger

logger = get_logger("gemini")

try:
    import google.generativeai as genai
    _GEMINI_AVAILABLE = True
except ImportError:  # pragma: no cover
    genai = None
    _GEMINI_AVAILABLE = False


def _configure() -> Optional[Any]:
    if not _GEMINI_AVAILABLE:
        logger.warning("google-generativeai not installed; Gemini calls will return fallback text.")
        return None
    if not settings.gemini_api_key:
        logger.warning("GEMINI_API_KEY not set; Gemini calls will return fallback text.")
        return None
    genai.configure(api_key=settings.gemini_api_key)
    return genai.GenerativeModel(
        settings.gemini_model,
        system_instruction=SYSTEM_PROMPT,
    )


def _generate(prompt: str) -> str:
    """Call Gemini with a prompt, returning text. Falls back gracefully."""
    model = _configure()
    if model is None:
        return _fallback_response(prompt)
    try:
        resp = model.generate_content(prompt)
        text = resp.text if hasattr(resp, "text") else str(resp)
        logger.info("Gemini call succeeded (%d chars)", len(text))
        return text
    except Exception as e:  # noqa: BLE001
        logger.error("Gemini call failed: %s", e)
        return _fallback_response(prompt, error=str(e))


def _fallback_response(prompt: str, error: Optional[str] = None) -> str:
    note = f" (Gemini error: {error})" if error else " (Gemini not configured)"
    return f"I cannot determine this from the uploaded dataset.{note}"


def _try_parse_json(text: str) -> Any:
    """Attempt to extract JSON from a Gemini response."""
    try:
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1:
            return json.loads(text[start : end + 1])
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return json.loads(text[start : end + 1])
    except (json.JSONDecodeError, ValueError):
        pass
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def generate_dataset_summary(summary: Dict[str, Any]) -> str:
    return _generate(dataset_summary_prompt(summary))


def business_diagnosis(summary: Dict[str, Any], kpis: Dict[str, Any], issues: List[Dict[str, Any]]) -> str:
    return _generate(diagnosis_prompt(summary, kpis, issues))


def root_cause_analysis(
    summary: Dict[str, Any],
    kpis: Dict[str, Any],
    issues: List[Dict[str, Any]],
    feature_importance: Dict[str, Any],
) -> Dict[str, Any]:
    text = _generate(root_cause_prompt(summary, kpis, issues, feature_importance))
    parsed = _try_parse_json(text)
    return {
        "root_causes": parsed if isinstance(parsed, list) else [{"explanation": text}],
        "confidence": 0.75,
        "evidence": ["Derived from feature importance and KPI analysis"],
        "business_explanation": text,
    }


def generate_recommendations(
    summary: Dict[str, Any],
    kpis: Dict[str, Any],
    issues: List[Dict[str, Any]],
    predictions: Dict[str, Any],
) -> List[Dict[str, Any]]:
    text = _generate(recommendations_prompt(summary, kpis, issues, predictions))
    parsed = _try_parse_json(text)
    if isinstance(parsed, list):
        return parsed
    return [{"title": "Review analysis results", "priority": "Medium", "detail": text}]


def executive_summary(
    summary: Dict[str, Any],
    kpis: Dict[str, Any],
    issues: List[Dict[str, Any]],
    predictions: Dict[str, Any],
    recommendations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    text = _generate(
        executive_summary_prompt(summary, kpis, issues, predictions, recommendations)
    )
    return {
        "business_health": text,
        "major_risks": [i for i in issues if i.get("severity") == "Critical"][:3],
        "major_opportunities": [],
        "future_forecast": predictions.get("forecast", {}),
        "top_recommendations": recommendations[:3],
        "management_summary": text,
    }


def chat(question: str, context: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
    text = _generate(chat_prompt(question, context, history))
    return {
        "answer": text,
        "suggested_questions": [],
        "follow_up_questions": [],
    }


def what_if_analysis(
    scenario: Dict[str, float],
    base_prediction: Dict[str, Any],
    new_prediction: Dict[str, Any],
) -> str:
    return _generate(what_if_prompt(scenario, base_prediction, new_prediction))


def suggest_questions(summary: Dict[str, Any]) -> List[str]:
    text = _generate(suggest_questions_prompt(summary))
    lines = [l.strip().lstrip("0123456789.-) ") for l in text.splitlines() if l.strip()]
    return lines[:5]
