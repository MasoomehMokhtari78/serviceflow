import uuid
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, verify_branch_scope
from app.models.entities import User
from app.services.station_service import StationService
from app.schemas.schemas import StationQueueItemOut

router = APIRouter(prefix="/stations", tags=["Kitchen Stations"])


@router.get("/{station_id}/queue", response_model=List[StationQueueItemOut])
def get_station_queue(
    station_id: uuid.UUID,
    branch_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get live kitchen display system (KDS) queue for a specific station in a branch.
    Includes item preparation countdown and SLA delay status.
    Kitchen staff are restricted to their authorized branch and assigned station.
    Managers can view any station in their authorized branches.
    Waiters are forbidden from direct station queue access.
    """
    from app.core.deps import verify_kitchen_station_scope
    verify_branch_scope(current_user, branch_id, db=db)
    verify_kitchen_station_scope(current_user, branch_id, station_id)

    return StationService.get_station_queue(
        db=db,
        restaurant_id=current_user.restaurant_id,
        branch_id=branch_id,
        station_id=station_id
    )
