import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import type { MenuCategoryOut, MenuItemOut, TableOut, OrderCreate, OrderItemCreate } from '../../types';
import { formatToman, getTableSectionLabel, toPersianDigits } from '../../utils/formatters';
import { X, Plus, Minus, Trash2, Utensils, CheckCircle2, AlertCircle } from 'lucide-react';

interface CreateOrderModalProps {
  branchId: string;
  isOpen: boolean;
  onClose: () => void;
  onOrderCreated: () => void;
}

interface CartItem extends OrderItemCreate {
  item: MenuItemOut;
}

export const CreateOrderModal: React.FC<CreateOrderModalProps> = ({
  branchId,
  isOpen,
  onClose,
  onOrderCreated,
}) => {
  const [tables, setTables] = useState<TableOut[]>([]);
  const [categories, setCategories] = useState<MenuCategoryOut[]>([]);
  const [selectedTableId, setSelectedTableId] = useState<string>('');
  const [selectedCategoryId, setSelectedCategoryId] = useState<string>('');
  const [cart, setCart] = useState<CartItem[]>([]);
  const [notes, setNotes] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !branchId) return;

    async function loadData() {
      setError(null);
      try {
        const [tablesData, categoriesData] = await Promise.all([
          api.restaurants.getTables(branchId),
          api.menu.getCategories(),
        ]);
        setTables(tablesData);
        setCategories(categoriesData);
        if (categoriesData.length > 0) {
          setSelectedCategoryId(categoriesData[0].id);
        }
      } catch (err: any) {
        setError(err.message || 'خطا در دریافت اطلاعات میزها و منو');
      }
    }

    loadData();
    setCart([]);
    setNotes('');
    setSelectedTableId('');
  }, [isOpen, branchId]);

  if (!isOpen) return null;

  const currentCategory = categories.find((c) => c.id === selectedCategoryId) || categories[0];

  const handleAddToCart = (menuItem: MenuItemOut) => {
    setCart((prev) => {
      const existing = prev.find((i) => i.menu_item_id === menuItem.id);
      if (existing) {
        return prev.map((i) =>
          i.menu_item_id === menuItem.id ? { ...i, quantity: i.quantity + 1 } : i
        );
      }
      return [...prev, { menu_item_id: menuItem.id, quantity: 1, item: menuItem }];
    });
  };

  const handleUpdateQuantity = (itemId: string, delta: number) => {
    setCart((prev) =>
      prev
        .map((i) => {
          if (i.menu_item_id === itemId) {
            const newQty = i.quantity + delta;
            return newQty > 0 ? { ...i, quantity: newQty } : null;
          }
          return i;
        })
        .filter(Boolean) as CartItem[]
    );
  };

  const handleUpdateModifiers = (itemId: string, modifiers: string) => {
    setCart((prev) =>
      prev.map((i) => (i.menu_item_id === itemId ? { ...i, modifiers } : i))
    );
  };

  const calculateTotal = () => {
    return cart.reduce((sum, item) => sum + item.quantity * item.item.price_toman, 0);
  };

  const handleSubmit = async () => {
    if (!selectedTableId) {
      setError('لطفا شماره میز را انتخاب نمایید.');
      return;
    }
    if (cart.length === 0) {
      setError('حداقل یک آیتم برای ثبت سفارش انتخاب نمایید.');
      return;
    }

    setSubmitting(true);
    setError(null);

    const payload: OrderCreate = {
      branch_id: branchId,
      table_id: selectedTableId,
      notes: notes.trim() || undefined,
      items: cart.map((i) => ({
        menu_item_id: i.menu_item_id,
        quantity: i.quantity,
        modifiers: i.modifiers?.trim() || undefined,
      })),
    };

    try {
      await api.orders.create(payload);
      onOrderCreated();
      onClose();
    } catch (err: any) {
      setError(err.message || 'خطا در ثبت نهایی سفارش');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4">
      <div className="bg-stone-900 border border-stone-800 rounded-2xl w-full max-w-5xl h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-stone-800 flex items-center justify-between bg-stone-950">
          <div className="flex items-center space-x-2 space-x-reverse">
            <Utensils className="w-5 h-5 text-amber-500 ml-2" />
            <h3 className="text-lg font-bold text-stone-100">ثبت سفارش سالن جدید</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-stone-400 hover:text-stone-100 hover:bg-stone-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="m-4 mb-0 p-3 rounded-xl bg-rose-950/60 border border-rose-800/60 text-rose-200 text-sm flex items-center space-x-2 space-x-reverse">
            <AlertCircle className="w-4 h-4 ml-2 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Content Body: Split View (Menu on right, Cart on left in RTL) */}
        <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
          {/* Menu & Table Selector (2/3 width) */}
          <div className="flex-1 flex flex-col border-b lg:border-b-0 lg:border-l border-stone-800 overflow-y-auto p-4 sm:p-6 space-y-5">
            {/* Table Selection */}
            <div>
              <label className="block text-xs font-semibold text-stone-400 mb-2">
                انتخاب میز سالن:
              </label>
              <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2">
                {tables.map((t) => {
                  const isOccupied = !!t.active_order_id;
                  const isSelected = selectedTableId === t.id;
                  return (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => setSelectedTableId(t.id)}
                      className={`p-2.5 rounded-xl border text-center transition-all ${
                        isSelected
                          ? 'bg-amber-600 border-amber-500 text-white shadow-lg ring-2 ring-amber-400/30'
                          : isOccupied
                          ? 'bg-amber-950/20 border-amber-900/40 text-amber-300/80 hover:bg-amber-950/30'
                          : 'bg-stone-950 border-stone-800 text-stone-300 hover:bg-stone-800/80'
                      }`}
                    >
                      <div className="font-bold text-sm">میز {toPersianDigits(t.table_number)}</div>
                      <div className="text-[10px] text-stone-400 mt-0.5">
                        {getTableSectionLabel(t.section)}
                      </div>
                      {isOccupied && (
                        <div className="text-[9px] text-amber-400 mt-1 font-medium">سفارش باز</div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Category Tabs */}
            <div>
              <label className="block text-xs font-semibold text-stone-400 mb-2">
                دسته‌بندی‌های منو:
              </label>
              <div className="flex space-x-2 space-x-reverse overflow-x-auto pb-1">
                {categories.map((c) => (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => setSelectedCategoryId(c.id)}
                    className={`px-4 py-2 rounded-xl text-xs font-medium whitespace-nowrap transition-colors ${
                      selectedCategoryId === c.id
                        ? 'bg-amber-600 text-white shadow-sm'
                        : 'bg-stone-950 border border-stone-800 text-stone-300 hover:bg-stone-800'
                    }`}
                  >
                    {c.name}
                  </button>
                ))}
              </div>
            </div>

            {/* Menu Items Grid */}
            <div className="flex-1">
              <label className="block text-xs font-semibold text-stone-400 mb-2">
                آیتم‌های {currentCategory?.name || 'منو'}:
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {currentCategory?.items?.map((item) => (
                  <div
                    key={item.id}
                    className="p-3 rounded-xl bg-stone-950 border border-stone-800/80 hover:border-stone-700 flex flex-col justify-between transition-all"
                  >
                    <div>
                      <div className="flex justify-between items-start">
                        <span className="font-semibold text-sm text-stone-100">{item.name_fa}</span>
                        <span className="text-xs font-bold text-amber-400">
                          {formatToman(item.price_toman)}
                        </span>
                      </div>
                      {item.description && (
                        <p className="text-xs text-stone-400 mt-1 line-clamp-1">{item.description}</p>
                      )}
                    </div>
                    <div className="mt-3 flex justify-end">
                      <button
                        type="button"
                        onClick={() => handleAddToCart(item)}
                        className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium bg-stone-800 hover:bg-amber-600 hover:text-white text-stone-200 transition-colors"
                      >
                        <Plus className="w-3.5 h-3.5 ml-1" />
                        افزودن
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Cart & Final Submit (1/3 width) */}
          <div className="w-full lg:w-80 bg-stone-950 flex flex-col justify-between p-4 sm:p-6 overflow-hidden">
            <div className="flex-1 flex flex-col overflow-hidden">
              <div className="flex items-center justify-between pb-3 border-b border-stone-800">
                <span className="text-sm font-bold text-stone-100">فاکتور سفارش</span>
                <span className="text-xs text-stone-400">
                  {cart.length > 0 ? `${toPersianDigits(cart.length)} قلم` : 'خالی'}
                </span>
              </div>

              {/* Items List */}
              <div className="flex-1 overflow-y-auto py-3 space-y-3">
                {cart.length === 0 ? (
                  <div className="h-40 flex items-center justify-center text-xs text-stone-500">
                    هیچ آیتمی انتخاب نشده است
                  </div>
                ) : (
                  cart.map((cartItem) => (
                    <div
                      key={cartItem.menu_item_id}
                      className="p-2.5 rounded-xl bg-stone-900 border border-stone-800 text-xs space-y-2"
                    >
                      <div className="flex justify-between items-start">
                        <span className="font-medium text-stone-200">{cartItem.item.name_fa}</span>
                        <span className="text-amber-400 font-semibold">
                          {formatToman(cartItem.item.price_toman * cartItem.quantity)}
                        </span>
                      </div>

                      {/* Quantity Controls */}
                      <div className="flex items-center justify-between pt-1">
                        <div className="flex items-center space-x-2 space-x-reverse">
                          <button
                            type="button"
                            onClick={() => handleUpdateQuantity(cartItem.menu_item_id, -1)}
                            className="p-1 rounded bg-stone-800 hover:bg-stone-700 text-stone-300"
                          >
                            {cartItem.quantity === 1 ? <Trash2 className="w-3 h-3 text-rose-400" /> : <Minus className="w-3 h-3" />}
                          </button>
                          <span className="font-bold text-stone-100 px-1">
                            {toPersianDigits(cartItem.quantity)}
                          </span>
                          <button
                            type="button"
                            onClick={() => handleUpdateQuantity(cartItem.menu_item_id, 1)}
                            className="p-1 rounded bg-stone-800 hover:bg-stone-700 text-stone-300"
                          >
                            <Plus className="w-3 h-3" />
                          </button>
                        </div>

                        {/* Modifiers input */}
                        <input
                          type="text"
                          placeholder="یادداشت (کم‌شیرین و...)"
                          value={cartItem.modifiers || ''}
                          onChange={(e) => handleUpdateModifiers(cartItem.menu_item_id, e.target.value)}
                          className="w-28 text-[11px] px-2 py-1 rounded bg-stone-950 border border-stone-800 text-stone-200 focus:outline-none focus:border-amber-500"
                        />
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Order Notes */}
              <div className="pt-2">
                <input
                  type="text"
                  placeholder="یادداشت کلی سفارش..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full text-xs px-3 py-2 rounded-xl bg-stone-900 border border-stone-800 text-stone-200 focus:outline-none focus:border-amber-500"
                />
              </div>
            </div>

            {/* Bottom Actions */}
            <div className="pt-4 border-t border-stone-800 space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-xs text-stone-400">مجموع فاکتور:</span>
                <span className="text-base font-extrabold text-amber-400">
                  {formatToman(calculateTotal())}
                </span>
              </div>

              <button
                type="button"
                onClick={handleSubmit}
                disabled={submitting || cart.length === 0 || !selectedTableId}
                className="w-full py-3 px-4 rounded-xl text-sm font-bold text-white bg-amber-600 hover:bg-amber-500 disabled:opacity-50 transition-all flex items-center justify-center shadow-lg active:scale-95"
              >
                {submitting ? (
                  <span className="inline-flex items-center">
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin ml-2" />
                    در حال ارسال به آشپزخانه...
                  </span>
                ) : (
                  <span className="inline-flex items-center">
                    <CheckCircle2 className="w-4 h-4 ml-2" />
                    ارسال سفارش به آشپزخانه
                  </span>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
