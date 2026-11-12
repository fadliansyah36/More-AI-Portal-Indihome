'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { ArrowLeft, Activity, Sparkles, LogOut, Plus } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { customerApi, type CustomerNetworkSession, type CustomerQuota, type CustomerWallet } from '@/lib/api/client';

interface WifiSessionViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

export const WifiSessionView: React.FC<WifiSessionViewProps> = ({ onBack, onNavigateTab }) => {
  const [sessions, setSessions] = useState<CustomerNetworkSession[]>([]);
  const [wallets, setWallets] = useState<CustomerWallet[]>([]);
  const [quotas, setQuotas] = useState<CustomerQuota[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    let active = true;
    Promise.allSettled([customerApi.networkSessions(100), customerApi.wallets(), customerApi.quotas()])
      .then(([sessionResult, walletResult, quotaResult]) => {
        if (!active) return;
        if (sessionResult.status === 'fulfilled') setSessions(sessionResult.value);
        else setError(sessionResult.reason instanceof Error ? sessionResult.reason.message : 'Riwayat sesi Wi-Fi tidak dapat dimuat.');
        if (walletResult.status === 'fulfilled') setWallets(walletResult.value.wallets || []);
        else setError((current) => current || (walletResult.reason instanceof Error ? walletResult.reason.message : 'Saldo akun tidak dapat dimuat.'));
        if (quotaResult.status === 'fulfilled') setQuotas(quotaResult.value || []);
        else setError((current) => current || (quotaResult.reason instanceof Error ? quotaResult.reason.message : 'Kuota akun tidak dapat dimuat.'));
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  const activeSession = sessions.find((session) => session.status === 'active' && new Date(session.expires_at).getTime() > now) || null;
  const remainingSeconds = activeSession ? Math.max(0, Math.floor((new Date(activeSession.expires_at).getTime() - now) / 1000)) : 0;
  const remainingTime = activeSession
    ? [Math.floor(remainingSeconds / 3600), Math.floor((remainingSeconds % 3600) / 60), remainingSeconds % 60].map((part) => String(part).padStart(2, '0')).join(':')
    : '—:—:—';
  const balance = useMemo(() => wallets.reduce((total, wallet) => total + Number(wallet.balance || 0), 0), [wallets]);
  const quota = quotas.find((item) => /partner|ai|token|credit/i.test(item.metric_key)) || null;
  const quotaLimit = quota ? Number(quota.limit_value) : 0;
  const quotaUsed = quota ? Number(quota.usage?.used_value || 0) : 0;
  const quotaPercent = quotaLimit > 0 ? Math.max(0, Math.min(100, (quotaUsed / quotaLimit) * 100)) : 0;
  const currency = wallets[0]?.currency || 'kredit';

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <button onClick={onBack} className="p-1 rounded-lg text-slate-400 hover:text-slate-700">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="text-center">
          <span className="text-[10px] font-bold text-red-600 uppercase tracking-wider block">Sheet 3 Screen 10</span>
          <h1 className="text-sm sm:text-base font-bold text-slate-900 leading-tight">Sesi Wi-Fi &amp; Kuota Real-Time</h1>
        </div>
        <div className="w-5" />
      </div>

      <div className="p-5 rounded-3xl bg-slate-900 text-white shadow-md text-center space-y-3 relative overflow-hidden">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/20 text-amber-300 text-[10px] font-bold border border-amber-500/30">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-300" />
          <span>{loading ? 'Memuat status sesi…' : activeSession ? 'Sesi Wi-Fi aktif' : 'Tidak ada sesi aktif'}</span>
        </div>
        <div>
          <span className="text-[11px] text-slate-400 font-medium block">Sisa Waktu Akses Wi-Fi</span>
          <div className="font-mono text-3xl sm:text-4xl font-black text-white tracking-wider my-1">{loading ? '—:—:—' : remainingTime}</div>
          <span className="text-[10px] text-slate-400">{activeSession ? `${activeSession.network?.name || 'Jaringan partner'} · Berakhir ${new Date(activeSession.expires_at).toLocaleString('id-ID')}` : 'Tidak ada sesi aktif yang tercatat pada akun ini.'}</span>
        </div>
        <div className="pt-2 flex gap-2">
          <button type="button" disabled className="flex-1 py-2.5 rounded-xl bg-slate-700 text-slate-400 font-bold text-xs flex items-center justify-center gap-1.5 cursor-not-allowed">
            <Plus className="w-3.5 h-3.5" /><span>Perpanjang Sesi</span>
          </button>
          <button type="button" disabled title="Aksi pemutusan sesi belum tersedia" className="px-3.5 py-2.5 rounded-xl bg-slate-800 text-slate-500 font-semibold text-xs flex items-center justify-center cursor-not-allowed">
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>

      {error && <div role="alert" className="rounded-2xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">{error}</div>}

      <div className="grid grid-cols-2 gap-2.5">
        <div className="p-4 rounded-3xl bg-white border border-slate-100 shadow-xs">
          <div className="flex items-center gap-1.5 text-slate-400 mb-1"><Activity className="w-3.5 h-3.5 text-emerald-600" /><span className="text-[10px] uppercase font-bold">Download Saat Ini</span></div>
          <span className="text-xl font-black text-slate-400 font-mono">—</span><span className="text-[10px] text-slate-400 ml-1 font-semibold">Mbps</span>
        </div>
        <div className="p-4 rounded-3xl bg-white border border-slate-100 shadow-xs">
          <div className="flex items-center gap-1.5 text-slate-400 mb-1"><Activity className="w-3.5 h-3.5 text-blue-600" /><span className="text-[10px] uppercase font-bold">Upload Saat Ini</span></div>
          <span className="text-xl font-black text-slate-400 font-mono">—</span><span className="text-[10px] text-slate-400 ml-1 font-semibold">Mbps</span>
        </div>
      </div>

      <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-red-50 text-red-600 flex items-center justify-center"><Sparkles className="w-4 h-4" /></div>
            <div><h3 className="text-xs font-bold text-slate-900">Kuota AI Partner Free</h3><p className="text-[10px] text-slate-400">Kredit pemakaian model &amp; agent</p></div>
          </div>
          <span className="text-xs font-bold text-slate-700 font-mono">{loading ? 'Memuat…' : quota ? `${quotaUsed.toLocaleString('id-ID')} / ${quotaLimit.toLocaleString('id-ID')}` : 'Tidak tersedia'}</span>
        </div>
        <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden"><div className="h-full rounded-full bg-red-600 transition-all" style={{ width: `${quotaPercent}%` }} /></div>
        <p className="text-[11px] text-slate-500">{quota ? `Pemakaian ${quota.metric_key} dari kebijakan kuota akun.` : 'Belum ada kebijakan kuota AI yang tersedia untuk akun ini.'}</p>
        <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
          <span>{loading ? 'Memuat saldo…' : `Saldo: ${Number.isFinite(balance) ? balance.toLocaleString('id-ID') : '—'} ${currency}`}</span>
          <button onClick={() => onNavigateTab('account_upgrade')} className="text-red-600 font-bold hover:underline">Lihat Paket &gt;</button>
        </div>
      </div>
    </div>
  );
};
