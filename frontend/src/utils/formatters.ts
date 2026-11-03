import type { OrderItemStatusEnum, OrderStatusEnum, StationTypeEnum, TableSectionEnum } from '../types';

export function toPersianDigits(n: number | string): string {
  const persianDigits = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
  return String(n).replace(/[0-9]/g, (w) => persianDigits[+w]);
}

export function formatToman(amount: number): string {
  if (amount === null || amount === undefined) return '۰ تومان';
  const formatted = new Intl.NumberFormat('fa-IR').format(amount);
  return `${formatted} تومان`;
}

export function formatMinutes(minutes: number | null | undefined): string {
  if (minutes === null || minutes === undefined) return '۰ دقیقه';
  return `${toPersianDigits(Math.round(minutes))} دقیقه`;
}

export function formatTime(isoString: string): string {
  try {
    const d = new Date(isoString);
    const hours = d.getHours().toString().padStart(2, '0');
    const mins = d.getMinutes().toString().padStart(2, '0');
    return toPersianDigits(`${hours}:${mins}`);
  } catch {
    return '--:--';
  }
}

export function getOrderStatusInfo(status: OrderStatusEnum): { label: string; bg: string; text: string; border: string } {
  const s = String(status || '').toLowerCase();
  switch (s) {
    case 'submitted':
      return { label: 'ثبت شده', bg: 'bg-amber-950/40', text: 'text-amber-400', border: 'border-amber-600/40' };
    case 'in_progress':
      return { label: 'در حال آماده‌سازی', bg: 'bg-blue-950/40', text: 'text-blue-400', border: 'border-blue-600/40' };
    case 'ready_for_service':
      return { label: 'آماده سرو 🔔', bg: 'bg-emerald-950/40', text: 'text-emerald-400', border: 'border-emerald-500/60' };
    case 'served':
      return { label: 'سرو شده', bg: 'bg-stone-800/40', text: 'text-stone-400', border: 'border-stone-700/40' };
    case 'cancelled':
      return { label: 'لغو شده', bg: 'bg-rose-950/40', text: 'text-rose-400', border: 'border-rose-700/40' };
    default:
      return { label: status, bg: 'bg-stone-800', text: 'text-stone-300', border: 'border-stone-700' };
  }
}

export function getItemStatusInfo(status: OrderItemStatusEnum): { label: string; bg: string; text: string; border: string } {
  const s = String(status || '').toLowerCase();
  switch (s) {
    case 'pending':
      return { label: 'در انتظار', bg: 'bg-amber-950/50', text: 'text-amber-400', border: 'border-amber-700/40' };
    case 'preparing':
      return { label: 'در حال پخت / آماده‌سازی', bg: 'bg-blue-950/50', text: 'text-blue-400', border: 'border-blue-600/40' };
    case 'ready':
      return { label: 'آماده تحویل', bg: 'bg-emerald-950/50', text: 'text-emerald-300', border: 'border-emerald-500/50' };
    case 'served':
      return { label: 'سرو شده', bg: 'bg-stone-800/50', text: 'text-stone-400', border: 'border-stone-700/50' };
    case 'cancelled':
      return { label: 'لغو شده', bg: 'bg-rose-950/50', text: 'text-rose-400', border: 'border-rose-700/50' };
    default:
      return { label: status, bg: 'bg-stone-800', text: 'text-stone-300', border: 'border-stone-700' };
  }
}

export function getStationTypeLabel(type: StationTypeEnum): string {
  const t = String(type || '').toLowerCase();
  switch (t) {
    case 'barista':
      return 'بار اسپرسو (گرم)';
    case 'brew_bar':
      return 'برو بار (دمی)';
    case 'cold_bar':
      return 'بار سرد و ماکتیل';
    case 'kitchen':
      return 'آشپزخانه و غذا';
    default:
      return type;
  }
}

export function getTableSectionLabel(section: TableSectionEnum): string {
  const sec = String(section || '').toLowerCase();
  switch (sec) {
    case 'main_hall':
      return 'سالن اصلی';
    case 'terrace':
      return 'تراس';
    case 'vip':
      return 'بخش VIP';
    case 'bar':
      return 'میز بار';
    default:
      return section;
  }
}
