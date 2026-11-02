import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, verify_branch_scope
from app.core.exceptions import ResourceNotFoundException
from app.models.entities import User, Branch, KitchenStation, Table, Order, OrderStatusEnum
from app.schemas.schemas import BranchOut, KitchenStationOut, TableOut

router = APIRouter(prefix="/restaurants", tags=["Restaurants & Branches"])


@router.get("/branches", response_model=List[BranchOut])
def list_branches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all active branches for the authenticated restaurant tenant."""
    branches = db.query(Branch).filter(
        Branch.restaurant_id == current_user.restaurant_id,
        Branch.is_active == True
    ).order_by(Branch.name.asc()).all()
    return branches


@router.get("/branches/{branch_id}/stations", response_model=List[KitchenStationOut])
def list_branch_stations(
    branch_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List kitchen stations configured for a branch."""
    verify_branch_scope(current_user, branch_id, db=db)

    stations = db.query(KitchenStation).filter(
        KitchenStation.restaurant_id == current_user.restaurant_id,
        KitchenStation.branch_id == branch_id,
        KitchenStation.is_active == True
    ).order_by(KitchenStation.display_order.asc()).all()
    return stations


@router.get("/branches/{branch_id}/tables", response_model=List[TableOut])
def list_branch_tables(
    branch_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List tables in a branch with active order status."""
    verify_branch_scope(current_user, branch_id, db=db)


    tables = db.query(Table).filter(
        Table.restaurant_id == current_user.restaurant_id,
        Table.branch_id == branch_id,
        Table.is_active == True
    ).order_by(Table.table_number.asc()).all()

    # Find active orders on these tables
    active_orders = db.query(Order).filter(
        Order.restaurant_id == current_user.restaurant_id,
        Order.branch_id == branch_id,
        Order.status.in_([
            OrderStatusEnum.SUBMITTED,
            OrderStatusEnum.IN_PROGRESS,
            OrderStatusEnum.READY_FOR_SERVICE
        ])
    ).all()

    order_by_table = {o.table_id: o for o in active_orders}

    results = []
    for t in tables:
        active_order = order_by_table.get(t.id)
        results.append(
            TableOut(
                id=t.id,
                restaurant_id=t.restaurant_id,
                branch_id=t.branch_id,
                table_number=t.table_number,
                section=t.section,
                capacity=t.capacity,
                is_active=t.is_active,
                active_order_id=active_order.id if active_order else None,
                active_order_status=active_order.status if active_order else None
            )
        )

    return results
