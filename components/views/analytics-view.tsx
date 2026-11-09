'use client';

import React, { useState } from 'react';
import {
  TrendingUp,
  BarChart2,
  Calendar,
  Zap,
  Activity,
  ArrowUpRight,
  ShieldCheck,
} from 'lucide-react';

export const AnalyticsView: React.FC = () => {
  const [timeFilter, setTimeFilter] = useState<'minggu' | 'bulan' | 'tahun'>('minggu');

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Title */}
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">Analytics & Usage</h1>
        <p className="text-xs text-slate-500">Statistik aktivitas AI, efisiensi tugas, dan konsumsi kuota</p>
      </div>

      {/* Time Filter Tabs (Sheet 1) */}
      <div className="flex items-center gap-1 p-1 bg-white rounded-2xl border border-slate-200 shadow-2xs">
        {(['minggu', 'bulan', 'tahun'] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTimeFilter(t)}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-xl capitalize transition ${
              timeFilter === t
                ? 'bg-red-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Metric Card: Total Aktivitas 12.5K (Exact from Sheet 1) */}
      <div className="p-5 rounded-3xl bg-white border border-slate-100 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400 font-semibold block uppercase tracking-wider">
              Total Aktivitas
            </span>
            <div className="flex items-baseline gap-2 mt-0.5">
              <span className="text-3xl font-black text-slate-900 tracking-tight">12.5K</span>
              <span className="text-xs font-bold text-emerald-600 flex items-center gap-0.5">
                <ArrowUpRight className="w-3.5 h-3.5" />
                <span>+12%</span>
              </span>
            </div>
          </div>
          <div className="w-10 h-10 rounded-2xl bg-red-50 text-red-600 flex items-center justify-center">
            <Activity className="w-5 h-5" />
          </div>
        </div>

        {/* Visual SVG Wave Chart (matching Sheet 1 red line with gradient fill) */}
        <div className="pt-2">
          <svg viewBox="0 0 400 120" className="w-full h-28 overflow-visible">
            <defs>
              <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#E11D48" stopOpacity="0.35" />
                <stop offset="100%" stopColor="#E11D48" stopOpacity="0.0" />
              </linearGradient>
            </defs>
            {/* Area Fill */}
            <path
              d="M 0,90 Q 50,40 100,70 T 200,30 T 300,55 T 400,20 L 400,120 L 0,120 Z"
              fill="url(#chartGradient)"
            />
            {/* Stroke Line */}
            <path
              d="M 0,90 Q 50,40 100,70 T 200,30 T 300,55 T 400,20"
              fill="none"
              stroke="#E11D48"
              strokeWidth="3.5"
              strokeLinecap="round"
            />
            {/* Peak Indicator Dot */}
            <circle cx="200" cy="30" r="5" fill="#E11D48" stroke="#FFFFFF" strokeWidth="2" />
            <circle cx="400" cy="20" r="5" fill="#E11D48" stroke="#FFFFFF" strokeWidth="2" />
          </svg>
          <div className="flex justify-between text-[10px] text-slate-400 font-medium pt-1 px-1">
            <span>Sen</span>
            <span>Sel</span>
            <span>Rab</span>
            <span>Kam</span>
            <span>Jum</span>
            <span>Sab</span>
            <span>Min</span>
          </div>
        </div>
      </div>

      {/* Feature Breakdown (From Sheet 4 & Master PRD) */}
      <div className="bg-white rounded-3xl p-4 border border-slate-100 shadow-xs space-y-3">
        <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
          Fitur AI Terfavorit
        </h2>

        <div className="space-y-2.5">
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="font-semibold text-slate-700">Chat AI & Assistant</span>
              <span className="font-bold text-slate-900">38% (4.8K req)</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-2">
              <div className="bg-red-600 h-2 rounded-full" style={{ width: '38%' }} />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="font-semibold text-slate-700">Create Studio</span>
              <span className="font-bold text-slate-900">24% (3.0K req)</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-2">
              <div className="bg-amber-500 h-2 rounded-full" style={{ width: '24%' }} />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="font-semibold text-slate-700">Research Agent</span>
              <span className="font-bold text-slate-900">18% (2.2K req)</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-2">
              <div className="bg-blue-600 h-2 rounded-full" style={{ width: '18%' }} />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="font-semibold text-slate-700">Data & Code Runner</span>
              <span className="font-bold text-slate-900">20% (2.5K req)</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-2">
              <div className="bg-emerald-600 h-2 rounded-full" style={{ width: '20%' }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
