import React, { useState } from 'react';
import { api } from '../../services/api';
import type { AIAnalystResponse, AnalyticalIntentEnum } from '../../types';
import { 
  Sparkles, 
  Send, 
  ShieldCheck, 
  Cpu, 
  CheckCircle, 
  Info,
  Clock,
  Layers,
  Store
} from 'lucide-react';

interface AIAnalystSectionProps {
  branchId?: string;
}

export const AIAnalystSection: React.FC<AIAnalystSectionProps> = ({ branchId }) => {
  const [intent, setIntent] = useState<AnalyticalIntentEnum>('SHIFT_SUMMARY');
  const [question, setQuestion] = useState<string>('');
  const [result, setResult] = useState<AIAnalystResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const INTENTS: Array<{ id: AnalyticalIntentEnum; title: string; desc: string; icon: any }> = [
    {
      id: 'SHIFT_SUMMARY',
      title: 'خلاصه وضعیت شیفت',
      desc: 'بررسی شاخص‌های کلی عملکرد سالن، سفارشات تکمیل شده و راندمان کلی',
      icon: Clock,
    },
    {
      id: 'BOTTLENECK_STATION',
      title: 'شناسایی ایستگاه گلوگاه',
      desc: 'تحلیل زمان‌بندی بار اسپرسو، برو بار و آشپزخانه جهت کشف نقاط انسداد',
      icon: Layers,
    },
    {
      id: 'DELAYED_ITEMS',
      title: 'آیتم‌های دارای تاخیر SLA',
      desc: 'استخراج آیتم‌های منو که بیش از زمان هدف استاندارد طول کشیده‌اند',
      icon: Info,
    },
    {
      id: 'BRANCH_COMPARISON',
      title: 'مقایسه تطبیقی شعب',
      desc: 'ارزیابی سرعت سرویس‌دهی و تاخیر شعب مختلف نسبت به یکدیگر',
      icon: Store,
    },
  ];

  const handleRunAnalysis = async (selectedIntent?: AnalyticalIntentEnum) => {
    const targetIntent = selectedIntent || intent;
    setLoading(true);
    setError(null);

    try {
      const response = await api.ai.explain({
        branch_id: branchId,
        intent: targetIntent,
        question: question.trim() || undefined,
      });
      setResult(response);
    } catch (err: any) {
      setError(err.message || 'خطا در اجرای تحلیل هوشمند');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-black text-stone-100 flex items-center">
          <Sparkles className="w-6 h-6 ml-2 text-purple-400" />
          تحلیلگر هوشمند عملیات شیفت (AI Analyst)
        </h1>
        <p className="text-xs text-stone-400 mt-1">
          محاسبه قطعی شاخص‌ها از پایگاه داده و تولید بینش عملیاتی با تایید حقایق آماری
        </p>
      </div>

      {/* Analytical Intent Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {INTENTS.map((item) => {
          const Icon = item.icon;
          const isSelected = intent === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => {
                setIntent(item.id);
                handleRunAnalysis(item.id);
              }}
              className={`p-4 rounded-2xl border text-right transition-all flex flex-col justify-between ${
                isSelected
                  ? 'bg-purple-950/40 border-purple-600 ring-2 ring-purple-500/20 shadow-lg'
                  : 'bg-stone-950 border-stone-800 hover:border-stone-700 hover:bg-stone-900/60'
              }`}
            >
              <div>
                <div
                  className={`w-9 h-9 rounded-xl flex items-center justify-center mb-3 ${
                    isSelected ? 'bg-purple-600 text-white' : 'bg-stone-900 text-stone-400'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                </div>
                <div className="font-bold text-sm text-stone-100">{item.title}</div>
                <div className="text-[11px] text-stone-400 mt-1 leading-relaxed">
                  {item.desc}
                </div>
              </div>

              <div className="mt-3 pt-2 border-t border-stone-800/60 flex items-center text-xs font-semibold text-purple-400">
                <span>اجرای تحلیل</span>
                <span className="mr-1">←</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Optional Custom Question Box */}
      <div className="p-4 rounded-2xl bg-stone-950 border border-stone-800 flex items-center gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="پرسش اختصاصی تکمیلی از تحلیلگر (مثلا: پیشنهاد کاهش تاخیر باریستا)..."
          className="flex-1 bg-stone-900 border border-stone-800 rounded-xl px-4 py-2.5 text-xs text-stone-100 focus:outline-none focus:border-purple-500"
        />
        <button
          type="button"
          onClick={() => handleRunAnalysis()}
          disabled={loading}
          className="px-4 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold transition-all disabled:opacity-50 flex items-center shrink-0"
        >
          {loading ? (
            <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin ml-2" />
          ) : (
            <Send className="w-3.5 h-3.5 ml-2" />
          )}
          تحلیل پرسش
        </button>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-950/60 border border-rose-800/80 text-rose-200 text-xs">
          {error}
        </div>
      )}

      {/* Loading Indicator */}
      {loading && (
        <div className="p-12 text-center border border-stone-800 rounded-2xl bg-stone-950/50 space-y-3">
          <div className="w-8 h-8 border-3 border-purple-500/30 border-t-purple-500 rounded-full animate-spin mx-auto" />
          <div className="text-xs text-stone-400 font-medium">
            در حال تجمیع قطعی داده‌های سفارشات و استخراج تحلیل هوشمند...
          </div>
        </div>
      )}

      {/* Result Display */}
      {result && !loading && (
        <div className="space-y-4 animate-in fade-in duration-300">
          {/* Header Badge */}
          <div className="p-3 rounded-xl bg-stone-950 border border-stone-800 flex items-center justify-between">
            <div className="flex items-center space-x-2 space-x-reverse">
              <ShieldCheck className="w-4 h-4 text-emerald-400 ml-1.5" />
              <span className="text-xs font-semibold text-stone-300">
                منبع محاسبات: پایگاه داده عملیاتی PostgreSQL
              </span>
            </div>

            <div>
              {result.is_fallback ? (
                <span className="px-2.5 py-1 rounded-md text-[11px] font-bold bg-amber-950/80 text-amber-300 border border-amber-800/60 flex items-center">
                  <Cpu className="w-3.5 h-3.5 ml-1" />
                  موتور تحلیلی قطعی پشتیبان (Offline Fallback Engine)
                </span>
              ) : (
                <span className="px-2.5 py-1 rounded-md text-[11px] font-bold bg-purple-950/80 text-purple-300 border border-purple-800/60 flex items-center">
                  <Sparkles className="w-3.5 h-3.5 ml-1" />
                  تحلیل شناختی مبتنی بر مدل ({result.provider})
                </span>
              )}
            </div>
          </div>

          {/* Measured Facts (Deterministic Evidence) */}
          <div className="p-5 rounded-2xl bg-stone-950 border border-stone-800 space-y-3">
            <h3 className="text-xs font-bold text-stone-400 flex items-center">
              <CheckCircle className="w-4 h-4 ml-1.5 text-emerald-400" />
              شواهد و حقایق آماری اندازه‌گیری شده (Measured Facts):
            </h3>
            <ul className="space-y-1.5 mr-2">
              {result.measured_facts.map((fact, index) => (
                <li
                  key={index}
                  className="text-xs text-stone-200 flex items-start space-x-2 space-x-reverse"
                >
                  <span className="text-purple-400 font-bold ml-2">•</span>
                  <span>{fact}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Narrative Analysis */}
          <div className="p-5 rounded-2xl bg-stone-950 border border-stone-800 space-y-3">
            <h3 className="text-xs font-bold text-purple-400 flex items-center">
              <Sparkles className="w-4 h-4 ml-1.5" />
              تحلیل و توصیه‌های عملیاتی مدیر شیفت:
            </h3>
            <div className="text-xs text-stone-200 leading-relaxed whitespace-pre-line p-4 rounded-xl bg-stone-900 border border-stone-800/80 font-medium">
              {result.analysis_text}
            </div>
            <div className="text-[10px] text-stone-500">
              * نکته: تحلیل‌های هوش مصنوعی جنبه مشاوره داشته و تصمیم‌گیری نهایی همواره بر عهده سرپرست سالن است.
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
