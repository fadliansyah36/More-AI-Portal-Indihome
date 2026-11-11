'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { customerApi, CustomerUsageRecord } from '@/lib/api/client';
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
  const [usage, setUsage] = useState<CustomerUsageRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    customerApi.usage(100).then((rows) => { if (active) setUsage(rows); })
      .catch((err) => { if (active) setError(err instanceof Error ? err.message : 'Data analytics tidak tersedia.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const periodUsage = useMemo(() => {
    const now = Date.now();
    const duration = timeFilter === 'minggu' ? 7 : timeFilter === 'bulan' ? 30 : 365;
    return usage.filter((row) => {
      const created = new Date(row.created_at).getTime();
      return Number.isFinite(created) && created >= now - duration * 86400000;
    });
  }, [usage, timeFilter]);
  const modelBreakdown = useMemo(() => {
    const grouped = new Map<string, { requests: number; tokens: number }>();
    for (const row of periodUsage) {
      const key = row.model_key || 'model_tidak_diketahui';
      const current = grouped.get(key) || { requests: 0, tokens: 0 };
      current.requests += 1;
      current.tokens += row.input_tokens + row.output_tokens;
      grouped.set(key, current);
    }
    return [...grouped.entries()].map(([model, metrics]) => ({ model, ...metrics })).sort((a, b) => b.requests - a.requests);
  }, [periodUsage]);
  const totalTokens = periodUsage.reduce((sum, row) => sum + row.input_tokens + row.output_tokens, 0);
  const totalCost = periodUsage.reduce((sum, row) => sum + Number(row.actual_cost ?? row.estimated_cost ?? 0), 0);
  const successfulRuns = periodUsage.filter((row) => row.status === 'succeeded' || row.status === 'completed').length;

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

      {/* Metric Card: Total Aktivitas {loading ? "—" : periodUsage.length.toLocaleString("id-ID")} (Exact from Sheet 1) */}
      <div className="p-5 rounded-3xl bg-white border border-slate-100 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400 font-semibold block uppercase tracking-wider">
              Aktivitas AI · {timeFilter}
            </span>
            <div className="flex items-baseline gap-2 mt-0.5">
              <span className="text-3xl font-black text-slate-900 tracking-tight">{loading ? "—" : periodUsage.length.toLocaleString("id-ID")}</span>
              <span className="text-xs font-bold text-emerald-600 flex items-center gap-0.5">
                <ArrowUpRight className="w-3.5 h-3.5" />
                <span>rekaman API</span>
              </span>
            </div>
          </div>
          <div className="w-10 h-10 rounded-2xl bg-red-50 text-red-600 flex items-center justify-center">
            <Activity className="w-5 h-5" />
          </div>
        </div>

        {/* Visual SVG Wave Chart (matching Sheet 1 red line with gradient fill) */}
        <div className="pt-2">{error ? <p className="text-xs text-amber-700">{error}</p> : <p className="text-xs text-slate-500">{loading ? "Memuat data penggunaan…" : `${totalTokens.toLocaleString("id-ID")} token diproses · ${successfulRuns} penggunaan berhasil · biaya tercatat ${totalCost.toLocaleString("id-ID")}`}</p>}
          <div className="mt-3 rounded-xl bg-slate-50 border border-slate-100 p-3 text-[11px] text-slate-500">Grafik tren akan ditampilkan setelah API menyediakan agregasi historis yang tervalidasi. Angka di atas berasal dari catatan penggunaan akun.</div>
        </div>
      </div>

      <div className="space-y-3 rounded-3xl border border-slate-100 bg-white p-4 shadow-xs">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-800">Penggunaan berdasarkan model</h2>
        {loading ? <p className="text-xs text-slate-500">Memuat penggunaan…</p> : modelBreakdown.length === 0 ? (
          <p className="text-xs text-slate-500">Belum ada catatan penggunaan pada periode ini.</p>
        ) : (
          <div className="space-y-3">
            {modelBreakdown.map((item) => {
              const share = periodUsage.length ? Math.round((item.requests / periodUsage.length) * 100) : 0;
              return <div key={item.model}>
                <div className="mb-1 flex items-center justify-between gap-3 text-xs">
                  <span className="truncate font-semibold text-slate-700">{item.model}</span>
                  <span className="shrink-0 font-bold text-slate-900">{item.requests.toLocaleString('id-ID')} request · {item.tokens.toLocaleString('id-ID')} token</span>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-100"><div className="h-2 rounded-full bg-red-600" style={{ width: `${share}%` }} /></div>
              </div>;
            })}
          </div>
        )}
      </div>
    </div>
  );
};
