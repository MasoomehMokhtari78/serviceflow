import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.core.deps import (
    get_current_user,
    require_waiter_or_manager,
    verify_branch_scope
)
from app.core.exceptions import ForbiddenException

from app.models.entities import (
    User,
    RoleEnum,
    Order,
    OrderItem,
    OrderStatusEnum,
    OrderItemStatusEnum,
    utcnow
)

from app.services.order_service import OrderService
from app.schemas.schemas import (
    OrderCreate,
    OrderAddItemRequest,
    OrderServeRequest,
    OrderCancelRequest,
    OrderOut,
    OrderItemOut
)

router = APIRouter(prefix="/orders", tags=["Orders"])


def format_order_item_out(item: OrderItem) -> OrderItemOut:
    now = utcnow()
    ref_time = item.preparing_at or item.created_at
    elapsed = (now - ref_time).total_seconds() / 60.0 if ref_time else 0.0

    target_prep = item.station.target_prep_time_minutes if item.station else 5
    is_delayed = (
        item.status in [OrderItemStatusEnum.PENDING, OrderItemStatusEnum.PREPARING]
        and elapsed > target_prep
    )

    return OrderItemOut(
        id=item.id,
        restaurant_id=item.restaurant_id,
        branch_id=item.branch_id,
        order_id=item.order_id,
        menu_item_id=item.menu_item_id,
        station_id=item.station_id,
        station_name=item.station.name if item.station else None,
        item_name_fa=item.menu_item.name_fa if item.menu_item else "Unknown",
        item_name_en=item.menu_item.name_en if item.menu_item else None,
        quantity=item.quantity,
        unit_price_toman=item.unit_price_toman,
        status=item.status,
        version=item.version,
        modifiers=item.modifiers,
        created_at=item.created_at,
        preparing_at=item.preparing_at,
        ready_at=item.ready_at,
        served_at=item.served_at,
        elapsed_minutes=round(elapsed, 1),
        is_delayed=is_delayed
    )


def format_order_out(order: Order) -> OrderOut:
    formatted_items = [format_order_item_out(i) for i in order.items]
    active_items = [i for i in order.items if i.status != OrderItemStatusEnum.CANCELLED]
    ready_count = len([i for i in active_items if i.status in [OrderItemStatusEnum.READY, OrderItemStatusEnum.SERVED]])
    total_count = len(active_items)

    is_ready = total_count > 0 and ready_count == total_count

    return OrderOut(
        id=order.id,
        restaurant_id=order.restaurant_id,
        branch_id=order.branch_id,
        branch_name=order.branch.name if order.branch else None,
        table_id=order.table_id,
        table_number=order.table.table_number if order.table else None,
        table_section=order.table.section if order.table else None,
        waiter_id=order.waiter_id,
        waiter_name=order.waiter.full_name if order.waiter else None,
        order_number=order.order_number,
        status=order.status,
        version=order.version,
        notes=order.notes,
        total_price_toman=order.total_price_toman,
        created_at=order.created_at,
        updated_at=order.updated_at,
        served_at=order.served_at,
        items=formatted_items,
        ready_items_count=ready_count,
        total_items_count=total_count,
        is_ready_for_service=is_ready
    )


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_waiter_or_manager)
):
    """Create a new table order with atomic station item routing."""
    verify_branch_scope(current_user, data.branch_id)
    order = OrderService.create_order(db, current_user.restaurant_id, current_user.id, data)
    return format_order_out(order)


