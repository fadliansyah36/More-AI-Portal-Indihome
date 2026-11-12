'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { Wifi, Shield, RefreshCw, Gauge, Sliders, Timer, ChevronRight, Activity } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { customerApi, CustomerNetworkSession } from '@/lib/api/client';

interface WifiManagementViewProps {
  onNavigateTab?: (tab: NavigationTab) => void;
}

export const WifiManagementView: React.FC<WifiManagementViewProps> = ({ onNavigateTab }) => {
  const [sessions, setSessions] = useState<CustomerNetworkSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (refresh = false) => {
    if (refresh) setRefreshing(true);
    try {
      setSessions(await customerApi.networkSessions(50));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Status jaringan tidak dapat dimuat.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const activeSession = sessions.find((session) => session.status === 'active') || null;
  const network = activeSession?.network || null;

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Wi-Fi Management</h1>
          <p className="text-xs text-slate-500">Status sesi jaringan yang terhubung dengan akun Anda</p>
        </div>
        <button onClick={() => void load(true)} disabled={refreshing} className="rounded-xl border border-slate-200 bg-white p-2 text-slate-600 shadow-2xs transition hover:text-red-600 disabled:opacity-50" title="Segarkan status">
          <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin text-red-600' : ''}`} />
        </button>
      </div>

      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-red-600 to-rose-700 p-5 text-white shadow-md">
        <div className="relative z-10 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-white/20"><Wifi className="h-4 w-4" /></div>
              <div><h3 className="text-sm font-black leading-none">{network?.name || 'Jaringan Wi-Fi'}</h3><span className="text-[10px] font-medium text-red-100">{network?.ssid_label || 'Informasi SSID tidak tersedia'}</span></div>
            </div>
            <span className={`rounded-full px-2.5 py-1 text-[10px] font-bold ${activeSession ? 'bg-emerald-500/90' : 'bg-white/20'}`}>{loading ? 'Memuat…' : activeSession ? 'Aktif' : 'Tidak ada sesi aktif'}</span>
          </div>
          <div className="grid grid-cols-2 gap-2 border-t border-white/20 pt-2">
            <div><span className="block text-[10px] text-red-200">Status Koneksi</span><span className="text-xs font-bold">{activeSession?.status || 'Tidak diketahui'}</span></div>
            <div><span className="block text-[10px] text-red-200">Gateway Type</span><span className="text-xs font-bold">{network?.gateway_type || '—'}</span></div>
            <div><span className="block text-[10px] text-red-200">Mulai Sesi</span><span className="text-xs font-bold">{activeSession ? new Date(activeSession.started_at).toLocaleString('id-ID') : '—'}</span></div>
            <div><span className="block text-[10px] text-red-200">Masa Berlaku</span><span className="text-xs font-bold">{activeSession ? new Date(activeSession.expires_at).toLocaleString('id-ID') : '—'}</span></div>
          </div>
        </div>
        <div className="pointer-events-none absolute -bottom-10 -right-10 h-32 w-32 rounded-full bg-white/10 blur-xl" />
      </div>

      {error && <div role="alert" className="rounded-2xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">{error}</div>}

      <div className="space-y-3 rounded-3xl border border-slate-100 bg-white p-4 shadow-xs">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-800">Detail jaringan</h2>
        <div className="space-y-2 text-xs">
          <div className="rounded-2xl border border-slate-100 bg-slate-50 p-3"><span className="block text-[10px] text-slate-400">Nama jaringan</span><span className="font-bold text-slate-800">{network?.name || 'Belum ada jaringan terkait sesi akun'}</span></div>
          <div className="rounded-2xl border border-slate-100 bg-slate-50 p-3"><span className="block text-[10px] text-slate-400">Lokasi partner</span><span className="font-bold text-slate-800">{network?.location?.name || 'Tidak tersedia'}</span></div>
          <div className="rounded-2xl border border-slate-100 bg-slate-50 p-3"><span className="block text-[10px] text-slate-400">Status jaringan partner</span><span className="font-bold text-slate-800">{network?.status || 'Tidak tersedia'}</span></div>
        </div>
        <div className="grid grid-cols-2 gap-2 pt-1">
          <div className="rounded-2xl border border-slate-100 bg-slate-50 p-3"><Activity className="mb-1 h-4 w-4 text-slate-600" /><span className="block text-xs font-bold text-slate-800">Diagnostik</span><span className="text-[10px] text-slate-400">Belum tersedia dari gateway</span></div>
          <div className="rounded-2xl border border-slate-100 bg-slate-50 p-3"><Shield className="mb-1 h-4 w-4 text-slate-600" /><span className="block text-xs font-bold text-slate-800">Proteksi jaringan</span><span className="text-[10px] text-slate-400">Status belum dilaporkan</span></div>
        </div>
      </div>

      {onNavigateTab && <div className="space-y-1.5 rounded-3xl border border-slate-100 bg-white p-4 shadow-xs">
        <button onClick={() => onNavigateTab('speedtest')} className="group flex w-full items-center justify-between rounded-xl border border-slate-100 bg-slate-50 p-2.5 text-left transition hover:bg-slate-100">
          <div className="flex items-center gap-2.5"><div className="flex h-7 w-7 items-center justify-center rounded-lg bg-red-600 text-white"><Gauge className="h-3.5 w-3.5" /></div><div><span className="block text-xs font-bold text-slate-900">Uji Kecepatan & Diagnostik</span><span className="text-[10px] text-slate-500">Hasil pengukuran aktual jika tersedia</span></div></div><ChevronRight className="h-4 w-4 text-red-600" />
        </button>
        <button onClick={() => onNavigateTab('device_access_control')} className="group flex w-full items-center justify-between rounded-xl border border-slate-100 bg-slate-50 p-2.5 text-left transition hover:bg-slate-100">
          <div className="flex items-center gap-2.5"><div className="flex h-7 w-7 items-center justify-center rounded-lg bg-slate-900 text-white"><Sliders className="h-3.5 w-3.5" /></div><div><span className="block text-xs font-bold text-slate-900">Kontrol Akses Perangkat</span><span className="text-[10px] text-slate-500">Memerlukan integrasi gateway</span></div></div><ChevronRight className="h-4 w-4 text-slate-400" />
        </button>
        <button onClick={() => onNavigateTab('wifi_session')} className="group flex w-full items-center justify-between rounded-xl border border-slate-100 bg-slate-50 p-2.5 text-left transition hover:bg-slate-100">
          <div className="flex items-center gap-2.5"><div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-600 text-white"><Timer className="h-3.5 w-3.5" /></div><div><span className="block text-xs font-bold text-slate-900">Riwayat Sesi Wi-Fi</span><span className="text-[10px] text-slate-500">Sesi tercatat pada akun</span></div></div><ChevronRight className="h-4 w-4 text-slate-400" />
        </button>
      </div>}

      <div className="space-y-3 rounded-3xl border border-slate-100 bg-white p-4 shadow-xs">
        <div className="flex items-center justify-between"><h2 className="text-xs font-bold uppercase tracking-wider text-slate-800">Riwayat Sesi Jaringan</h2><span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-700">{sessions.length} sesi</span></div>
        {loading ? <p className="py-5 text-center text-xs text-slate-500">Memuat sesi jaringan…</p> : sessions.length === 0 ? <p className="py-5 text-center text-xs text-slate-500">Belum ada sesi jaringan yang tercatat untuk akun ini.</p> : <div className="space-y-2">{sessions.map((session) => <div key={session.id} className="flex items-center justify-between gap-3 rounded-2xl border border-slate-100 bg-slate-50 p-3"><div className="min-w-0"><p className="truncate text-xs font-bold text-slate-900">{session.network?.name || 'Jaringan partner'}</p><p className="mt-0.5 text-[10px] text-slate-500">{new Date(session.started_at).toLocaleString('id-ID')}</p></div><span className="shrink-0 rounded-full bg-white px-2 py-1 text-[10px] font-semibold text-slate-600">{session.status}</span></div>)}</div>}
      </div>
    </div>
  );
};
