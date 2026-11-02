import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    BigInteger,
    DateTime,
    Date,
    ForeignKey,
    ForeignKeyConstraint,
    UniqueConstraint,
    Index,
    Text,
    Enum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def utcnow_date():
    return datetime.now(timezone.utc).date()


class RoleEnum(str, enum.Enum):
    MANAGER = "manager"
    WAITER = "waiter"
    KITCHEN = "kitchen"


class StationTypeEnum(str, enum.Enum):
    BARISTA = "barista"
    BREW_BAR = "brew_bar"
    COLD_BAR = "cold_bar"
    KITCHEN = "kitchen"


class TableSectionEnum(str, enum.Enum):
    MAIN_HALL = "main_hall"
    TERRACE = "terrace"
    VIP = "vip"
    BAR = "bar"


class OrderStatusEnum(str, enum.Enum):
    SUBMITTED = "submitted"
    IN_PROGRESS = "in_progress"
    READY_FOR_SERVICE = "ready_for_service"
    SERVED = "served"
    CANCELLED = "cancelled"


class OrderItemStatusEnum(str, enum.Enum):
    PENDING = "pending"
    PREPARING = "preparing"
    READY = "ready"
    SERVED = "served"
    CANCELLED = "cancelled"


# ==========================================
# 1. Multi-Tenant Restaurant & Branch Models
# ==========================================

class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    branches = relationship("Branch", back_populates="restaurant", cascade="all, delete-orphan")
    users = relationship("User", back_populates="restaurant", cascade="all, delete-orphan")
    menu_categories = relationship("MenuCategory", back_populates="restaurant", cascade="all, delete-orphan")
    menu_items = relationship("MenuItem", back_populates="restaurant", cascade="all, delete-orphan")


class Branch(Base):
    __tablename__ = "branches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    address = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("restaurant_id", "id", name="uq_branches_tenant"),
        Index("ix_branches_tenant_active", "restaurant_id", "is_active"),
    )

    restaurant = relationship("Restaurant", back_populates="branches")
    stations = relationship("KitchenStation", back_populates="branch", cascade="all, delete-orphan")
    tables = relationship("Table", back_populates="branch", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="branch", cascade="all, delete-orphan")


# ==========================================
# 2. Staff & Identity
# ==========================================

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id", ondelete="SET NULL"), nullable=True, index=True)
    station_id = Column(UUID(as_uuid=True), ForeignKey("kitchen_stations.id", ondelete="SET NULL"), nullable=True)
    email = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.WAITER)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("restaurant_id", "email", name="uq_users_tenant_email"),
        Index("ix_users_tenant_role", "restaurant_id", "role"),
    )

    restaurant = relationship("Restaurant", back_populates="users")
    branch = relationship("Branch")
    station = relationship("KitchenStation")


# ==========================================
# 3. Kitchen Stations & Tables
# ==========================================

class KitchenStation(Base):
    __tablename__ = "kitchen_stations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(UUID(as_uuid=True), nullable=False)
    branch_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(100), nullable=False)
    station_type = Column(Enum(StationTypeEnum), nullable=False, default=StationTypeEnum.BARISTA)
    target_prep_time_minutes = Column(Integer, default=5, nullable=False)  # SLA for delays
    display_order = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("restaurant_id", "branch_id", "id", name="uq_stations_tenant_branch"),
        ForeignKeyConstraint(
            ["restaurant_id", "branch_id"],
            ["branches.restaurant_id", "branches.id"],
            ondelete="CASCADE",
            name="fk_stations_branch_tenant"
        ),
        Index("ix_stations_tenant_branch_active", "restaurant_id", "branch_id", "is_active"),
    )

    branch = relationship("Branch", back_populates="stations")
    order_items = relationship("OrderItem", back_populates="station")


class Table(Base):
    __tablename__ = "tables"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(UUID(as_uuid=True), nullable=False)
    branch_id = Column(UUID(as_uuid=True), nullable=False)
    table_number = Column(String(50), nullable=False)
    section = Column(Enum(TableSectionEnum), nullable=False, default=TableSectionEnum.MAIN_HALL)
    capacity = Column(Integer, default=4, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("restaurant_id", "branch_id", "id", name="uq_tables_tenant_branch"),
        UniqueConstraint("restaurant_id", "branch_id", "table_number", name="uq_tables_number_branch"),
        ForeignKeyConstraint(
            ["restaurant_id", "branch_id"],
            ["branches.restaurant_id", "branches.id"],
            ondelete="CASCADE",
            name="fk_tables_branch_tenant"
        ),
        Index("ix_tables_tenant_branch_active", "restaurant_id", "branch_id", "is_active"),
    )

    branch = relationship("Branch", back_populates="tables")
    orders = relationship("Order", back_populates="table", overlaps="branch,orders")


# ==========================================
# 4. Menu & Branch-Station Routing
# ==========================================

class MenuCategory(Base):
    __tablename__ = "menu_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    display_order = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    restaurant = relationship("Restaurant", back_populates="menu_categories")
    items = relationship("MenuItem", back_populates="category", cascade="all, delete-orphan")


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("menu_categories.id", ondelete="CASCADE"), nullable=False, index=True)
    name_fa = Column(String(255), nullable=False)
    name_en = Column(String(255), nullable=True)
    price_toman = Column(BigInteger, nullable=False)  # Toman, no decimals
    default_station_type = Column(Enum(StationTypeEnum), nullable=False, default=StationTypeEnum.BARISTA)
    description = Column(Text, nullable=True)
    is_available = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    restaurant = relationship("Restaurant", back_populates="menu_items")
    category = relationship("MenuCategory", back_populates="items")


