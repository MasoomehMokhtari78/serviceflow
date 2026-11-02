from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import require_manager, verify_branch_scope
from app.models.entities import User
from app.services.metrics_service import MetricsService
from app.ai.analyst import AIAnalystService
from app.schemas.schemas import AIAnalystQuery, AIAnalystResponse

router = APIRouter(prefix="/ai", tags=["AI Operational Analyst"])


@router.post("/explain", response_model=AIAnalystResponse)
def explain_operations(
    query: AIAnalystQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """
    Read-only AI Operational Analyst for shift managers.
    Calculates deterministic metrics from real database orders, passes sanitized evidence
    to the LLM with defensive prompt fencing, and returns a grounded explanation.
    Under provider latency or failure, returns a deterministic Python rule-based fallback.
    """
    if query.branch_id:
        verify_branch_scope(user=current_user, branch_id=query.branch_id, db=db)

    metrics = MetricsService.get_operational_metrics(
        db=db,
        restaurant_id=current_user.restaurant_id,
        branch_id=query.branch_id,
        time_window_hours=24
    )

    return AIAnalystService.analyze(
        intent=query.intent,
        question=query.question,
        metrics=metrics
    )

