import enum
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.entities import RoleEnum, StationTypeEnum, TableSectionEnum, OrderStatusEnum, OrderItemStatusEnum



# ==========================================
# Auth & User Schemas
# ==========================================

class LoginRequest(BaseModel):
    restaurant_slug: str = Field(..., min_length=2, max_length=100)
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    restaurant_id: uuid.UUID
    branch_id: Optional[uuid.UUID] = None
    role: RoleEnum
    full_name: str
    restaurant_name: str


class UserOut(BaseModel):
    id: uuid.UUID
    restaurant_id: uuid.UUID
    branch_id: Optional[uuid.UUID] = None
    station_id: Optional[uuid.UUID] = None
    email: str
    full_name: str
    role: RoleEnum
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Restaurant & Branch Schemas
# ==========================================

class BranchOut(BaseModel):
    id: uuid.UUID
    restaurant_id: uuid.UUID
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class KitchenStationOut(BaseModel):
    id: uuid.UUID
    restaurant_id: uuid.UUID
    branch_id: uuid.UUID
    name: str
    station_type: StationTypeEnum
    target_prep_time_minutes: int
    display_order: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TableOut(BaseModel):
    id: uuid.UUID
    restaurant_id: uuid.UUID
    branch_id: uuid.UUID
    table_number: str
    section: TableSectionEnum
    capacity: int
    is_active: bool
    active_order_id: Optional[uuid.UUID] = None
    active_order_status: Optional[OrderStatusEnum] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Menu Schemas
# ==========================================

class MenuItemOut(BaseModel):
    id: uuid.UUID
    restaurant_id: uuid.UUID
    category_id: uuid.UUID
    name_fa: str
    name_en: Optional[str] = None
    price_toman: int
    default_station_type: StationTypeEnum
    description: Optional[str] = None
    is_available: bool

    model_config = ConfigDict(from_attributes=True)


class MenuCategoryOut(BaseModel):
    id: uuid.UUID
    restaurant_id: uuid.UUID
    name: str
    display_order: int
    is_active: bool
    items: List[MenuItemOut] = []

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Order & Order Item Schemas
# ==========================================

class OrderItemCreate(BaseModel):
    menu_item_id: uuid.UUID
    quantity: int = Field(default=1, ge=1)
    modifiers: Optional[str] = None  # e.g., "کم‌شیرین", "با یخ اضافه"


class OrderCreate(BaseModel):
    branch_id: uuid.UUID
    table_id: uuid.UUID
    notes: Optional[str] = None
    items: List[OrderItemCreate] = Field(..., min_length=1)


class OrderAddItemRequest(BaseModel):
    expected_order_version: int
    items: List[OrderItemCreate] = Field(..., min_length=1)


class OrderItemStatusUpdate(BaseModel):
    target_status: OrderItemStatusEnum
    expected_item_version: int
    notes: Optional[str] = None


class OrderServeRequest(BaseModel):
    expected_order_version: int
    notes: Optional[str] = None


class OrderCancelRequest(BaseModel):
    expected_order_version: int
    reason: Optional[str] = None


class OrderItemOut(BaseModel):
    id: uuid.UUID
    restaurant_id: uuid.UUID
    branch_id: uuid.UUID
    order_id: uuid.UUID
    menu_item_id: uuid.UUID
    station_id: uuid.UUID
    station_name: Optional[str] = None
    item_name_fa: Optional[str] = None
    item_name_en: Optional[str] = None
    quantity: int
    unit_price_toman: int
    status: OrderItemStatusEnum
    version: int
    modifiers: Optional[str] = None
    created_at: datetime
    preparing_at: Optional[datetime] = None
    ready_at: Optional[datetime] = None
    served_at: Optional[datetime] = None
    elapsed_minutes: Optional[float] = None
    is_delayed: bool = False

    model_config = ConfigDict(from_attributes=True)


class OrderOut(BaseModel):
    id: uuid.UUID
    restaurant_id: uuid.UUID
    branch_id: uuid.UUID
    branch_name: Optional[str] = None
    table_id: uuid.UUID
    table_number: Optional[str] = None
    table_section: Optional[TableSectionEnum] = None
    waiter_id: uuid.UUID
    waiter_name: Optional[str] = None
    order_number: int
    status: OrderStatusEnum
    version: int
    notes: Optional[str] = None
    total_price_toman: int
    created_at: datetime
    updated_at: datetime
    served_at: Optional[datetime] = None
    items: List[OrderItemOut] = []
    ready_items_count: int = 0
    total_items_count: int = 0
    is_ready_for_service: bool = False

    model_config = ConfigDict(from_attributes=True)


class StationQueueItemOut(BaseModel):
    item_id: uuid.UUID
    order_id: uuid.UUID
    order_number: int
    table_number: str
    menu_item_name_fa: str
    menu_item_name_en: Optional[str] = None
    quantity: int
    status: OrderItemStatusEnum
    version: int
    modifiers: Optional[str] = None
    created_at: datetime
    preparing_at: Optional[datetime] = None
    elapsed_minutes: float
    target_prep_time_minutes: int
    is_delayed: bool


# ==========================================
# Operational Metrics & AI Schemas
# ==========================================

class StationPerformanceMetric(BaseModel):
    station_id: uuid.UUID
    station_name: str
    station_type: StationTypeEnum
    target_prep_time_minutes: int
    total_items_count: int
    completed_items_count: int
    delayed_items_count: int
    delay_rate_percentage: float
    avg_turnaround_minutes: float


class DelayedDishSummary(BaseModel):
    menu_item_id: uuid.UUID
    name_fa: str
    station_type: StationTypeEnum
    delayed_count: int
    total_ordered_count: int


class BranchOperationalSummary(BaseModel):
    branch_id: uuid.UUID
    branch_name: str
    total_orders_count: int
    completed_orders_count: int
    active_orders_count: int
    avg_order_lead_time_minutes: float
    delayed_orders_count: int
    delayed_orders_percentage: float


class OperationalMetricsOut(BaseModel):
    calculated_at: datetime
    restaurant_id: uuid.UUID
    branch_id: Optional[uuid.UUID] = None
    time_window_hours: int
    total_orders: int
    active_orders: int
    completed_orders: int
    avg_order_lead_time_minutes: float
    stations: List[StationPerformanceMetric]
    top_delayed_dishes: List[DelayedDishSummary]
    branch_comparison: List[BranchOperationalSummary] = []


class AnalyticalIntentEnum(str, enum.Enum):
    BOTTLENECK_STATION = "BOTTLENECK_STATION"
    DELAYED_ITEMS = "DELAYED_ITEMS"
    BRANCH_COMPARISON = "BRANCH_COMPARISON"
    SHIFT_SUMMARY = "SHIFT_SUMMARY"


class AIAnalystQuery(BaseModel):
    branch_id: Optional[uuid.UUID] = None
    intent: AnalyticalIntentEnum = Field(default=AnalyticalIntentEnum.SHIFT_SUMMARY)
    question: Optional[str] = Field(None, max_length=200)


class AIAnalystResponse(BaseModel):
    intent: AnalyticalIntentEnum
    question: Optional[str] = None
    measured_facts: List[str]
    analysis_text: str
    is_fallback: bool = False
    provider: str = "deterministic_engine"
    analyzed_at: datetime
