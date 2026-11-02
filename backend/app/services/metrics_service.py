import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.entities import (
    Order,
    OrderItem,
    KitchenStation,
    MenuItem,
    Branch,
    OrderStatusEnum,
    OrderItemStatusEnum,
    utcnow
)
from app.schemas.schemas import (
    OperationalMetricsOut,
    StationPerformanceMetric,
    DelayedDishSummary,
    BranchOperationalSummary
)


class MetricsService:

    @staticmethod
    def get_operational_metrics(
        db: Session,
        restaurant_id: uuid.UUID,
        branch_id: Optional[uuid.UUID] = None,
        time_window_hours: int = 24
    ) -> OperationalMetricsOut:
        now = utcnow()
        window_start = now - timedelta(hours=time_window_hours)

        # 1. Base order query for the time window
        order_query = db.query(Order).filter(
            Order.restaurant_id == restaurant_id,
            Order.created_at >= window_start
        )
        if branch_id:
            order_query = order_query.filter(Order.branch_id == branch_id)

        orders = order_query.all()
        total_orders = len(orders)
        completed_orders = len([o for o in orders if o.status == OrderStatusEnum.SERVED])
        active_orders = len([o for o in orders if o.status in [OrderStatusEnum.SUBMITTED, OrderStatusEnum.IN_PROGRESS, OrderStatusEnum.READY_FOR_SERVICE]])

        # Lead time for served orders
        lead_times = []
        for o in orders:
            if o.status == OrderStatusEnum.SERVED and o.served_at and o.created_at:
                lead_times.append((o.served_at - o.created_at).total_seconds() / 60.0)
        avg_lead_time = round(sum(lead_times) / len(lead_times), 1) if lead_times else 0.0

        # 2. Station-level metrics
        station_query = db.query(KitchenStation).filter(
            KitchenStation.restaurant_id == restaurant_id,
            KitchenStation.is_active == True
        )
        if branch_id:
            station_query = station_query.filter(KitchenStation.branch_id == branch_id)
        stations = station_query.order_by(KitchenStation.display_order.asc()).all()

        station_metrics: List[StationPerformanceMetric] = []
        for s in stations:
            items_query = db.query(OrderItem).filter(
                OrderItem.restaurant_id == restaurant_id,
                OrderItem.station_id == s.id,
                OrderItem.created_at >= window_start
            )
            items = items_query.all()
            total_items = len(items)
            completed_items = len([i for i in items if i.status in [OrderItemStatusEnum.READY, OrderItemStatusEnum.SERVED]])
            
            prep_durations = []
            delayed_count = 0
            for i in items:
                # Calculate turnaround
                if i.ready_at and i.created_at:
                    dur = (i.ready_at - i.created_at).total_seconds() / 60.0
                    prep_durations.append(dur)
                    if dur > s.target_prep_time_minutes:
                        delayed_count += 1
                elif i.status in [OrderItemStatusEnum.PENDING, OrderItemStatusEnum.PREPARING]:
                    ref = i.preparing_at or i.created_at
                    dur = (now - ref).total_seconds() / 60.0
                    if dur > s.target_prep_time_minutes:
                        delayed_count += 1

            avg_dur = round(sum(prep_durations) / len(prep_durations), 1) if prep_durations else 0.0
            delay_pct = round((delayed_count / total_items) * 100, 1) if total_items > 0 else 0.0

            station_metrics.append(
                StationPerformanceMetric(
                    station_id=s.id,
                    station_name=s.name,
                    station_type=s.station_type,
                    target_prep_time_minutes=s.target_prep_time_minutes,
                    total_items_count=total_items,
                    completed_items_count=completed_items,
                    delayed_items_count=delayed_count,
                    delay_rate_percentage=delay_pct,
                    avg_turnaround_minutes=avg_dur
                )
            )

        # 3. Top Delayed Dishes
        # Find which menu items took longer than their station's SLA
        delayed_dish_counts = {}
        total_dish_counts = {}
        dish_info = {}

        all_items = db.query(OrderItem, MenuItem, KitchenStation).join(
            MenuItem, OrderItem.menu_item_id == MenuItem.id
        ).join(
            KitchenStation, OrderItem.station_id == KitchenStation.id
        ).filter(
            OrderItem.restaurant_id == restaurant_id,
            OrderItem.created_at >= window_start
        )
        if branch_id:
            all_items = all_items.filter(OrderItem.branch_id == branch_id)

        for item, menu_item, station in all_items.all():
            m_id = menu_item.id
            total_dish_counts[m_id] = total_dish_counts.get(m_id, 0) + item.quantity
            dish_info[m_id] = (menu_item.name_fa, station.station_type)

            is_delayed = False
            if item.ready_at and item.created_at:
                dur = (item.ready_at - item.created_at).total_seconds() / 60.0
                if dur > station.target_prep_time_minutes:
                    is_delayed = True
            elif item.status in [OrderItemStatusEnum.PENDING, OrderItemStatusEnum.PREPARING]:
                ref = item.preparing_at or item.created_at
                dur = (now - ref).total_seconds() / 60.0
                if dur > station.target_prep_time_minutes:
                    is_delayed = True

            if is_delayed:
                delayed_dish_counts[m_id] = delayed_dish_counts.get(m_id, 0) + item.quantity

        top_delayed: List[DelayedDishSummary] = []
        for m_id, delayed_count in sorted(delayed_dish_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            name_fa, station_type = dish_info[m_id]
            top_delayed.append(
                DelayedDishSummary(
                    menu_item_id=m_id,
                    name_fa=name_fa,
                    station_type=station_type,
                    delayed_count=delayed_count,
                    total_ordered_count=total_dish_counts.get(m_id, 0)
                )
            )

        # 4. Multi-Branch Operational Comparison
        branch_summaries: List[BranchOperationalSummary] = []
        all_branches = db.query(Branch).filter(
            Branch.restaurant_id == restaurant_id,
            Branch.is_active == True
        ).all()

        for b in all_branches:
            b_orders = [o for o in orders if o.branch_id == b.id]
            b_total = len(b_orders)
            b_completed = len([o for o in b_orders if o.status == OrderStatusEnum.SERVED])
            b_active = len([o for o in b_orders if o.status in [OrderStatusEnum.SUBMITTED, OrderStatusEnum.IN_PROGRESS, OrderStatusEnum.READY_FOR_SERVICE]])
            
            b_leads = []
            b_delayed_count = 0
            for o in b_orders:
                if o.status == OrderStatusEnum.SERVED and o.served_at and o.created_at:
                    lead = (o.served_at - o.created_at).total_seconds() / 60.0
                    b_leads.append(lead)
                    if lead > 20:  # Branch-level SLA threshold: 20 mins
                        b_delayed_count += 1
                elif o.status in [OrderStatusEnum.SUBMITTED, OrderStatusEnum.IN_PROGRESS]:
                    lead = (now - o.created_at).total_seconds() / 60.0
                    if lead > 20:
                        b_delayed_count += 1

            b_avg_lead = round(sum(b_leads) / len(b_leads), 1) if b_leads else 0.0
            b_delay_pct = round((b_delayed_count / b_total) * 100, 1) if b_total > 0 else 0.0

            branch_summaries.append(
                BranchOperationalSummary(
                    branch_id=b.id,
                    branch_name=b.name,
                    total_orders_count=b_total,
                    completed_orders_count=b_completed,
                    active_orders_count=b_active,
                    avg_order_lead_time_minutes=b_avg_lead,
                    delayed_orders_count=b_delayed_count,
                    delayed_orders_percentage=b_delay_pct
                )
            )

        return OperationalMetricsOut(
            calculated_at=now,
            restaurant_id=restaurant_id,
            branch_id=branch_id,
            time_window_hours=time_window_hours,
            total_orders=total_orders,
            active_orders=active_orders,
            completed_orders=completed_orders,
            avg_order_lead_time_minutes=avg_lead_time,
            stations=station_metrics,
            top_delayed_dishes=top_delayed,
            branch_comparison=branch_summaries
        )