@router.get("", response_model=List[OrderOut])
def list_orders(
    branch_id: Optional[uuid.UUID] = Query(None),
    status: Optional[OrderStatusEnum] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List orders filtered by branch and status."""
    query = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.menu_item),
        joinedload(Order.items).joinedload(OrderItem.station),
        joinedload(Order.table),
        joinedload(Order.waiter),
        joinedload(Order.branch)
    ).filter(
        Order.restaurant_id == current_user.restaurant_id
    )

    if current_user.role != RoleEnum.MANAGER:
        if not current_user.branch_id:
            raise ForbiddenException("User has no branch assignment.")
        if branch_id and branch_id != current_user.branch_id:
            raise ForbiddenException("Access denied: You are not authorized for this branch.")
        query = query.filter(Order.branch_id == current_user.branch_id)
    else:
        if branch_id:
            verify_branch_scope(current_user, branch_id, db=db)
            query = query.filter(Order.branch_id == branch_id)
        elif current_user.branch_id:
            query = query.filter(Order.branch_id == current_user.branch_id)

    if status:
        query = query.filter(Order.status == status)
    elif active_only:
        query = query.filter(Order.status.in_([
            OrderStatusEnum.SUBMITTED,
            OrderStatusEnum.IN_PROGRESS,
            OrderStatusEnum.READY_FOR_SERVICE
        ]))

    orders = query.order_by(Order.created_at.desc()).all()
    return [format_order_out(o) for o in orders]


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: uuid.UUID,
    branch_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get single order details.
    Enforces that non-managers can only access orders within their authorized branch,
    regardless of whether the client supplied branch_id.
    Managers are restricted to branches belonging to their restaurant tenant.
    """
    query = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.menu_item),
        joinedload(Order.items).joinedload(OrderItem.station),
        joinedload(Order.table),
        joinedload(Order.waiter),
        joinedload(Order.branch)
    ).filter(
        Order.id == order_id,
        Order.restaurant_id == current_user.restaurant_id
    )

    if current_user.role != RoleEnum.MANAGER:
        if not current_user.branch_id:
            raise ForbiddenException("User has no branch assignment.")
        if branch_id and branch_id != current_user.branch_id:
            raise ForbiddenException("Access denied: You are not authorized for this branch.")
        query = query.filter(Order.branch_id == current_user.branch_id)
    else:
        if branch_id:
            verify_branch_scope(current_user, branch_id, db=db)
            query = query.filter(Order.branch_id == branch_id)

    order = query.first()
    if not order:
        from app.core.exceptions import ResourceNotFoundException
        raise ResourceNotFoundException("Order")

    return format_order_out(order)


@router.post("/{order_id}/items", response_model=OrderOut)
def add_items_to_order(
    order_id: uuid.UUID,
    data: OrderAddItemRequest,
    branch_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_waiter_or_manager)
):
    """Append additional items to an active order with optimistic version check."""
    verify_branch_scope(current_user, branch_id)
    order = OrderService.add_items_to_order(
        db=db,
        restaurant_id=current_user.restaurant_id,
        branch_id=branch_id,
        order_id=order_id,
        user_id=current_user.id,
        data=data
    )
    return format_order_out(order)


@router.post("/{order_id}/serve", response_model=OrderOut)
def serve_order(
    order_id: uuid.UUID,
    data: OrderServeRequest,
    branch_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_waiter_or_manager)
):
    """Mark an order served with invariant validation (all items must be READY or CANCELLED)."""
    verify_branch_scope(current_user, branch_id)
    order = OrderService.serve_order(
        db=db,
        restaurant_id=current_user.restaurant_id,
        branch_id=branch_id,
        order_id=order_id,
        user_id=current_user.id,
        expected_order_version=data.expected_order_version,
        notes=data.notes
    )
    return format_order_out(order)


@router.post("/{order_id}/cancel", response_model=OrderOut)
def cancel_order(
    order_id: uuid.UUID,
    data: OrderCancelRequest,
    branch_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_waiter_or_manager)
):
    """Cancel an entire order with optimistic version check."""
    verify_branch_scope(current_user, branch_id)
    order = OrderService.cancel_order(
        db=db,
        restaurant_id=current_user.restaurant_id,
        branch_id=branch_id,
        order_id=order_id,
        user_id=current_user.id,
        expected_order_version=data.expected_order_version,
        reason=data.reason
    )
    return format_order_out(order)
