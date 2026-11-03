export type RoleEnum = 
  | 'manager' | 'waiter' | 'kitchen'
  | 'MANAGER' | 'WAITER' | 'KITCHEN';

export type StationTypeEnum = 
  | 'barista' | 'brew_bar' | 'cold_bar' | 'kitchen'
  | 'BARISTA' | 'BREW_BAR' | 'COLD_BAR' | 'KITCHEN';

export type TableSectionEnum = 
  | 'main_hall' | 'terrace' | 'vip' | 'bar'
  | 'MAIN_HALL' | 'TERRACE' | 'VIP' | 'BAR';

export type OrderStatusEnum = 
  | 'submitted' | 'in_progress' | 'ready_for_service' | 'served' | 'cancelled'
  | 'SUBMITTED' | 'IN_PROGRESS' | 'READY_FOR_SERVICE' | 'SERVED' | 'CANCELLED';

export type OrderItemStatusEnum = 
  | 'pending' | 'preparing' | 'ready' | 'served' | 'cancelled'
  | 'PENDING' | 'PREPARING' | 'READY' | 'SERVED' | 'CANCELLED';

export type AnalyticalIntentEnum = 
  | 'BOTTLENECK_STATION' 
  | 'DELAYED_ITEMS' 
  | 'BRANCH_COMPARISON' 
  | 'SHIFT_SUMMARY';

export interface LoginRequest {
  restaurant_slug: string;
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  restaurant_id: string;
  branch_id?: string | null;
  role: RoleEnum;
  full_name: string;
  restaurant_name: string;
}

export interface UserOut {
  id: string;
  restaurant_id: string;
  branch_id?: string | null;
  station_id?: string | null;
  email: string;
  full_name: string;
  role: RoleEnum;
  is_active: boolean;
}

export interface BranchOut {
  id: string;
  restaurant_id: string;
  name: string;
  address?: string;
  phone?: string;
  is_active: boolean;
}

export interface KitchenStationOut {
  id: string;
  restaurant_id: string;
  branch_id: string;
  name: string;
  station_type: StationTypeEnum;
  target_prep_time_minutes: number;
  display_order: number;
  is_active: boolean;
}

export interface TableOut {
  id: string;
  restaurant_id: string;
  branch_id: string;
  table_number: string;
  section: TableSectionEnum;
  capacity: number;
  is_active: boolean;
  active_order_id?: string | null;
  active_order_status?: OrderStatusEnum | null;
}

export interface MenuItemOut {
  id: string;
  restaurant_id: string;
  category_id: string;
  name_fa: string;
  name_en?: string;
  price_toman: number;
  default_station_type: StationTypeEnum;
  description?: string;
  is_available: boolean;
}

export interface MenuCategoryOut {
  id: string;
  restaurant_id: string;
  name: string;
  display_order: number;
  is_active: boolean;
  items: MenuItemOut[];
}

export interface OrderItemCreate {
  menu_item_id: string;
  quantity: number;
  modifiers?: string;
}

export interface OrderCreate {
  branch_id: string;
  table_id: string;
  notes?: string;
  items: OrderItemCreate[];
}

export interface OrderAddItemRequest {
  expected_order_version: number;
  items: OrderItemCreate[];
}

export interface OrderItemStatusUpdate {
  target_status: OrderItemStatusEnum;
  expected_item_version: number;
  notes?: string;
}

export interface OrderServeRequest {
  expected_order_version: number;
  notes?: string;
}

export interface OrderCancelRequest {
  expected_order_version: number;
  reason?: string;
}

export interface OrderItemOut {
  id: string;
  restaurant_id: string;
  branch_id: string;
  order_id: string;
  menu_item_id: string;
  station_id: string;
  station_name?: string;
  item_name_fa?: string;
  item_name_en?: string;
  quantity: number;
  unit_price_toman: number;
  status: OrderItemStatusEnum;
  version: number;
  modifiers?: string;
  created_at: string;
  preparing_at?: string;
  ready_at?: string;
  served_at?: string;
  elapsed_minutes?: number;
  is_delayed: boolean;
}

export interface OrderOut {
  id: string;
  restaurant_id: string;
  branch_id: string;
  branch_name?: string;
  table_id: string;
  table_number?: string;
  table_section?: TableSectionEnum;
  waiter_id: string;
  waiter_name?: string;
  order_number: number;
  status: OrderStatusEnum;
  version: number;
  notes?: string;
  total_price_toman: number;
  created_at: string;
  updated_at: string;
  served_at?: string;
  items: OrderItemOut[];
  ready_items_count: number;
  total_items_count: number;
  is_ready_for_service: boolean;
}

export interface StationQueueItemOut {
  item_id: string;
  order_id: string;
  order_number: number;
  table_number: string;
  menu_item_name_fa: string;
  menu_item_name_en?: string;
  quantity: number;
  status: OrderItemStatusEnum;
  version: number;
  modifiers?: string;
  created_at: string;
  preparing_at?: string;
  elapsed_minutes: number;
  target_prep_time_minutes: number;
  is_delayed: boolean;
}

export interface StationPerformanceMetric {
  station_id: string;
  station_name: string;
  station_type: StationTypeEnum;
  target_prep_time_minutes: number;
  total_items_count: number;
  completed_items_count: number;
  delayed_items_count: number;
  delay_rate_percentage: number;
  avg_turnaround_minutes: number;
}

export interface DelayedDishSummary {
  menu_item_id: string;
  name_fa: string;
  station_type: StationTypeEnum;
  delayed_count: number;
  total_ordered_count: number;
}

export interface BranchOperationalSummary {
  branch_id: string;
  branch_name: string;
  total_orders_count: number;
  completed_orders_count: number;
  active_orders_count: number;
  avg_order_lead_time_minutes: number;
  delayed_orders_count: number;
  delayed_orders_percentage: number;
}

export interface OperationalMetricsOut {
  calculated_at: string;
  restaurant_id: string;
  branch_id?: string;
  time_window_hours: number;
  total_orders: number;
  active_orders: number;
  completed_orders: number;
  avg_order_lead_time_minutes: number;
  stations: StationPerformanceMetric[];
  top_delayed_dishes: DelayedDishSummary[];
  branch_comparison: BranchOperationalSummary[];
}

export interface AIAnalystQuery {
  branch_id?: string;
  intent: AnalyticalIntentEnum;
  question?: string;
}

export interface AIAnalystResponse {
  intent: AnalyticalIntentEnum;
  question?: string;
  measured_facts: string[];
  analysis_text: string;
  is_fallback: boolean;
  provider: string;
  analyzed_at: string;
}
