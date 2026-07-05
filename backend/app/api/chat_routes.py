"""Chat API route with RAG context retrieval."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Analysis, ChatMessage, Dataset, Prediction, User
from app.auth.dependencies import get_current_user
from app.schemas import ChatRequest, ChatResponse
from app.services.gemini_service import chat as gemini_chat, suggest_questions
from app.services.rag_service import build_index, get_index, retrieve_context
from app.utils.dataset import load_dataset
from app.utils.logging import get_logger

logger = get_logger("api.chat")

router = APIRouter(tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ds = db.query(Dataset).filter(Dataset.id == payload.dataset_id, Dataset.user_id == current_user.id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Build RAG index if not present
    if get_index(ds.id) is None:
        df = load_dataset(ds.stored_path)
        build_index(ds.id, df)

    # Retrieve relevant chunks
    chunks = retrieve_context(ds.id, payload.question, k=5)
    context = "\n---\n".join(chunks) if chunks else "No relevant data chunks retrieved."

    # Enrich context with analysis + ML results
    analysis = db.query(Analysis).filter(Analysis.dataset_id == ds.id).order_by(Analysis.created_at.desc()).first()
    prediction = db.query(Prediction).filter(Prediction.dataset_id == ds.id).order_by(Prediction.created_at.desc()).first()

    if analysis:
        context += f"\n\nDataset Summary: {analysis.summary}\nKPIs: {analysis.kpis}\nIssues: {analysis.diagnosis.get('issues', [])}"
    if prediction:
        context += f"\nML Results: model={prediction.best_model}, metrics={prediction.metrics}, predictions={prediction.predictions}"

    # Load conversation history from DB
    history_records = db.query(ChatMessage).filter(
        ChatMessage.dataset_id == ds.id, ChatMessage.user_id == current_user.id
    ).order_by(ChatMessage.created_at.desc()).limit(10).all()
    history = [{"role": r.role, "content": r.content} for r in reversed(history_records)]
    history.extend(payload.history)

    # Call Gemini
    result = gemini_chat(payload.question, context, history)

    # Persist messages
    db.add(ChatMessage(
        dataset_id=ds.id, user_id=current_user.id, role="user", content=payload.question,
    ))
    db.add(ChatMessage(
        dataset_id=ds.id, user_id=current_user.id, role="assistant", content=result["answer"],
        context={"retrieved_chunks": chunks[:3]},
    ))
    db.commit()

    # Generate suggested questions if none
    suggested = result.get("suggested_questions", [])
    if not suggested and analysis:
        suggested = suggest_questions(analysis.summary)

    return ChatResponse(
        answer=result["answer"],
        context_used=[c[:200] for c in chunks[:3]],
        suggested_questions=suggested,
        follow_up_questions=result.get("follow_up_questions", []),
        created_at=datetime.utcnow(),
    )
