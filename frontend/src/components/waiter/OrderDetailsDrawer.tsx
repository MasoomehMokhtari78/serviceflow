import React, { useState } from 'react';
import { api, ApiError } from '../../services/api';
import type { OrderOut } from '../../types';
import { formatTime, formatToman, getTableSectionLabel, toPersianDigits } from '../../utils/formatters';
import { StatusBadge } from '../common/StatusBadge';
import { X, CheckCircle, Ban, AlertCircle, Clock } from 'lucide-react';

interface OrderDetailsDrawerProps {
  order: OrderOut | null;
  isOpen: boolean;
  onClose: () => void;
  onOrderUpdated: () => void;
}

export const OrderDetailsDrawer: React.FC<OrderDetailsDrawerProps> = ({
  order,
  isOpen,
  onClose,
  onOrderUpdated,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conflictMsg, setConflictMsg] = useState<string | null>(null);

  if (!isOpen || !order) return null;

  const handleServe = async () => {
    setLoading(true);
    setError(null);
    setConflictMsg(null);

    try {
      await api.orders.serve(order.id, order.branch_id, {
        expected_order_version: order.version,
      });
      onOrderUpdated();
      onClose();
    } catch (err: any) {
      if (err instanceof ApiError && err.status === 409) {
        setConflictMsg('توجه: این سفارش توسط کاربر دیگری به‌روزرسانی شده بود. اطلاعات تجدید گردید.');
        onOrderUpdated();
      } else {
        setError(err.message || 'خطا در ثبت سرو سفارش');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    const reason = window.prompt('لطفا دلیل لغو سفارش را وارد کنید (مثلا انصراف مشتری):');
    if (reason === null) return;

    setLoading(true);
    setError(null);
    setConflictMsg(null);

    try {
      await api.orders.cancel(order.id, order.branch_id, {
        expected_order_version: order.version,
        reason: reason.trim() || undefined,
      });
      onOrderUpdated();
      onClose();
    } catch (err: any) {
      if (err instanceof ApiError && err.status === 409) {
        setConflictMsg('توجه: نسخه سفارش تغییر کرده بود. اطلاعات مجددا بارگذاری شد.');
        onOrderUpdated();
      } else {
        setError(err.message || 'خطا در لغو سفارش');
      }
    } finally {
      setLoading(false);
    }
  };

  const canServe = order.is_ready_for_service && order.status?.toLowerCase() !== 'served' && order.status?.toLowerCase() !== 'cancelled';
  const isTerminal = order.status?.toLowerCase() === 'served' || order.status?.toLowerCase() === 'cancelled';

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/75 backdrop-blur-sm flex justify-end">
      <div className="w-full max-w-md bg-stone-900 border-r border-stone-800 h-full flex flex-col shadow-2xl animate-in slide-in-from-left duration-200">
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-stone-800 bg-stone-950 flex items-center justify-between">
          <div>
            <div className="flex items-center space-x-2 space-x-reverse">
              <span className="font-extrabold text-base text-stone-100">
                سفارش شماره #{toPersianDigits(order.order_number)}
              </span>
              <StatusBadge status={order.status} type="order" />
            </div>
            <div className="text-xs text-stone-400 mt-1 flex items-center space-x-2 space-x-reverse">
              <span>میز {toPersianDigits(order.table_number || '')}</span>
              {order.table_section && (
                <>
                  <span>•</span>
                  <span>{getTableSectionLabel(order.table_section)}</span>
                </>
              )}
              <span>•</span>
              <span className="flex items-center">
                <Clock className="w-3 h-3 ml-1" />
                {formatTime(order.created_at)}
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-stone-400 hover:text-stone-100 hover:bg-stone-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Notices */}
        {conflictMsg && (
          <div className="m-4 p-3 rounded-xl bg-amber-950/60 border border-amber-800/80 text-amber-200 text-xs flex items-center">
            <AlertCircle className="w-4 h-4 ml-2 text-amber-400 shrink-0" />
            <span>{conflictMsg}</span>
          </div>
        )}
        {error && (
          <div className="m-4 p-3 rounded-xl bg-rose-950/60 border border-rose-800/80 text-rose-200 text-xs flex items-center">
            <AlertCircle className="w-4 h-4 ml-2 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Items List */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-3">
          <div className="flex justify-between items-center text-xs font-semibold text-stone-400">
            <span>اقلام سفارش ({toPersianDigits(order.items.length)})</span>
            <span>
              {toPersianDigits(order.ready_items_count)} از {toPersianDigits(order.total_items_count)} آماده تحویل
            </span>
          </div>

          <div className="space-y-2.5">
            {order.items.map((item) => (
              <div
                key={item.id}
                className="p-3 rounded-xl bg-stone-950 border border-stone-800 space-y-2"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-semibold text-sm text-stone-100 flex items-center">
                      <span className="w-5 h-5 rounded-md bg-stone-800 text-amber-400 text-xs flex items-center justify-center font-bold ml-2">
                        {toPersianDigits(item.quantity)}
                      </span>
                      {item.item_name_fa}
                    </div>
                    {item.modifiers && (
                      <div className="text-[11px] text-amber-300/80 mt-1 mr-7">
                        یادداشت: {item.modifiers}
                      </div>
                    )}
                    {item.station_name && (
                      <div className="text-[10px] text-stone-400 mt-0.5 mr-7">
                        ایستگاه: {item.station_name}
                      </div>
                    )}
                  </div>
                  <div className="text-left">
                    <StatusBadge status={item.status} type="item" />
                    <div className="text-xs text-stone-400 mt-1 font-medium">
                      {formatToman(item.unit_price_toman * item.quantity)}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {order.notes && (
            <div className="mt-4 p-3 rounded-xl bg-stone-950 border border-stone-800 text-xs text-stone-300">
              <span className="font-semibold text-stone-400">یادداشت کلی سالن‌کار: </span>
              {order.notes}
            </div>
          )}
        </div>

        {/* Bottom Actions */}
        <div className="p-4 sm:p-5 border-t border-stone-800 bg-stone-950 space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-xs text-stone-400">جمع کل فاکتور:</span>
            <span className="text-lg font-black text-amber-400">
              {formatToman(order.total_price_toman)}
            </span>
          </div>

          {!isTerminal && (
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={handleCancel}
                disabled={loading}
                className="py-2.5 px-3 rounded-xl text-xs font-semibold text-rose-300 bg-rose-950/40 hover:bg-rose-950 border border-rose-800/50 flex items-center justify-center transition-colors disabled:opacity-50"
              >
                <Ban className="w-4 h-4 ml-1.5" />
                لغو سفارش
              </button>

              <button
                type="button"
                onClick={handleServe}
                disabled={loading || !canServe}
                className={`py-2.5 px-3 rounded-xl text-xs font-bold text-white flex items-center justify-center transition-all shadow-md ${
                  canServe
                    ? 'bg-emerald-600 hover:bg-emerald-500 shadow-emerald-950 active:scale-95'
                    : 'bg-stone-800 text-stone-500 cursor-not-allowed border border-stone-700'
                }`}
              >
                <CheckCircle className="w-4 h-4 ml-1.5" />
                {canServe ? 'تحویل و سرو سفارش' : 'در انتظار آماده‌سازی'}
              </button>
            </div>
          )}

          {order.status?.toLowerCase() === 'served' && (
            <div className="p-2.5 rounded-xl bg-stone-800/60 border border-stone-700/60 text-center text-xs text-stone-300 font-medium">
              این سفارش با موفقیت سرو شده و پرونده آن بسته است.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
