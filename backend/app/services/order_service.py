"""
ServiceFlow Order Service
==========================

CONCURRENCY & HIERARCHICAL LOCKING STRATEGY (H1):
To eliminate deadlock risks across concurrent item updates, order serving, and cancellation:
1. Hierarchical Locking Order:
   - Order-level operations (serve_order, add_items_to_order, cancel_order) ALWAYS lock the parent Order row first:
     `SELECT ... FROM orders WHERE id = :id FOR UPDATE`
   - If item rows must also be locked (e.g. serve_order), they are fetched with `with_for_update()` ordered by id.
2. Item-level Operations (update_order_item_status):
   - Atomically locks only the specific OrderItem row:
     `SELECT ... FROM order_items WHERE id = :id FOR UPDATE`
   - Does NOT acquire a blocking lock on the parent Order.
   - Status synchronization to the parent Order is performed via single-statement conditional SQL updates:
     `UPDATE orders SET status = ... WHERE id = :id AND status NOT IN ('served', 'cancelled')`
   - This ensures item mutations never conflict with unrelated items on the same order, and never deadlock with serve_order.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import func, text
from sqlalchemy.orm import Session, joinedload
from app.models.entities import (
    User,
    Order,
    OrderItem,
    OrderStatusHistory,
    RoleEnum,
    OrderStatusEnum,
    OrderItemStatusEnum,
    Table,
    MenuItem,
    KitchenStation,
    Branch,
    utcnow,
    utcnow_date
)
from app.core.exceptions import (
    ResourceNotFoundException,
    ForbiddenException,
    ConflictException,
    InvalidStateTransitionException,
    UnreadyItemsException,
    AppException
)
from app.schemas.schemas import OrderCreate, OrderAddItemRequest


logger = logging.getLogger(__name__)


class OrderService:

    @staticmethod
    def get_order_by_id(
        db: Session,
        restaurant_id: uuid.UUID,
        branch_id: uuid.UUID,
        order_id: uuid.UUID
    ) -> Order:
        order = db.query(Order).options(
            joinedload(Order.items).joinedload(OrderItem.menu_item),
            joinedload(Order.items).joinedload(OrderItem.station),
            joinedload(Order.table),
            joinedload(Order.waiter),
            joinedload(Order.branch)
        ).filter(
            Order.id == order_id,
            Order.restaurant_id == restaurant_id,
            Order.branch_id == branch_id
        ).first()

        if not order:
            raise ResourceNotFoundException("Order")
        return order

    @staticmethod
    def create_order(
        db: Session,
        restaurant_id: uuid.UUID,
        waiter_id: uuid.UUID,
        data: OrderCreate
    ) -> Order:
        # 1. Verify branch exists and is active for this tenant
        branch = db.query(Branch).filter(
            Branch.id == data.branch_id,
            Branch.restaurant_id == restaurant_id,
            Branch.is_active == True
        ).first()
        if not branch:
            raise ResourceNotFoundException("Branch")

        # 2. Verify table belongs to branch and tenant
        table = db.query(Table).filter(
            Table.id == data.table_id,
            Table.restaurant_id == restaurant_id,
            Table.branch_id == data.branch_id,
            Table.is_active == True
        ).first()
        if not table:
            raise ResourceNotFoundException("Table")

        # 3. Fetch branch kitchen stations mapped by station_type
        stations = db.query(KitchenStation).filter(
            KitchenStation.restaurant_id == restaurant_id,
            KitchenStation.branch_id == data.branch_id,
            KitchenStation.is_active == True
        ).all()
        if not stations:
            raise AppException(400, "Branch has no active kitchen stations configured.")
        
        station_by_type = {s.station_type: s for s in stations}
        default_fallback_station = stations[0]

        # 4. Generate daily order number for branch atomically via PostgreSQL upsert
        today_date = utcnow_date()
        counter_stmt = text("""
            INSERT INTO branch_daily_counters (id, restaurant_id, branch_id, counter_date, last_order_number, updated_at)
            VALUES (:id, :r_id, :b_id, :counter_date, 1, NOW())
            ON CONFLICT (restaurant_id, branch_id, counter_date)
            DO UPDATE SET 
                last_order_number = branch_daily_counters.last_order_number + 1,
                updated_at = NOW()
            RETURNING last_order_number;
        """)
        order_number = db.execute(counter_stmt, {
            "id": uuid.uuid4(),
            "r_id": restaurant_id,
            "b_id": data.branch_id,
            "counter_date": today_date
        }).scalar_one()

        # 5. Create Order entity
        order = Order(
            restaurant_id=restaurant_id,
            branch_id=data.branch_id,
            table_id=data.table_id,
            waiter_id=waiter_id,
            order_date=today_date,
            order_number=order_number,
            status=OrderStatusEnum.SUBMITTED,
            version=1,
            notes=data.notes,
            total_price_toman=0
        )
        db.add(order)
        db.flush()  # allocate order.id

        total_price = 0
        # 6. Resolve and create each OrderItem
        for item_in in data.items:
            menu_item = db.query(MenuItem).filter(
                MenuItem.id == item_in.menu_item_id,
                MenuItem.restaurant_id == restaurant_id,
                MenuItem.is_available == True
            ).first()
            if not menu_item:
                raise ResourceNotFoundException(f"Menu item {item_in.menu_item_id}")

            target_station = station_by_type.get(menu_item.default_station_type, default_fallback_station)
            item_total = menu_item.price_toman * item_in.quantity
            total_price += item_total

            order_item = OrderItem(
                restaurant_id=restaurant_id,
                branch_id=data.branch_id,
                order_id=order.id,
                menu_item_id=menu_item.id,
                station_id=target_station.id,
                quantity=item_in.quantity,
                unit_price_toman=menu_item.price_toman,
                status=OrderItemStatusEnum.PENDING,
                version=1,
                modifiers=item_in.modifiers,
                created_at=utcnow()
            )
            db.add(order_item)

        order.total_price_toman = total_price

        # 7. Audit log
        history = OrderStatusHistory(
            restaurant_id=restaurant_id,
            branch_id=data.branch_id,
            order_id=order.id,
            from_status=None,
            to_status=OrderStatusEnum.SUBMITTED.value,
            changed_by_user_id=waiter_id,
            notes="Order created"
        )
        db.add(history)
        db.commit()

        logger.info(
            "Order created: order_id=%s, order_number=%s, restaurant_id=%s, branch_id=%s, items_count=%s, total_price=%s",
            order.id, order.order_number, restaurant_id, data.branch_id, len(data.items), total_price
        )

        return OrderService.get_order_by_id(db, restaurant_id, data.branch_id, order.id)

    @staticmethod
    def add_items_to_order(
        db: Session,
        restaurant_id: uuid.UUID,
        branch_id: uuid.UUID,
        order_id: uuid.UUID,
        user_id: uuid.UUID,
        data: OrderAddItemRequest
    ) -> Order:
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.restaurant_id == restaurant_id,
            Order.branch_id == branch_id
        ).with_for_update().first()

        if not order:
            raise ResourceNotFoundException("Order")

        if order.status in [OrderStatusEnum.SERVED, OrderStatusEnum.CANCELLED]:
            raise AppException(400, f"Cannot add items to an order with status '{order.status.value}'.")

        # Concurrency check
        if order.version != data.expected_order_version:
            logger.warning(
                "Version conflict on add_items: order_id=%s, expected_version=%s, current_version=%s",
                order_id, data.expected_order_version, order.version
            )
            raise ConflictException(
                detail=f"Order version conflict: Expected {data.expected_order_version}, found {order.version}. Another staff member updated this order.",
                current_version=order.version
            )

        # Stations map
        stations = db.query(KitchenStation).filter(
            KitchenStation.restaurant_id == restaurant_id,
            KitchenStation.branch_id == branch_id,
            KitchenStation.is_active == True
        ).all()
        station_by_type = {s.station_type: s for s in stations}
        default_fallback_station = stations[0] if stations else None

        additional_price = 0
        for item_in in data.items:
            menu_item = db.query(MenuItem).filter(
                MenuItem.id == item_in.menu_item_id,
                MenuItem.restaurant_id == restaurant_id,
                MenuItem.is_available == True
            ).first()
            if not menu_item:
                raise ResourceNotFoundException(f"Menu item {item_in.menu_item_id}")

            target_station = station_by_type.get(menu_item.default_station_type, default_fallback_station)
            additional_price += menu_item.price_toman * item_in.quantity

            new_item = OrderItem(
                restaurant_id=restaurant_id,
                branch_id=branch_id,
                order_id=order.id,
                menu_item_id=menu_item.id,
                station_id=target_station.id,
                quantity=item_in.quantity,
                unit_price_toman=menu_item.price_toman,
                status=OrderItemStatusEnum.PENDING,
                version=1,
                modifiers=item_in.modifiers,
                created_at=utcnow()
            )
            db.add(new_item)

        order.total_price_toman += additional_price
        order.version += 1
        order.updated_at = utcnow()
        # If order was ready for service, new pending items pull it back to in_progress
        if order.status == OrderStatusEnum.READY_FOR_SERVICE:
            order.status = OrderStatusEnum.IN_PROGRESS

        history = OrderStatusHistory(
            restaurant_id=restaurant_id,
            branch_id=branch_id,
            order_id=order.id,
            from_status=order.status.value,
            to_status="ITEMS_ADDED",
            changed_by_user_id=user_id,
            notes=f"Added {len(data.items)} item(s) to order"
        )
        db.add(history)
        db.commit()

        logger.info(
            "Order items added: order_id=%s, count=%s, new_version=%s, new_total=%s",
            order.id, len(data.items), order.version, order.total_price_toman
        )

        return OrderService.get_order_by_id(db, restaurant_id, branch_id, order.id)

    @staticmethod
    def update_order_item_status(
        db: Session,
        restaurant_id: uuid.UUID,
        order_item_id: uuid.UUID,
        user: User,
        target_status: OrderItemStatusEnum,
        expected_item_version: int,
        notes: Optional[str] = None
    ) -> OrderItem:
        # Atomic lock on the specific OrderItem row
        item = db.query(OrderItem).filter(
            OrderItem.id == order_item_id,
            OrderItem.restaurant_id == restaurant_id
        ).with_for_update().first()

        if not item:
            raise ResourceNotFoundException("OrderItem")

        # C2: Enforce branch and station authorization
        if user.role == RoleEnum.WAITER:
            raise ForbiddenException("Waiters are not permitted to update kitchen item statuses.")
        elif user.role == RoleEnum.KITCHEN:
            if not user.branch_id or item.branch_id != user.branch_id:
                raise ResourceNotFoundException("OrderItem")
            if not user.station_id:
                raise ForbiddenException("Kitchen staff has no station assignment.")
            if item.station_id != user.station_id:
                raise ForbiddenException("You are not authorized to update items for this kitchen station.")
        elif user.role == RoleEnum.MANAGER:
            # Managers can update any item within their tenant branches
            pass

        # Item-level optimistic concurrency check
        if item.version != expected_item_version:
            logger.warning(
                "Version conflict on item: item_id=%s, expected_version=%s, current_version=%s",
                order_item_id, expected_item_version, item.version
            )
            raise ConflictException(
                detail=f"Order item conflict: Expected version {expected_item_version}, found {item.version}. Item was updated by another station worker.",
                current_version=item.version
            )

        # State machine transition rules:
        # Kitchen workers mark PENDING -> PREPARING -> READY.
        # SERVED is exclusively managed when the entire order is served by floor staff.
        valid_transitions = {
            OrderItemStatusEnum.PENDING: [OrderItemStatusEnum.PREPARING, OrderItemStatusEnum.CANCELLED],
            OrderItemStatusEnum.PREPARING: [OrderItemStatusEnum.READY, OrderItemStatusEnum.CANCELLED],
            OrderItemStatusEnum.READY: [OrderItemStatusEnum.CANCELLED],
            OrderItemStatusEnum.SERVED: [],
            OrderItemStatusEnum.CANCELLED: []
        }

        if target_status not in valid_transitions.get(item.status, []):
            logger.warning(
                "Invalid item transition rejected: item_id=%s, current_status=%s, target_status=%s",
                order_item_id, item.status.value, target_status.value
            )
            raise InvalidStateTransitionException(
                detail=f"Invalid transition from '{item.status.value}' to '{target_status.value}'.",
                current_status=item.status.value,
                target_status=target_status.value
            )

        prev_status = item.status
        item.status = target_status
        item.version += 1

        now = utcnow()
        if target_status == OrderItemStatusEnum.PREPARING:
            item.preparing_at = now
        elif target_status == OrderItemStatusEnum.READY:
            item.ready_at = now
        elif target_status == OrderItemStatusEnum.SERVED:
            item.served_at = now

        # H1: Safe atomic parent order status transitions without bumping Order.version
        # and preventing regressions on SERVED or CANCELLED orders
        if target_status == OrderItemStatusEnum.PREPARING:
            db.query(Order).filter(
                Order.id == item.order_id,
                Order.status == OrderStatusEnum.SUBMITTED
            ).update({
                Order.status: OrderStatusEnum.IN_PROGRESS,
                Order.updated_at: now
            }, synchronize_session=False)

        # Check if all non-cancelled items are ready
        all_items = db.query(OrderItem).filter(OrderItem.order_id == item.order_id).all()
        active_items = [i for i in all_items if i.id != item.id and i.status != OrderItemStatusEnum.CANCELLED]
        if target_status != OrderItemStatusEnum.CANCELLED:
            active_items.append(item)

        if active_items and all(i.status in [OrderItemStatusEnum.READY, OrderItemStatusEnum.SERVED] for i in active_items):
            # Atomic update: ONLY if order is not already SERVED or CANCELLED!
            db.query(Order).filter(
                Order.id == item.order_id,
                Order.status.notin_([OrderStatusEnum.SERVED, OrderStatusEnum.CANCELLED])
            ).update({
                Order.status: OrderStatusEnum.READY_FOR_SERVICE,
                Order.updated_at: now
            }, synchronize_session=False)

        # Audit history
        history = OrderStatusHistory(
            restaurant_id=restaurant_id,
            branch_id=item.branch_id,
            order_id=item.order_id,
            order_item_id=item.id,
            from_status=prev_status.value,
            to_status=target_status.value,
            changed_by_user_id=user.id,
            notes=notes or f"Item status transitioned to {target_status.value}"
        )
        db.add(history)
        db.commit()
        db.refresh(item)

        logger.info(
            "OrderItem status updated: item_id=%s, station_id=%s, from_status=%s, to_status=%s, new_version=%s",
            item.id, item.station_id, prev_status.value, target_status.value, item.version
        )
        return item

    @staticmethod
    def serve_order(
        db: Session,
        restaurant_id: uuid.UUID,
        branch_id: uuid.UUID,
        order_id: uuid.UUID,
        user_id: uuid.UUID,
        expected_order_version: int,
        notes: Optional[str] = None
    ) -> Order:
        # Hierarchical locking: lock Order first
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.restaurant_id == restaurant_id,
            Order.branch_id == branch_id
        ).with_for_update().first()

        if not order:
            raise ResourceNotFoundException("Order")

        if order.status == OrderStatusEnum.SERVED:
            return order  # idempotent if already served

        if order.status == OrderStatusEnum.CANCELLED:
            raise AppException(400, "Cannot serve a cancelled order.")

        # Concurrency version check
        if order.version != expected_order_version:
            logger.warning(
                "Version conflict on serve_order: order_id=%s, expected_version=%s, current_version=%s",
                order_id, expected_order_version, order.version
            )
            raise ConflictException(
                detail=f"Order version conflict: Expected {expected_order_version}, found {order.version}. Order was modified by another user.",
                current_version=order.version
            )

        # Invariant check: Lock all items of this order before checking status
        items = db.query(OrderItem).options(
            joinedload(OrderItem.menu_item),
            joinedload(OrderItem.station)
        ).filter(OrderItem.order_id == order.id).with_for_update(of=OrderItem).all()


        unready_items = []
        for i in items:
            if i.status in [OrderItemStatusEnum.PENDING, OrderItemStatusEnum.PREPARING]:
                unready_items.append({
                    "item_id": str(i.id),
                    "dish_name": i.menu_item.name_fa if i.menu_item else "Unknown",
                    "station": i.station.name if i.station else "Unknown",
                    "status": i.status.value
                })

        if unready_items:
            logger.warning(
                "Serve order rejected due to unready items: order_id=%s, unready_count=%s",
                order_id, len(unready_items)
            )
            raise UnreadyItemsException(
                detail=f"Cannot serve order: {len(unready_items)} item(s) are not ready yet.",
                unready_items=unready_items
            )

        now = utcnow()
        # Mark ready items as SERVED
        for i in items:
            if i.status == OrderItemStatusEnum.READY:
                i.status = OrderItemStatusEnum.SERVED
                i.served_at = now
                i.version += 1

        prev_status = order.status
        order.status = OrderStatusEnum.SERVED
        order.served_at = now
        order.version += 1
        order.updated_at = now

        history = OrderStatusHistory(
            restaurant_id=restaurant_id,
            branch_id=branch_id,
            order_id=order.id,
            from_status=prev_status.value,
            to_status=OrderStatusEnum.SERVED.value,
            changed_by_user_id=user_id,
            notes=notes or "Order successfully served to table"
        )
        db.add(history)
        db.commit()

        logger.info(
            "Order served: order_id=%s, branch_id=%s, served_by=%s, new_version=%s",
            order.id, branch_id, user_id, order.version
        )

        return OrderService.get_order_by_id(db, restaurant_id, branch_id, order.id)

    @staticmethod
    def cancel_order(
        db: Session,
        restaurant_id: uuid.UUID,
        branch_id: uuid.UUID,
        order_id: uuid.UUID,
        user_id: uuid.UUID,
        expected_order_version: int,
        reason: Optional[str] = None
    ) -> Order:
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.restaurant_id == restaurant_id,
            Order.branch_id == branch_id
        ).with_for_update().first()

        if not order:
            raise ResourceNotFoundException("Order")

        if order.status == OrderStatusEnum.CANCELLED:
            return order

        if order.version != expected_order_version:
            logger.warning(
                "Version conflict on cancel_order: order_id=%s, expected_version=%s, current_version=%s",
                order_id, expected_order_version, order.version
            )
            raise ConflictException(
                detail=f"Order version conflict: Expected {expected_order_version}, found {order.version}.",
                current_version=order.version
            )

        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        for i in items:
            if i.status not in [OrderItemStatusEnum.SERVED, OrderItemStatusEnum.CANCELLED]:
                i.status = OrderItemStatusEnum.CANCELLED
                i.version += 1

        prev_status = order.status
        order.status = OrderStatusEnum.CANCELLED
        order.version += 1
        order.updated_at = utcnow()

        history = OrderStatusHistory(
            restaurant_id=restaurant_id,
            branch_id=branch_id,
            order_id=order.id,
            from_status=prev_status.value,
            to_status=OrderStatusEnum.CANCELLED.value,
            changed_by_user_id=user_id,
            notes=reason or "Order cancelled by staff"
        )
        db.add(history)
        db.commit()

        logger.info(
            "Order cancelled: order_id=%s, branch_id=%s, cancelled_by=%s, reason=%s",
            order.id, branch_id, user_id, reason
        )

        return OrderService.get_order_by_id(db, restaurant_id, branch_id, order.id)

