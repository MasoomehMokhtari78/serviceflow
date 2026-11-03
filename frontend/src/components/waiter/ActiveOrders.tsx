import React, { useState, useEffect, useCallback } from 'react';
import { api, ApiError } from '../../services/api';
import type { OrderOut } from '../../types';
import { formatTime, formatToman, getTableSectionLabel, toPersianDigits } from '../../utils/formatters';
import { StatusBadge } from '../common/StatusBadge';
import { 
  RotateCw, 
  Utensils, 
  CheckCircle, 
  Clock, 
  PlusCircle, 
  AlertCircle,
  BellRing
} from 'lucide-react';

interface ActiveOrdersProps {
  branchId: string;
  onOpenCreateOrder: () => void;
  onSelectOrder: (order: OrderOut) => void;
}

export const ActiveOrders: React.FC<ActiveOrdersProps> = ({
  branchId,
  onOpenCreateOrder,
  onSelectOrder,
}) => {
  const [orders, setOrders] = useState<OrderOut[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [filter, setFilter] = useState<'active' | 'all'>('active');
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const fetchOrders = useCallback(async (isBackground = false) => {
    if (!branchId) return;
    if (!isBackground) setLoading(true);
    else setRefreshing(true);
    setError(null);

    try {
      const data = await api.orders.list(branchId, filter === 'active');
      setOrders(data);
    } catch (err: any) {
      setError(err.message || 'خطا در بارگذاری لیست سفارش‌ها');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [branchId, filter]);

  useEffect(() => {
    fetchOrders(false);

    // Periodic polling every 5 seconds for waiter view
    const interval = setInterval(() => {
      fetchOrders(true);
    }, 5000);

    return () => clearInterval(interval);
  }, [fetchOrders]);

  const handleQuickServe = async (e: React.MouseEvent, order: OrderOut) => {
    e.stopPropagation();
    setActionError(null);

    try {
      await api.orders.serve(order.id, branchId, {
        expected_order_version: order.version,
      });
      fetchOrders(true);
    } catch (err: any) {
      if (err instanceof ApiError && err.status === 409) {
        setActionError('سفارش همزمان تغییر کرده بود؛ اطلاعات به‌روزرسانی شد.');
        fetchOrders(true);
      } else {
        setActionError(err.message || 'خطا در سرو سفارش');
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Bar: Title & Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-stone-100 flex items-center">
            <Utensils className="w-6 h-6 ml-2 text-amber-500" />
            سفارش‌های سالن
          </h1>
          <p className="text-xs text-stone-400 mt-1">
            پیگیری زنده وضعیت آماده‌سازی اقلام سفارش در آشپزخانه و بار
          </p>
        </div>

        <div className="flex items-center space-x-2 space-x-reverse">
          <div className="bg-stone-950 p-1 rounded-xl border border-stone-800 flex text-xs">
            <button
              onClick={() => setFilter('active')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
                filter === 'active'
                  ? 'bg-amber-600 text-white shadow'
                  : 'text-stone-400 hover:text-stone-200'
              }`}
            >
              سفارش‌های باز
            </button>
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
                filter === 'all'
                  ? 'bg-amber-600 text-white shadow'
                  : 'text-stone-400 hover:text-stone-200'
              }`}
            >
              همه سفارش‌ها
            </button>
          </div>

          <button
            onClick={() => fetchOrders(true)}
            disabled={refreshing}
            title="به‌روزرسانی داده‌ها"
            className="p-2 rounded-xl bg-stone-900 border border-stone-800 text-stone-300 hover:text-white hover:bg-stone-800 transition-colors"
          >
            <RotateCw className={`w-4 h-4 ${refreshing ? 'animate-spin text-amber-500' : ''}`} />
          </button>

          <button
            onClick={onOpenCreateOrder}
            className="inline-flex items-center px-4 py-2 rounded-xl text-xs font-bold bg-amber-600 hover:bg-amber-500 text-white shadow-md shadow-amber-950 transition-all active:scale-95"
          >
            <PlusCircle className="w-4 h-4 ml-1.5" />
            ثبت سفارش جدید
          </button>
        </div>
      </div>

      {actionError && (
        <div className="p-3 rounded-xl bg-amber-950/60 border border-amber-800/80 text-amber-200 text-xs flex items-center">
          <AlertCircle className="w-4 h-4 ml-2 text-amber-400 shrink-0" />
          <span>{actionError}</span>
        </div>
      )}

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-950/60 border border-rose-800/80 text-rose-200 text-xs flex items-center">
          <AlertCircle className="w-4 h-4 ml-2 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Orders Grid */}
      {loading ? (
        <div className="h-64 flex flex-col items-center justify-center space-y-3">
          <div className="w-8 h-8 border-3 border-amber-600/30 border-t-amber-500 rounded-full animate-spin" />
          <span className="text-xs text-stone-400">در حال دریافت آخرین وضعیت سفارش‌ها...</span>
        </div>
      ) : orders.length === 0 ? (
        <div className="py-16 text-center border-2 border-dashed border-stone-800 rounded-2xl bg-stone-950/40">
          <Utensils className="w-12 h-12 text-stone-600 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-stone-300">هیچ سفارش فعالی وجود ندارد</h3>
          <p className="text-xs text-stone-500 mt-1 max-w-sm mx-auto">
            برای ثبت سفارش جدید از دکمه «ثبت سفارش جدید» استفاده کنید.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {orders.map((order) => {
            const isReady = order.is_ready_for_service;
            const progressPercent =
              order.total_items_count > 0
                ? Math.round((order.ready_items_count / order.total_items_count) * 100)
                : 0;

            return (
              <div
                key={order.id}
                onClick={() => onSelectOrder(order)}
                className={`p-5 rounded-2xl bg-stone-950 border transition-all cursor-pointer flex flex-col justify-between hover:border-amber-500/60 hover:shadow-xl ${
                  isReady && order.status?.toLowerCase() !== 'served'
                    ? 'border-emerald-500/80 ring-2 ring-emerald-500/20 shadow-emerald-950/30'
                    : 'border-stone-800/90'
                }`}
              >
                <div>
                  {/* Card Header */}
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center space-x-2 space-x-reverse">
                        <span className="text-base font-black text-stone-100">
                          میز {toPersianDigits(order.table_number || '')}
                        </span>
                        {order.table_section && (
                          <span className="text-[11px] text-stone-400 font-medium">
                            ({getTableSectionLabel(order.table_section)})
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-stone-400 mt-0.5 flex items-center space-x-2 space-x-reverse">
                        <span className="font-semibold text-amber-400">
                          #{toPersianDigits(order.order_number)}
                        </span>
                        <span>•</span>
                        <span className="flex items-center">
                          <Clock className="w-3 h-3 ml-1" />
                          {formatTime(order.created_at)}
                        </span>
                      </div>
                    </div>
                    <StatusBadge status={order.status} type="order" />
                  </div>

                  {/* Ready alert badge for waiter */}
                  {isReady && order.status?.toLowerCase() !== 'served' && (
                    <div className="mt-3 p-2 rounded-xl bg-emerald-950/70 border border-emerald-600/60 text-emerald-300 text-xs font-semibold flex items-center">
                      <BellRing className="w-4 h-4 ml-1.5 animate-bounce text-emerald-400" />
                      تمام اقلام آماده شد — لطفا سفارش را تحویل دهید!
                    </div>
                  )}

                  {/* Progress Bar */}
                  <div className="mt-4">
                    <div className="flex justify-between text-[11px] font-medium text-stone-400 mb-1.5">
                      <span>پیشرفت آماده‌سازی:</span>
                      <span>
                        {toPersianDigits(order.ready_items_count)} از {toPersianDigits(order.total_items_count)} قلم
                      </span>
                    </div>
                    <div className="w-full bg-stone-900 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-full transition-all duration-300 ${
                          isReady ? 'bg-emerald-500' : 'bg-amber-500'
                        }`}
                        style={{ width: `${progressPercent}%` }}
                      />
                    </div>
                  </div>

                  {/* Item List Preview */}
                  <div className="mt-3.5 space-y-1.5 border-t border-stone-800/80 pt-3">
                    {order.items.slice(0, 4).map((i) => (
                      <div
                        key={i.id}
                        className="flex justify-between items-center text-xs text-stone-300"
                      >
                        <span className="truncate flex items-center">
                          <span className="text-stone-500 font-semibold ml-1.5">
                            {toPersianDigits(i.quantity)}×
                          </span>
                          {i.item_name_fa}
                        </span>
                        <span
                          className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                            i.status === 'READY'
                              ? 'bg-emerald-950 text-emerald-400 border border-emerald-800/50'
                              : i.status === 'PREPARING'
                              ? 'bg-blue-950 text-blue-400 border border-blue-800/50'
                              : 'bg-stone-900 text-stone-400'
                          }`}
                        >
                          {i.status?.toLowerCase() === 'ready' ? 'آماده' : i.status?.toLowerCase() === 'preparing' ? 'پخت' : 'انتظار'}
                        </span>
                      </div>
                    ))}
                    {order.items.length > 4 && (
                      <div className="text-[10px] text-stone-500 text-left pt-0.5">
                        +{toPersianDigits(order.items.length - 4)} قلم دیگر...
                      </div>
                    )}
                  </div>
                </div>

                {/* Card Footer */}
                <div className="mt-4 pt-3 border-t border-stone-800/80 flex items-center justify-between">
                  <div className="text-xs font-bold text-amber-400">
                    {formatToman(order.total_price_toman)}
                  </div>

                  {isReady && order.status?.toLowerCase() !== 'served' ? (
                    <button
                      type="button"
                      onClick={(e) => handleQuickServe(e, order)}
                      className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-950 transition-all active:scale-95"
                    >
                      <CheckCircle className="w-3.5 h-3.5 ml-1" />
                      سرو سفارش
                    </button>
                  ) : (
                    <span className="text-[11px] text-stone-500">مشاهده جزئیات ←</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
