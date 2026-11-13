'use client';

import React, { useEffect, useState } from 'react';
import { customerApi, type CustomerUsageAnalytics } from '@/lib/api/client';
import { Activity, ArrowUpRight } from 'lucide-react';

export const AnalyticsView: React.FC = () => {
  const [timeFilter, setTimeFilter] = useState<'minggu' | 'bulan' | 'tahun'>('minggu');
  const [analytics, setAnalytics] = useState<CustomerUsageAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const periodDays = timeFilter === 'minggu' ? 7 : timeFilter === 'bulan' ? 30 : 365;

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    customerApi.usageAnalytics(periodDays)
      .then((result) => { if (active) setAnalytics(result); })
      .catch((cause) => {
        if (active) {
          setAnalytics(null);
          setError(cause instanceof Error ? cause.message : 'Data analytics tidak tersedia.');
        }
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [periodDays]);

  const summary = analytics?.summary;
  const modelBreakdown = analytics?.by_model || [];
  const dailyUsage = analytics?.by_day || [];
  const totalCost = Number(summary?.total_cost || 0);
  const maxDailyRequests = Math.max(1, ...dailyUsage.map((item) => item.requests));

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">Analytics & Usage</h1>
        <p className="text-xs text-slate-500">Statistik aktivitas AI, efisiensi tugas, dan konsumsi kuota dari catatan penggunaan tersimpan</p>
      </div>

      <div className="flex items-center gap-1 p-1 bg-white rounded-2xl border border-slate-200 shadow-2xs">
        {(['minggu', 'bulan', 'tahun'] as const).map((period) => (
          <button
            key={period}
            onClick={() => setTimeFilter(period)}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-xl capitalize transition ${
              timeFilter === period ? 'bg-red-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            {period}
          </button>
        ))}
      </div>

      {error && <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-700">{error}</div>}

      <div className="p-5 rounded-3xl bg-white border border-slate-100 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400 font-semibold block uppercase tracking-wider">Aktivitas AI · {timeFilter}</span>
            <div className="flex items-baseline gap-2 mt-0.5">
              <span className="text-3xl font-black text-slate-900 tracking-tight">{loading ? '—' : (summary?.total_requests || 0).toLocaleString('id-ID')}</span>
              <span className="text-xs font-bold text-slate-500 flex items-center gap-0.5"><ArrowUpRight className="w-3.5 h-3.5" /><span>request tercatat</span></span>
            </div>
          </div>
          <div className="w-10 h-10 rounded-2xl bg-red-50 text-red-600 flex items-center justify-center"><Activity className="w-5 h-5" /></div>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div className="rounded-xl bg-slate-50 border border-slate-100 p-3">
            <p className="text-[10px] text-slate-500">Total token</p>
            <p className="text-lg font-bold text-slate-900">{loading ? '—' : (summary?.total_tokens || 0).toLocaleString('id-ID')}</p>
          </div>
          <div className="rounded-xl bg-slate-50 border border-slate-100 p-3">
            <p className="text-[10px] text-slate-500">Penggunaan berhasil</p>
            <p className="text-lg font-bold text-slate-900">{loading ? '—' : (summary?.successful_requests || 0).toLocaleString('id-ID')}</p>
          </div>
          <div className="rounded-xl bg-slate-50 border border-slate-100 p-3">
            <p className="text-[10px] text-slate-500">Penggunaan gagal</p>
            <p className="text-lg font-bold text-slate-900">{loading ? '—' : (summary?.failed_requests || 0).toLocaleString('id-ID')}</p>
          </div>
          <div className="rounded-xl bg-slate-50 border border-slate-100 p-3">
            <p className="text-[10px] text-slate-500">Rata-rata latency</p>
            <p className="text-lg font-bold text-slate-900">{loading ? '—' : (summary?.average_latency_ms || 0).toLocaleString('id-ID') + ' ms'}</p>
          </div>
        </div>
        <p className="text-xs text-slate-500">Biaya tercatat: {loading ? '—' : totalCost.toLocaleString('id-ID', { maximumFractionDigits: 6 })}. Angka dihitung di FastAPI dari seluruh rekaman akun pada rentang waktu yang dipilih.</p>
      </div>

      <div className="space-y-3 rounded-3xl border border-slate-100 bg-white p-4 shadow-xs">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-800">Penggunaan berdasarkan model</h2>
        {loading ? <p className="text-xs text-slate-500">Memuat agregasi server…</p> : modelBreakdown.length === 0 ? (
          <p className="text-xs text-slate-500">Belum ada catatan penggunaan pada periode ini.</p>
        ) : (
          <div className="space-y-3">
            {modelBreakdown.map((item) => {
              const share = summary?.total_requests ? Math.round((item.requests / summary.total_requests) * 100) : 0;
              return <div key={item.provider_key + ':' + item.model_key}>
                <div className="mb-1 flex items-center justify-between gap-3 text-xs">
                  <span className="min-w-0 truncate font-semibold text-slate-700">{item.model_key}<span className="ml-1 text-[10px] font-normal text-slate-400">· {item.provider_key}</span></span>
                  <span className="shrink-0 font-bold text-slate-900">{item.requests.toLocaleString('id-ID')} request · {item.tokens.toLocaleString('id-ID')} token</span>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-100"><div className="h-2 rounded-full bg-red-600" style={{ width: `${share}%` }} /></div>
              </div>;
            })}
          </div>
        )}
      </div>

      <div className="space-y-3 rounded-3xl border border-slate-100 bg-white p-4 shadow-xs">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-800">Tren aktivitas harian</h2>
        {loading ? <p className="text-xs text-slate-500">Memuat tren harian…</p> : dailyUsage.length === 0 ? (
          <p className="text-xs text-slate-500">Belum ada rekaman harian pada periode ini.</p>
        ) : (
          <div className="space-y-2">
            {dailyUsage.map((item) => (
              <div key={item.day} className="grid grid-cols-[76px_1fr_48px] items-center gap-2 text-[10px]">
                <span className="text-slate-500">{new Date(item.day + 'T00:00:00Z').toLocaleDateString('id-ID', { day: '2-digit', month: 'short', timeZone: 'UTC' })}</span>
                <div className="h-2 rounded-full bg-slate-100"><div className="h-2 rounded-full bg-red-600" style={{ width: `${Math.max(2, Math.round((item.requests / maxDailyRequests) * 100))}%` }} /></div>
                <span className="text-right font-semibold text-slate-700">{item.requests}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
