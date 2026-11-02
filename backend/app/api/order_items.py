import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_kitchen_or_manager
from app.models.entities import User
from app.services.order_service import OrderService
from app.schemas.schemas import OrderItemStatusUpdate, OrderItemOut
from app.api.orders import format_order_item_out

router = APIRouter(prefix="/order-items", tags=["Order Items"])


@router.patch("/{item_id}/status", response_model=OrderItemOut)
def update_item_status(
    item_id: uuid.UUID,
    data: OrderItemStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_kitchen_or_manager)
):
    """
    Update item preparation state (e.g., PENDING -> PREPARING -> READY).
    Increments OrderItem.version independently without locking or incrementing the parent Order.version.
    Returns 409 Conflict if item version does not match expected_item_version.
    """
    updated_item = OrderService.update_order_item_status(
        db=db,
        restaurant_id=current_user.restaurant_id,
        order_item_id=item_id,
        user=current_user,
        target_status=data.target_status,
        expected_item_version=data.expected_item_version,
        notes=data.notes
    )
    return format_order_item_out(updated_item)
