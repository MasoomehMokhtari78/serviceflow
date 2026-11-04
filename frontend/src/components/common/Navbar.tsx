import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { 
  Coffee, 
  UtensilsCrossed, 
  LayoutDashboard, 
  LogOut, 
  PlusCircle, 
  Sparkles, 
  Store
} from 'lucide-react';

interface NavbarProps {
  currentTab: string;
  onTabChange: (tab: string) => void;
  onOpenCreateOrder?: () => void;
  branchName?: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  onTabChange,
  onOpenCreateOrder,
  branchName
}) => {
  const { user, restaurantName, logout } = useAuth();
  const role = user?.role?.toLowerCase();

  const getRoleBadge = () => {
    switch (role) {
      case 'waiter':
        return { label: 'گارسون / سالن‌کار', bg: 'bg-amber-900/40 text-amber-300 border-amber-700/50' };
      case 'kitchen':
        return { label: 'آشپزخانه و بار (KDS)', bg: 'bg-blue-900/40 text-blue-300 border-blue-700/50' };
      case 'manager':
        return { label: 'مدیر مجموعه', bg: 'bg-emerald-900/40 text-emerald-300 border-emerald-700/50' };
      default:
        return { label: user?.role || '', bg: 'bg-stone-800 text-stone-300 border-stone-700' };
    }
  };

  const badge = getRoleBadge();

  return (
    <header className="sticky top-0 z-30 bg-stone-900/95 backdrop-blur-md border-b border-stone-800 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand & Context */}
          <div className="flex items-center space-x-3 space-x-reverse">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-600 to-amber-800 flex items-center justify-center text-white shadow-md shadow-amber-950">
              <Coffee className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2 space-x-reverse">
                <span className="font-extrabold text-lg text-stone-100 tracking-tight">سرویس‌فلو</span>
                <span className="text-xs px-2 py-0.5 rounded bg-stone-800 text-stone-400 font-medium">ServiceFlow</span>
              </div>
              <div className="flex items-center text-xs text-stone-400 space-x-2 space-x-reverse">
                <span className="font-medium text-amber-400/90">{restaurantName || 'مجموعه کاریز'}</span>
                {branchName && (
                  <>
                    <span className="text-stone-600">•</span>
                    <span className="flex items-center">
                      <Store className="w-3 h-3 ml-1 text-stone-400" />
                      {branchName}
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Role Navigation */}
          <nav className="flex items-center space-x-1 sm:space-x-2 space-x-reverse">
            {(role === 'waiter' || role === 'manager') && (
              <button
                onClick={() => onTabChange('orders')}
                className={`px-3 py-2 rounded-lg text-sm font-medium flex items-center transition-colors ${
                  currentTab === 'orders'
                    ? 'bg-amber-600 text-white shadow'
                    : 'text-stone-300 hover:text-white hover:bg-stone-800'
                }`}
              >
                <UtensilsCrossed className="w-4 h-4 ml-1.5" />
                سفارش‌های فعال
              </button>
            )}

            {(role === 'kitchen' || role === 'manager') && (
              <button
                onClick={() => onTabChange('kitchen')}
                className={`px-3 py-2 rounded-lg text-sm font-medium flex items-center transition-colors ${
                  currentTab === 'kitchen'
                    ? 'bg-blue-600 text-white shadow'
                    : 'text-stone-300 hover:text-white hover:bg-stone-800'
                }`}
              >
                <Coffee className="w-4 h-4 ml-1.5" />
                صف KDS آشپزخانه
              </button>
            )}

            {role === 'manager' && (
              <>
                <button
                  onClick={() => onTabChange('metrics')}
                  className={`px-3 py-2 rounded-lg text-sm font-medium flex items-center transition-colors ${
                    currentTab === 'metrics'
                      ? 'bg-emerald-600 text-white shadow'
                      : 'text-stone-300 hover:text-white hover:bg-stone-800'
                  }`}
                >
                  <LayoutDashboard className="w-4 h-4 ml-1.5" />
                  داشبورد شیفت
                </button>
                <button
                  onClick={() => onTabChange('ai')}
                  className={`px-3 py-2 rounded-lg text-sm font-medium flex items-center transition-colors ${
                    currentTab === 'ai'
                      ? 'bg-purple-600 text-white shadow'
                      : 'text-stone-300 hover:text-white hover:bg-stone-800'
                  }`}
                >
                  <Sparkles className="w-4 h-4 ml-1.5" />
                  تحلیلگر AI
                </button>
              </>
            )}
          </nav>

          {/* User & Actions */}
          <div className="flex items-center space-x-3 space-x-reverse">
            {onOpenCreateOrder && (user?.role === 'WAITER' || user?.role === 'MANAGER') && (
              <button
                onClick={onOpenCreateOrder}
                className="hidden sm:inline-flex items-center px-3.5 py-1.5 rounded-lg text-sm font-medium bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-500 hover:to-amber-600 text-white shadow-md shadow-amber-950/50 transition-all active:scale-95"
              >
                <PlusCircle className="w-4 h-4 ml-1.5" />
                سفارش جدید
              </button>
            )}

            <div className="flex items-center space-x-2 space-x-reverse pl-2 border-l border-stone-800">
              <div className="text-left hidden md:block">
                <div className="text-xs font-medium text-stone-200">{user?.full_name}</div>
                <div className={`text-[10px] px-1.5 py-0.5 rounded border inline-block ${badge.bg}`}>
                  {badge.label}
                </div>
              </div>
              <button
                onClick={logout}
                title="خروج از حساب"
                className="p-2 rounded-lg text-stone-400 hover:text-rose-400 hover:bg-rose-950/30 transition-colors"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
