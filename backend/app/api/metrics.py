import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import require_manager
from app.models.entities import User
from app.services.metrics_service import MetricsService
from app.schemas.schemas import OperationalMetricsOut

router = APIRouter(prefix="/metrics", tags=["Operational Metrics"])


@router.get("/operational", response_model=OperationalMetricsOut)
def get_operational_metrics(
    branch_id: Optional[uuid.UUID] = Query(None),
    time_window_hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """
    Manager endpoint: Calculate deterministic operational metrics for shift intelligence.
    Computes lead times, station turnaround durations, delay percentages against SLAs,
    top delayed menu items, and cross-branch comparative analytics.
    """
    return MetricsService.get_operational_metrics(
        db=db,
        restaurant_id=current_user.restaurant_id,
        branch_id=branch_id,
        time_window_hours=time_window_hours
    )
