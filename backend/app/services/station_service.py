import uuid
from datetime import datetime, timezone, timedelta
from typing import List
from sqlalchemy.orm import Session, joinedload
from app.models.entities import (
    KitchenStation,
    OrderItem,
    Order,
    Table,
    MenuItem,
    OrderItemStatusEnum,
    utcnow
)
from app.core.exceptions import ResourceNotFoundException
from app.schemas.schemas import StationQueueItemOut


class StationService:

    @staticmethod
    def get_station_queue(
        db: Session,
        restaurant_id: uuid.UUID,
        branch_id: uuid.UUID,
        station_id: uuid.UUID
    ) -> List[StationQueueItemOut]:
        station = db.query(KitchenStation).filter(
            KitchenStation.id == station_id,
            KitchenStation.restaurant_id == restaurant_id,
            KitchenStation.branch_id == branch_id,
            KitchenStation.is_active == True
        ).first()

        if not station:
            raise ResourceNotFoundException("KitchenStation")

        now = utcnow()
        ten_minutes_ago = now - timedelta(minutes=10)

        # Retrieve items in PENDING, PREPARING, or recently READY
        items = db.query(OrderItem).options(
            joinedload(OrderItem.order).joinedload(Order.table),
            joinedload(OrderItem.menu_item)
        ).filter(
            OrderItem.restaurant_id == restaurant_id,
            OrderItem.branch_id == branch_id,
            OrderItem.station_id == station_id,
            (
                (OrderItem.status.in_([OrderItemStatusEnum.PENDING, OrderItemStatusEnum.PREPARING])) |
                ((OrderItem.status == OrderItemStatusEnum.READY) & (OrderItem.ready_at >= ten_minutes_ago))
            )
        ).order_by(OrderItem.created_at.asc()).all()

        results: List[StationQueueItemOut] = []
        for item in items:
            ref_time = item.preparing_at or item.created_at
            elapsed = (now - ref_time).total_seconds() / 60.0 if ref_time else 0.0
            is_delayed = (item.status in [OrderItemStatusEnum.PENDING, OrderItemStatusEnum.PREPARING]) and (
                elapsed > station.target_prep_time_minutes
            )

            table_num = item.order.table.table_number if item.order and item.order.table else "Unknown"
            order_num = item.order.order_number if item.order else 0

            results.append(
                StationQueueItemOut(
                    item_id=item.id,
                    order_id=item.order_id,
                    order_number=order_num,
                    table_number=table_num,
                    menu_item_name_fa=item.menu_item.name_fa if item.menu_item else "Unknown",
                    menu_item_name_en=item.menu_item.name_en if item.menu_item else None,
                    quantity=item.quantity,
                    status=item.status,
                    version=item.version,
                    modifiers=item.modifiers,
                    created_at=item.created_at,
                    preparing_at=item.preparing_at,
                    elapsed_minutes=round(elapsed, 1),
                    target_prep_time_minutes=station.target_prep_time_minutes,
                    is_delayed=is_delayed
                )
            )

        return results
