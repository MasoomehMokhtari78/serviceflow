import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import type { OperationalMetricsOut } from '../../types';
import { 
  formatMinutes, 
  getStationTypeLabel, 
  toPersianDigits 
} from '../../utils/formatters';
import { 
  LayoutDashboard, 
  Clock, 
  CheckCircle2, 
  AlertTriangle, 
  TrendingUp, 
  RotateCw, 
  Store,
  Layers
} from 'lucide-react';

interface ManagerDashboardProps {
  branchId?: string;
}

export const ManagerDashboard: React.FC<ManagerDashboardProps> = ({ branchId }) => {
  const [metrics, setMetrics] = useState<OperationalMetricsOut | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = async (isBackground = false) => {
    if (!isBackground) setLoading(true);
    else setRefreshing(true);
    setError(null);

    try {
      const data = await api.metrics.getOperational(branchId, 24);
      setMetrics(data);
    } catch (err: any) {
      setError(err.message || 'خطا در محاسبه شاخص‌های عملیاتی');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, [branchId]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-stone-100 flex items-center">
            <LayoutDashboard className="w-6 h-6 ml-2 text-emerald-500" />
            داشبورد هوش عملیاتی شیفت
          </h1>
          <p className="text-xs text-stone-400 mt-1">
            محاسبه دقیق SLA آماده‌سازی، تحلیل گلوگاه ایستگاه‌ها و تاخیر سفارشات (۲۴ ساعت گذشته)
          </p>
        </div>

        <button
          onClick={() => fetchMetrics(true)}
          disabled={refreshing}
          className="inline-flex items-center px-3.5 py-2 rounded-xl bg-stone-900 border border-stone-800 text-stone-300 hover:text-white transition-colors text-xs font-semibold"
        >
          <RotateCw className={`w-4 h-4 ml-2 ${refreshing ? 'animate-spin text-emerald-500' : ''}`} />
          به‌روزرسانی آمار
        </button>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-950/60 border border-rose-800/80 text-rose-200 text-xs">
          {error}
        </div>
      )}

      {loading ? (
        <div className="h-64 flex flex-col items-center justify-center space-y-3">
          <div className="w-8 h-8 border-3 border-emerald-600/30 border-t-emerald-500 rounded-full animate-spin" />
          <span className="text-xs text-stone-400">در حال استخراج داده‌های آماری پایگاه داده...</span>
        </div>
      ) : metrics ? (
        <>
          {/* Key KPI Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 rounded-2xl bg-stone-950 border border-stone-800 flex items-center space-x-3 space-x-reverse">
              <div className="w-12 h-12 rounded-xl bg-amber-950/60 border border-amber-800/60 flex items-center justify-center text-amber-400">
                <Clock className="w-6 h-6" />
              </div>
              <div>
                <div className="text-xs text-stone-400 font-medium">سفارش‌های در جریان</div>
                <div className="text-2xl font-black text-stone-100 mt-0.5">
                  {toPersianDigits(metrics.active_orders)}
                </div>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-stone-950 border border-stone-800 flex items-center space-x-3 space-x-reverse">
              <div className="w-12 h-12 rounded-xl bg-emerald-950/60 border border-emerald-800/60 flex items-center justify-center text-emerald-400">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <div className="text-xs text-stone-400 font-medium">سفارش‌های تکمیل شده</div>
                <div className="text-2xl font-black text-stone-100 mt-0.5">
                  {toPersianDigits(metrics.completed_orders)}
                </div>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-stone-950 border border-stone-800 flex items-center space-x-3 space-x-reverse">
              <div className="w-12 h-12 rounded-xl bg-blue-950/60 border border-blue-800/60 flex items-center justify-center text-blue-400">
                <TrendingUp className="w-6 h-6" />
              </div>
              <div>
                <div className="text-xs text-stone-400 font-medium">میانگین زمان تحویل (Lead Time)</div>
                <div className="text-2xl font-black text-stone-100 mt-0.5">
                  {formatMinutes(metrics.avg_order_lead_time_minutes)}
                </div>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-stone-950 border border-stone-800 flex items-center space-x-3 space-x-reverse">
              <div className="w-12 h-12 rounded-xl bg-rose-950/60 border border-rose-800/60 flex items-center justify-center text-rose-400">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <div className="text-xs text-stone-400 font-medium">کل سفارشات ثبت شده</div>
                <div className="text-2xl font-black text-stone-100 mt-0.5">
                  {toPersianDigits(metrics.total_orders)}
                </div>
              </div>
            </div>
          </div>

          {/* Station Performance Section */}
          <div className="p-5 rounded-2xl bg-stone-950 border border-stone-800 space-y-4">
            <h3 className="text-sm font-bold text-stone-100 flex items-center">
              <Layers className="w-4 h-4 ml-2 text-amber-500" />
              عملکرد و تاخیر ایستگاه‌های کاری (KDS Stations)
            </h3>

            <div className="overflow-x-auto">
              <table className="w-full text-right text-xs">
                <thead>
                  <tr className="border-b border-stone-800 text-stone-400 pb-2">
                    <th className="py-2 font-semibold">ایستگاه</th>
                    <th className="py-2 font-semibold">نوع بخش</th>
                    <th className="py-2 font-semibold">زمان استاندارد</th>
                    <th className="py-2 font-semibold">کل اقلام</th>
                    <th className="py-2 font-semibold">اقلام با تاخیر</th>
                    <th className="py-2 font-semibold">درصد تاخیر SLA</th>
                    <th className="py-2 font-semibold">میانگین زمان آماده‌سازی</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-800/60 text-stone-200">
                  {metrics.stations.map((st) => (
                    <tr key={st.station_id} className="hover:bg-stone-900/50">
                      <td className="py-3 font-bold text-stone-100">{st.station_name}</td>
                      <td className="py-3 text-stone-400">{getStationTypeLabel(st.station_type)}</td>
                      <td className="py-3 font-medium">{toPersianDigits(st.target_prep_time_minutes)} دقیقه</td>
                      <td className="py-3 font-medium">{toPersianDigits(st.total_items_count)}</td>
                      <td className="py-3 font-semibold text-rose-400">{toPersianDigits(st.delayed_items_count)}</td>
                      <td className="py-3">
                        <span
                          className={`px-2 py-0.5 rounded font-bold ${
                            st.delay_rate_percentage > 25
                              ? 'bg-rose-950/80 text-rose-400 border border-rose-800/60'
                              : 'bg-stone-800 text-stone-300'
                          }`}
                        >
                          {toPersianDigits(st.delay_rate_percentage)}٪
                        </span>
                      </td>
                      <td className="py-3 font-bold text-amber-400">
                        {formatMinutes(st.avg_turnaround_minutes)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Two-Column Grid: Top Delayed Dishes & Branch Comparison */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Top Delayed Dishes */}
            <div className="p-5 rounded-2xl bg-stone-950 border border-stone-800 space-y-3">
              <h3 className="text-sm font-bold text-stone-100 flex items-center">
                <AlertTriangle className="w-4 h-4 ml-2 text-rose-500" />
                آیتم‌های دارای بیشترین تاخیر در منو
              </h3>
              {metrics.top_delayed_dishes.length === 0 ? (
                <div className="py-6 text-center text-xs text-stone-500">
                  هیچ آیتمی با تاخیر ثبت نشده است.
                </div>
              ) : (
                <div className="space-y-2">
                  {metrics.top_delayed_dishes.map((dish) => (
                    <div
                      key={dish.menu_item_id}
                      className="p-3 rounded-xl bg-stone-900 border border-stone-800/80 flex justify-between items-center text-xs"
                    >
                      <div>
                        <div className="font-bold text-stone-100">{dish.name_fa}</div>
                        <div className="text-[10px] text-stone-400 mt-0.5">
                          بخش: {getStationTypeLabel(dish.station_type)}
                        </div>
                      </div>
                      <div className="text-left">
                        <span className="px-2 py-1 rounded bg-rose-950/60 border border-rose-800/60 text-rose-400 font-bold">
                          {toPersianDigits(dish.delayed_count)} تاخیر
                        </span>
                        <div className="text-[10px] text-stone-500 mt-1">
                          از {toPersianDigits(dish.total_ordered_count)} سفارش
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Branch Comparison */}
            <div className="p-5 rounded-2xl bg-stone-950 border border-stone-800 space-y-3">
              <h3 className="text-sm font-bold text-stone-100 flex items-center">
                <Store className="w-4 h-4 ml-2 text-blue-500" />
                مقایسه تطبیقی عملکرد شعب مجموعه
              </h3>
              {metrics.branch_comparison.length === 0 ? (
                <div className="py-6 text-center text-xs text-stone-500">
                  اطلاعات سایر شعب در دسترس نیست.
                </div>
              ) : (
                <div className="space-y-2">
                  {metrics.branch_comparison.map((b) => (
                    <div
                      key={b.branch_id}
                      className="p-3 rounded-xl bg-stone-900 border border-stone-800/80 flex justify-between items-center text-xs"
                    >
                      <div>
                        <div className="font-bold text-stone-100">{b.branch_name}</div>
                        <div className="text-[10px] text-stone-400 mt-0.5">
                          {toPersianDigits(b.completed_orders_count)} سفارش تکمیل شده
                        </div>
                      </div>
                      <div className="text-left space-y-1">
                        <div className="font-bold text-amber-400">
                          {formatMinutes(b.avg_order_lead_time_minutes)}
                        </div>
                        <div className="text-[10px] text-rose-400 font-medium">
                          {toPersianDigits(b.delayed_orders_percentage)}٪ تاخیر
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
};
