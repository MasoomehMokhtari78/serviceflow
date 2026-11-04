import React, { useState, useEffect, useCallback } from 'react';
import { api, ApiError } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import type { KitchenStationOut, OrderItemStatusEnum, StationQueueItemOut } from '../../types';
import { formatMinutes, toPersianDigits } from '../../utils/formatters';
import { 
  Coffee, 
  RotateCw, 
  CheckCircle2, 
  Play, 
  AlertTriangle, 
  Clock, 
  Flame, 
  AlertCircle
} from 'lucide-react';

interface KitchenQueueProps {
  branchId: string;
}

export const KitchenQueue: React.FC<KitchenQueueProps> = ({ branchId }) => {
  const { user } = useAuth();
  const [stations, setStations] = useState<KitchenStationOut[]>([]);
  const [selectedStationId, setSelectedStationId] = useState<string>('');
  const [queue, setQueue] = useState<StationQueueItemOut[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [conflictNotice, setConflictNotice] = useState<string | null>(null);

  // Load available stations
  useEffect(() => {
    if (!branchId) return;

    async function loadStations() {
      try {
        const data = await api.restaurants.getStations(branchId);
        setStations(data);

        // If kitchen staff has a station_id assigned, default to it
        if (user?.station_id) {
          setSelectedStationId(user.station_id);
        } else if (data.length > 0) {
          setSelectedStationId(data[0].id);
        }
      } catch (err: any) {
        setError(err.message || 'خطا در بارگذاری ایستگاه‌های کاری');
      }
    }

    loadStations();
  }, [branchId, user?.station_id]);

  // Fetch queue items
  const fetchQueue = useCallback(async (isBackground = false) => {
    if (!branchId || !selectedStationId) return;
    if (!isBackground) setLoading(true);
    else setRefreshing(true);
    setError(null);

    try {
      const items = await api.kitchen.getQueue(selectedStationId, branchId);
      setQueue(items);
    } catch (err: any) {
      setError(err.message || 'خطا در دریافت صف اقلام ایستگاه');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [branchId, selectedStationId]);

  // Polling every 4 seconds for live kitchen updates
  useEffect(() => {
    fetchQueue(false);

    const interval = setInterval(() => {
      fetchQueue(true);
    }, 4000);

    return () => clearInterval(interval);
  }, [fetchQueue]);

  const handleUpdateStatus = async (item: StationQueueItemOut, nextStatus: OrderItemStatusEnum) => {
    setActionLoadingId(item.item_id);
    setError(null);
    setConflictNotice(null);

    try {
      await api.kitchen.updateItemStatus(item.item_id, {
        target_status: nextStatus,
        expected_item_version: item.version,
      });
      fetchQueue(true);
    } catch (err: any) {
      if (err instanceof ApiError && err.status === 409) {
        setConflictNotice('وضعیت این آیتم همزمان توسط پرسنل دیگری تغییر کرد. صف به‌روزرسانی شد.');
        fetchQueue(true);
      } else {
        setError(err.message || 'خطا در تغییر وضعیت آیتم');
      }
    } finally {
      setActionLoadingId(null);
    }
  };

  const currentStation = stations.find((s) => s.id === selectedStationId);

  return (
    <div className="space-y-6">
      {/* KDS Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-stone-100 flex items-center">
            <Flame className="w-6 h-6 ml-2 text-blue-500" />
            صف نمایش KDS آشپزخانه و بار
          </h1>
          <p className="text-xs text-stone-400 mt-1">
            سفارشات زنده تفکیک شده بر اساس ایستگاه پخت و بار
          </p>
        </div>

        <div className="flex items-center space-x-2 space-x-reverse">
          {/* Station Selector: enabled for managers, or locked to assigned for kitchen */}
          {user?.role?.toLowerCase() === 'manager' ? (
            <select
              value={selectedStationId}
              onChange={(e) => setSelectedStationId(e.target.value)}
              className="bg-stone-950 border border-stone-800 text-stone-200 text-xs px-3 py-2 rounded-xl focus:outline-none focus:border-blue-500"
            >
              {stations.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({toPersianDigits(s.target_prep_time_minutes)} دقیقه)
                </option>
              ))}
            </select>
          ) : (
            <div className="px-3 py-2 rounded-xl bg-blue-950/40 border border-blue-800/60 text-blue-300 text-xs font-bold">
              ایستگاه شما: {currentStation?.name || 'بار و آشپزخانه'}
            </div>
          )}

          <button
            onClick={() => fetchQueue(true)}
            disabled={refreshing}
            className="p-2 rounded-xl bg-stone-900 border border-stone-800 text-stone-300 hover:text-white transition-colors"
          >
            <RotateCw className={`w-4 h-4 ${refreshing ? 'animate-spin text-blue-500' : ''}`} />
          </button>
        </div>
      </div>

      {conflictNotice && (
        <div className="p-3 rounded-xl bg-amber-950/60 border border-amber-800/80 text-amber-200 text-xs flex items-center">
          <AlertCircle className="w-4 h-4 ml-2 text-amber-400 shrink-0" />
          <span>{conflictNotice}</span>
        </div>
      )}

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-950/60 border border-rose-800/80 text-rose-200 text-xs flex items-center">
          <AlertCircle className="w-4 h-4 ml-2 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Queue Tickets Grid */}
      {loading ? (
        <div className="h-64 flex flex-col items-center justify-center space-y-3">
          <div className="w-8 h-8 border-3 border-blue-600/30 border-t-blue-500 rounded-full animate-spin" />
          <span className="text-xs text-stone-400">در حال دریافت تیکت‌های ایستگاه...</span>
        </div>
      ) : queue.length === 0 ? (
        <div className="py-20 text-center border-2 border-dashed border-stone-800 rounded-2xl bg-stone-950/40">
          <Coffee className="w-12 h-12 text-stone-600 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-stone-300">صف ایستگاه خالی است!</h3>
          <p className="text-xs text-stone-500 mt-1">
            تمام اقلام این بخش آماده شده یا سفارشی در صف ثبت نشده است.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {queue.map((item) => {
            const isDelayed = item.is_delayed;
            const isPending = item.status?.toLowerCase() === 'pending';
            const isPreparing = item.status?.toLowerCase() === 'preparing';
            const isItemLoading = actionLoadingId === item.item_id;

            return (
              <div
                key={item.item_id}
                className={`p-4 rounded-2xl bg-stone-950 border flex flex-col justify-between transition-all shadow-lg ${
                  isDelayed
                    ? 'border-rose-600/80 ring-2 ring-rose-600/20 bg-rose-950/10'
                    : isPreparing
                    ? 'border-blue-500/80 bg-blue-950/10'
                    : 'border-stone-800'
                }`}
              >
                <div>
                  {/* Ticket Header: Order #, Table #, Timer */}
                  <div className="flex justify-between items-start border-b border-stone-800/80 pb-3">
                    <div>
                      <div className="text-xl font-black text-stone-100 flex items-center">
                        <span className="text-amber-500 ml-1">#</span>
                        {toPersianDigits(item.order_number)}
                        <span className="text-xs font-semibold text-stone-400 mr-2 bg-stone-900 px-2 py-0.5 rounded-md">
                          میز {toPersianDigits(item.table_number)}
                        </span>
                      </div>
                    </div>

                    <div className="text-left">
                      <div
                        className={`text-xs font-bold flex items-center justify-end ${
                          isDelayed ? 'text-rose-400' : 'text-stone-400'
                        }`}
                      >
                        <Clock className="w-3.5 h-3.5 ml-1" />
                        {formatMinutes(item.elapsed_minutes)}
                      </div>
                      <div className="text-[10px] text-stone-500 mt-0.5">
                        هدف: {toPersianDigits(item.target_prep_time_minutes)} دقیقه
                      </div>
                    </div>
                  </div>

                  {/* Delayed Warning */}
                  {isDelayed && (
                    <div className="mt-2.5 p-1.5 rounded-lg bg-rose-950/60 border border-rose-800/60 text-rose-300 text-[11px] font-semibold flex items-center justify-center">
                      <AlertTriangle className="w-3.5 h-3.5 ml-1 text-rose-400" />
                      تاخیر در آماده‌سازی (بیش از زمان استاندارد)
                    </div>
                  )}

                  {/* Item Content */}
                  <div className="py-4 space-y-2">
                    <div className="flex items-start justify-between">
                      <span className="text-lg font-bold text-stone-100 leading-tight">
                        {item.menu_item_name_fa}
                      </span>
                      <span className="text-xl font-black text-amber-400 bg-amber-950/40 border border-amber-800/40 px-2.5 py-0.5 rounded-lg mr-2 shrink-0">
                        {toPersianDigits(item.quantity)}×
                      </span>
                    </div>

                    {item.modifiers && (
                      <div className="p-2 rounded-lg bg-stone-900/90 border border-stone-800 text-xs text-amber-300 font-medium">
                        دستور ویژه: {item.modifiers}
                      </div>
                    )}
                  </div>
                </div>

                {/* Touch-Friendly Action Buttons */}
                <div className="pt-3 border-t border-stone-800/80">
                  {isPending && (
                    <button
                      type="button"
                      disabled={isItemLoading}
                      onClick={() => handleUpdateStatus(item, 'preparing')}
                      className="w-full py-3 px-4 rounded-xl text-xs font-bold text-white bg-blue-600 hover:bg-blue-500 active:scale-95 shadow-md shadow-blue-950 flex items-center justify-center transition-all disabled:opacity-50"
                    >
                      {isItemLoading ? (
                        <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin ml-2" />
                      ) : (
                        <Play className="w-4 h-4 ml-2 fill-current" />
                      )}
                      شروع آماده‌سازی
                    </button>
                  )}

                  {isPreparing && (
                    <button
                      type="button"
                      disabled={isItemLoading}
                      onClick={() => handleUpdateStatus(item, 'ready')}
                      className="w-full py-3 px-4 rounded-xl text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-500 active:scale-95 shadow-md shadow-emerald-950 flex items-center justify-center transition-all disabled:opacity-50"
                    >
                      {isItemLoading ? (
                        <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin ml-2" />
                      ) : (
                        <CheckCircle2 className="w-4 h-4 ml-2" />
                      )}
                      علامت‌گذاری به عنوان آماده تحویل
                    </button>
                  )}

                  {item.status?.toLowerCase() === 'ready' && (
                    <div className="py-2.5 px-3 rounded-xl bg-emerald-950/40 border border-emerald-800/40 text-center text-xs text-emerald-300 font-semibold">
                      آماده تحویل به سالن‌کار
                    </div>
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
