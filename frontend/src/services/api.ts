import type {
  AIAnalystQuery,
  AIAnalystResponse,
  BranchOut,
  KitchenStationOut,
  LoginRequest,
  MenuCategoryOut,
  MenuItemOut,
  OperationalMetricsOut,
  OrderAddItemRequest,
  OrderCancelRequest,
  OrderCreate,
  OrderItemOut,
  OrderItemStatusUpdate,
  OrderOut,
  OrderServeRequest,
  StationQueueItemOut,
  TableOut,
  TokenResponse,
  UserOut
} from '../types';

const API_BASE = '/api/v1';

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

function getAuthToken(): string | null {
  return localStorage.getItem('serviceflow_token');
}

export function setAuthToken(token: string | null) {
  if (token) {
    localStorage.setItem('serviceflow_token', token);
  } else {
    localStorage.removeItem('serviceflow_token');
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    setAuthToken(null);
    window.dispatchEvent(new CustomEvent('serviceflow:unauthorized'));
    throw new ApiError(401, 'اعتبار نشست به پایان رسیده است. لطفا مجددا وارد شوید.');
  }

  if (!response.ok) {
    let errorDetail = 'خطا در ارتباط با سرور';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.message || JSON.stringify(errJson);
    } catch {
      errorDetail = response.statusText || errorDetail;
    }
    throw new ApiError(response.status, errorDetail);
  }

  return response.json();
}

export const api = {
  auth: {
    login: (data: LoginRequest) =>
      request<TokenResponse>('/auth/login', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    me: () => request<UserOut>('/auth/me'),
  },

  restaurants: {
    getBranches: () => request<BranchOut[]>('/restaurants/branches'),
    getStations: (branchId: string) =>
      request<KitchenStationOut[]>(`/restaurants/branches/${branchId}/stations`),
    getTables: (branchId: string) =>
      request<TableOut[]>(`/restaurants/branches/${branchId}/tables`),
  },

  menu: {
    getCategories: () => request<MenuCategoryOut[]>('/menu/categories'),
    getItems: () => request<MenuItemOut[]>('/menu/items'),
  },

  orders: {
    create: (data: OrderCreate) =>
      request<OrderOut>('/orders', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    list: (branchId?: string, activeOnly = true) => {
      const params = new URLSearchParams();
      if (branchId) params.append('branch_id', branchId);
      params.append('active_only', activeOnly ? 'true' : 'false');
      return request<OrderOut[]>(`/orders?${params.toString()}`);
    },
    get: (orderId: string, branchId?: string) => {
      const url = branchId ? `/orders/${orderId}?branch_id=${branchId}` : `/orders/${orderId}`;
      return request<OrderOut>(url);
    },
    addItems: (orderId: string, branchId: string, data: OrderAddItemRequest) =>
      request<OrderOut>(`/orders/${orderId}/items?branch_id=${branchId}`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    serve: (orderId: string, branchId: string, data: OrderServeRequest) =>
      request<OrderOut>(`/orders/${orderId}/serve?branch_id=${branchId}`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    cancel: (orderId: string, branchId: string, data: OrderCancelRequest) =>
      request<OrderOut>(`/orders/${orderId}/cancel?branch_id=${branchId}`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  },

  kitchen: {
    getQueue: (stationId: string, branchId: string) =>
      request<StationQueueItemOut[]>(`/stations/${stationId}/queue?branch_id=${branchId}`),
    updateItemStatus: (itemId: string, data: OrderItemStatusUpdate) =>
      request<OrderItemOut>(`/order-items/${itemId}/status`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
  },

  metrics: {
    getOperational: (branchId?: string, hours = 24) => {
      const params = new URLSearchParams();
      if (branchId) params.append('branch_id', branchId);
      params.append('time_window_hours', hours.toString());
      return request<OperationalMetricsOut>(`/metrics/operational?${params.toString()}`);
    },
  },

  ai: {
    explain: (query: AIAnalystQuery) =>
      request<AIAnalystResponse>('/ai/explain', {
        method: 'POST',
        body: JSON.stringify(query),
      }),
  },
};
