import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Coffee, Lock, Mail, Store, AlertCircle, ArrowLeft } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const [restaurantSlug, setRestaurantSlug] = useState('kariz-cafe');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await login({
        restaurant_slug: restaurantSlug.trim(),
        email: email.trim(),
        password: password,
      });
    } catch (err: any) {
      setError(err.message || 'ورود ناموفق بود. لطفا اطلاعات را بررسی کنید.');
    } finally {
      setLoading(false);
    }
  };

  const setDemoCredentials = (slug: string, demoEmail: string, demoPass: string) => {
    setRestaurantSlug(slug);
    setEmail(demoEmail);
    setPassword(demoPass);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-stone-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex w-16 h-16 rounded-2xl bg-gradient-to-tr from-amber-600 to-amber-700 items-center justify-center text-white shadow-xl shadow-amber-950 mb-4 ring-4 ring-amber-500/20">
          <Coffee className="w-9 h-9" />
        </div>
        <h2 className="text-3xl font-extrabold text-stone-100 tracking-tight">
          سرویس‌فلو
        </h2>
        <p className="mt-2 text-sm text-stone-400">
          سامانه یکپارچه مدیریت سفارشات و آشپزخانه شعب کافه رستوران
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4">
        <div className="bg-stone-900 py-8 px-6 shadow-2xl rounded-2xl border border-stone-800 sm:px-10">
          {error && (
            <div className="mb-6 p-3.5 rounded-xl bg-rose-950/50 border border-rose-800/60 text-rose-200 text-sm flex items-start space-x-2 space-x-reverse">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5 ml-2" />
              <span>{error}</span>
            </div>
          )}

          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs font-medium text-stone-300 mb-1.5">
                شناسه مجموعه رستورانی (Restaurant Slug)
              </label>
              <div className="relative rounded-xl shadow-sm">
                <div className="absolute inset-y-0 right-0 pr-3.5 flex items-center pointer-events-none text-stone-500">
                  <Store className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  required
                  value={restaurantSlug}
                  onChange={(e) => setRestaurantSlug(e.target.value)}
                  placeholder="مثال: kariz"
                  dir="ltr"
                  className="block w-full pr-10 pl-3 py-2.5 bg-stone-950 border border-stone-800 rounded-xl text-stone-100 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all placeholder:text-stone-600"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-stone-300 mb-1.5">
                پست الکترونیکی کاربری (Email)
              </label>
              <div className="relative rounded-xl shadow-sm">
                <div className="absolute inset-y-0 right-0 pr-3.5 flex items-center pointer-events-none text-stone-500">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@kariz.ir"
                  dir="ltr"
                  className="block w-full pr-10 pl-3 py-2.5 bg-stone-950 border border-stone-800 rounded-xl text-stone-100 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all placeholder:text-stone-600"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-stone-300 mb-1.5">
                رمز عبور (Password)
              </label>
              <div className="relative rounded-xl shadow-sm">
                <div className="absolute inset-y-0 right-0 pr-3.5 flex items-center pointer-events-none text-stone-500">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  dir="ltr"
                  className="block w-full pr-10 pl-3 py-2.5 bg-stone-950 border border-stone-800 rounded-xl text-stone-100 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all placeholder:text-stone-600"
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-xl shadow-md text-sm font-semibold text-white bg-amber-600 hover:bg-amber-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-500 disabled:opacity-50 transition-all active:scale-[0.98]"
              >
                {loading ? (
                  <span className="inline-flex items-center">
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin ml-2" />
                    در حال احراز هویت...
                  </span>
                ) : (
                  <span className="inline-flex items-center">
                    ورود به سامانه
                    <ArrowLeft className="w-4 h-4 mr-2" />
                  </span>
                )}
              </button>
            </div>
          </form>

          {/* Quick Demo Credentials Helper */}
          <div className="mt-8 pt-6 border-t border-stone-800">
            <p className="text-xs font-semibold text-stone-400 mb-3 text-center">
              حساب‌های کاربری تایید شده آزمایشی (جهت ارزیابی سریع):
            </p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                type="button"
                onClick={() => setDemoCredentials('kariz-cafe', 'waiter.enghelab@kariz.ir', 'password123')}
                className="p-2 rounded-lg bg-stone-800/80 hover:bg-stone-800 text-stone-200 border border-stone-700/60 text-right transition-colors"
              >
                <div className="font-medium text-amber-400">گارسون انقلاب</div>
                <div className="text-[10px] text-stone-400">ثبت و پیگیری سفارش</div>
              </button>
              <button
                type="button"
                onClick={() => setDemoCredentials('kariz-cafe', 'barista.enghelab@kariz.ir', 'password123')}
                className="p-2 rounded-lg bg-stone-800/80 hover:bg-stone-800 text-stone-200 border border-stone-700/60 text-right transition-colors"
              >
                <div className="font-medium text-blue-400">باریستا انقلاب</div>
                <div className="text-[10px] text-stone-400">صف KDS بار اسپرسو</div>
              </button>
              <button
                type="button"
                onClick={() => setDemoCredentials('kariz-cafe', 'chef.enghelab@kariz.ir', 'password123')}
                className="p-2 rounded-lg bg-stone-800/80 hover:bg-stone-800 text-stone-200 border border-stone-700/60 text-right transition-colors"
              >
                <div className="font-medium text-orange-400">سرآشپز انقلاب</div>
                <div className="text-[10px] text-stone-400">صف KDS غذا و پخت</div>
              </button>
              <button
                type="button"
                onClick={() => setDemoCredentials('kariz-cafe', 'manager@kariz.ir', 'password123')}
                className="p-2 rounded-lg bg-stone-800/80 hover:bg-stone-800 text-stone-200 border border-stone-700/60 text-right transition-colors"
              >
                <div className="font-medium text-emerald-400">مدیر کاریز</div>
                <div className="text-[10px] text-stone-400">داشبورد و هوش AI</div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