# ==========================================
# 5. Orders, Order Items & Concurrency
# ==========================================

class BranchDailyCounter(Base):
    __tablename__ = "branch_daily_counters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(UUID(as_uuid=True), nullable=False)
    branch_id = Column(UUID(as_uuid=True), nullable=False)
    counter_date = Column(Date, nullable=False)
    last_order_number = Column(Integer, nullable=False, default=1)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("restaurant_id", "branch_id", "counter_date", name="uq_branch_daily_counter"),
        ForeignKeyConstraint(
            ["restaurant_id", "branch_id"],
            ["branches.restaurant_id", "branches.id"],
            ondelete="CASCADE",
            name="fk_daily_counter_branch_tenant"
        ),
        Index("ix_counters_branch_date", "restaurant_id", "branch_id", "counter_date"),
    )



class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(UUID(as_uuid=True), nullable=False)
    branch_id = Column(UUID(as_uuid=True), nullable=False)
    table_id = Column(UUID(as_uuid=True), nullable=False)
    waiter_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    order_date = Column(Date, default=utcnow_date, nullable=False, index=True)
    order_number = Column(Integer, nullable=False)
    status = Column(Enum(OrderStatusEnum), nullable=False, default=OrderStatusEnum.SUBMITTED)
    version = Column(Integer, default=1, nullable=False)  # Optimistic lock for whole-order changes
    notes = Column(Text, nullable=True)
    total_price_toman = Column(BigInteger, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    served_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("restaurant_id", "branch_id", "id", name="uq_orders_tenant_branch"),
        UniqueConstraint("restaurant_id", "branch_id", "order_date", "order_number", name="uq_orders_branch_daily_number"),
        ForeignKeyConstraint(
            ["restaurant_id", "branch_id"],
            ["branches.restaurant_id", "branches.id"],
            ondelete="CASCADE",
            name="fk_orders_branch_tenant"
        ),
        ForeignKeyConstraint(
            ["restaurant_id", "branch_id", "table_id"],
            ["tables.restaurant_id", "tables.branch_id", "tables.id"],
            ondelete="RESTRICT",
            name="fk_orders_table_tenant"
        ),
        Index("ix_orders_branch_status", "restaurant_id", "branch_id", "status"),
        Index("ix_orders_created_at", "restaurant_id", "created_at"),
    )

    branch = relationship("Branch", back_populates="orders")
    table = relationship("Table", back_populates="orders", overlaps="branch,orders")
    waiter = relationship("User")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan", order_by="OrderItem.created_at", overlaps="order_items,station")
    history = relationship("OrderStatusHistory", back_populates="order", cascade="all, delete-orphan", order_by="OrderStatusHistory.created_at")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(UUID(as_uuid=True), nullable=False)
    branch_id = Column(UUID(as_uuid=True), nullable=False)
    order_id = Column(UUID(as_uuid=True), nullable=False)
    menu_item_id = Column(UUID(as_uuid=True), ForeignKey("menu_items.id", ondelete="RESTRICT"), nullable=False)
    station_id = Column(UUID(as_uuid=True), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price_toman = Column(BigInteger, nullable=False)
    status = Column(Enum(OrderItemStatusEnum), nullable=False, default=OrderItemStatusEnum.PENDING)
    version = Column(Integer, default=1, nullable=False)  # Optimistic lock for item status changes
    modifiers = Column(Text, nullable=True)  # Persian notes: کم‌شیرین، با یخ اضافه
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    preparing_at = Column(DateTime(timezone=True), nullable=True)
    ready_at = Column(DateTime(timezone=True), nullable=True)
    served_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("restaurant_id", "branch_id", "id", name="uq_order_items_tenant_branch"),
        ForeignKeyConstraint(
            ["restaurant_id", "branch_id", "order_id"],
            ["orders.restaurant_id", "orders.branch_id", "orders.id"],
            ondelete="CASCADE",
            name="fk_order_items_order_tenant"
        ),
        ForeignKeyConstraint(
            ["restaurant_id", "branch_id", "station_id"],
            ["kitchen_stations.restaurant_id", "kitchen_stations.branch_id", "kitchen_stations.id"],
            ondelete="RESTRICT",
            name="fk_order_items_station_tenant"
        ),
        Index("ix_order_items_station_status", "restaurant_id", "branch_id", "station_id", "status"),
    )

    order = relationship("Order", back_populates="items", overlaps="order_items,items")
    menu_item = relationship("MenuItem")
    station = relationship("KitchenStation", back_populates="order_items", overlaps="items,order")


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(UUID(as_uuid=True), nullable=False)
    branch_id = Column(UUID(as_uuid=True), nullable=False)
    order_id = Column(UUID(as_uuid=True), nullable=False)
    order_item_id = Column(UUID(as_uuid=True), nullable=True)
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=False)
    changed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    notes = Column(String(500), nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["restaurant_id", "branch_id", "order_id"],
            ["orders.restaurant_id", "orders.branch_id", "orders.id"],
            ondelete="CASCADE",
            name="fk_history_order_tenant"
        ),
        Index("ix_history_order_created", "restaurant_id", "order_id", "created_at"),
    )

    order = relationship("Order", back_populates="history")
    changed_by = relationship("User")
