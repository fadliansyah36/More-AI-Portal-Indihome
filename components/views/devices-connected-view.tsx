'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { ArrowLeft, Wifi, Shield, RefreshCw, Smartphone } from 'lucide-react';
import { customerApi, CustomerNetworkSession } from '@/lib/api/client';

interface DevicesConnectedViewProps {
  onBack: () => void;
}

export const DevicesConnectedView: React.FC<DevicesConnectedViewProps> = ({ onBack }) => {
  const [sessions, setSessions] = useState<CustomerNetworkSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setSessions(await customerApi.networkSessions(100));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Riwayat jaringan tidak dapat dimuat.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      <div className="flex items-center justify-between border-b border-slate-100 pb-2">
        <button onClick={onBack} className="rounded-lg p-1 text-slate-400 hover:text-slate-700" aria-label="Kembali"><ArrowLeft className="h-5 w-5" /></button>
        <div className="text-center"><h1 className="text-base font-bold leading-tight text-slate-900">Perangkat &amp; Sesi Wi-Fi</h1><span className="text-[10px] font-medium text-slate-500">Data sesi akun dari FastAPI</span></div>
        <button onClick={() => { setLoading(true); setError(null); void load(); }} disabled={loading} className="rounded-lg p-1.5 text-slate-400 hover:text-slate-700 disabled:opacity-50" aria-label="Segarkan"><RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /></button>
      </div>

      <div className="flex items-start gap-3 rounded-3xl border border-slate-100 bg-white p-4 shadow-xs">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-blue-600"><Shield className="h-5 w-5" /></div>
        <div><h3 className="text-xs font-bold text-slate-900">Inventaris perangkat gateway</h3><p className="mt-1 text-[11px] leading-relaxed text-slate-500">API saat ini menyediakan sesi jaringan milik akun, tetapi belum menyediakan inventaris perangkat gateway, alamat IP, bandwidth per perangkat, atau tindakan pemutusan perangkat. Data tersebut tidak ditampilkan sebagai data live.</p></div>
      </div>

      {error && <div role="alert" className="rounded-2xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">{error}</div>}
      <div className="space-y-3 rounded-3xl border border-slate-100 bg-white p-4 shadow-xs">
        <div className="flex items-center justify-between"><h2 className="text-xs font-bold uppercase tracking-wider text-slate-800">Sesi jaringan</h2><span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-700">{sessions.length} sesi</span></div>
        {loading ? <p className="py-6 text-center text-xs text-slate-500">Memuat sesi jaringan…</p> : sessions.length === 0 ? <div className="py-6 text-center"><Wifi className="mx-auto h-7 w-7 text-slate-300" /><p className="mt-2 text-xs text-slate-500">Belum ada sesi jaringan yang tercatat untuk akun ini.</p></div> : (
          <div className="space-y-2">{sessions.map((session) => (
            <article key={session.id} className="flex items-center justify-between gap-3 rounded-2xl border border-slate-100 bg-slate-50 p-3">
              <div className="flex min-w-0 items-center gap-3"><div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-slate-200 bg-white"><Smartphone className="h-4 w-4 text-slate-600" /></div><div className="min-w-0"><h3 className="truncate text-xs font-bold text-slate-900">{session.network?.name || 'Jaringan partner'}</h3><p className="mt-0.5 text-[10px] text-slate-500">{session.network?.location?.name || 'Lokasi tidak tersedia'}</p><p className="mt-0.5 text-[10px] text-slate-400">{new Date(session.started_at).toLocaleString('id-ID')}</p></div></div>
              <span className={`shrink-0 rounded-full px-2 py-1 text-[9px] font-bold ${session.status === 'active' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-200 text-slate-600'}`}>{session.status}</span>
            </article>
          ))}</div>
        )}
      </div>
    </div>
  );
};
