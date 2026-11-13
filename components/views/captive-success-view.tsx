'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { ArrowLeft, CheckCircle2, Wifi, Gift, ArrowRight } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { customerApi, type CustomerNetworkSession, type CustomerWallet, type CustomerEntitlement } from '@/lib/api/client';

interface CaptiveSuccessViewProps {
  onNavigateTab: (tab: NavigationTab) => void;
}

export const CaptiveSuccessView: React.FC<CaptiveSuccessViewProps> = ({
  onNavigateTab,
}) => {
  const [sessions, setSessions] = useState<CustomerNetworkSession[]>([]);
  const [wallets, setWallets] = useState<CustomerWallet[]>([]);
  const [entitlements, setEntitlements] = useState<CustomerEntitlement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    Promise.allSettled([customerApi.networkSessions(100), customerApi.wallets(), customerApi.entitlements()])
      .then(([sessionResult, walletResult, entitlementResult]) => {
        if (!active) return;
        if (sessionResult.status === 'fulfilled') setSessions(sessionResult.value);
        else setError(sessionResult.reason instanceof Error ? sessionResult.reason.message : 'Status sesi tidak dapat dimuat.');
        if (walletResult.status === 'fulfilled') setWallets(walletResult.value.wallets || []);
        else setError((current) => current || (walletResult.reason instanceof Error ? walletResult.reason.message : 'Saldo akun tidak dapat dimuat.'));
        if (entitlementResult.status === 'fulfilled') setEntitlements(entitlementResult.value || []);
        else setError((current) => current || (entitlementResult.reason instanceof Error ? entitlementResult.reason.message : 'Benefit akun tidak dapat dimuat.'));
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);
  const activeSession = sessions.find((session) => session.status === 'active' && new Date(session.expires_at).getTime() > Date.now()) || null;
  const primaryWallet = wallets.find((wallet) => wallet.status === 'active') || null;
  const balance = primaryWallet ? Number(primaryWallet.balance || 0) : null;
  const partnerBenefit = entitlements.some((item) => item.status === 'active' && item.source_type === 'partner');

  return (
    <div className="space-y-4 pb-20 animate-fadeIn text-center">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <button onClick={() => onNavigateTab('captive')} className="p-1 rounded-lg text-slate-400 hover:text-slate-700">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <span className="text-[10px] font-bold text-emerald-600 uppercase tracking-wider">
          Sheet 3 Screen 5
        </span>
        <div className="w-5" />
      </div>

      {/* Big Animated Success Badge */}
      <div className="p-6 rounded-3xl bg-white border border-slate-100 shadow-xs space-y-4">
        <div className={`w-20 h-20 rounded-full flex items-center justify-center mx-auto shadow-sm ring-8 ${activeSession ? 'bg-emerald-50 text-emerald-600 ring-emerald-500/10' : 'bg-amber-50 text-amber-600 ring-amber-500/10'}`}>
          {activeSession ? <CheckCircle2 className="w-10 h-10" /> : <Wifi className="w-10 h-10" />}
        </div>

        <div>
          <h1 className="text-xl font-black text-slate-900 tracking-tight">
            {loading ? 'Memeriksa Status Koneksi…' : activeSession ? 'Sesi Wi-Fi Aktif' : 'Koneksi Belum Terkonfirmasi'}
          </h1>
          <p className="text-xs text-slate-500 mt-1 max-w-xs mx-auto">
            {activeSession ? 'Backend mencatat sesi jaringan aktif untuk akun Anda.' : 'Belum ada sesi jaringan aktif yang dapat dikonfirmasi dari backend. Verifikasi captive portal belum membuat sesi.'}
          </p>
        </div>

        {/* Network Details Card */}
        <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 text-left text-xs space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Nama Wi-Fi (SSID):</span>
            <span className="font-bold text-slate-900 flex items-center gap-1">
              <Wifi className="w-3.5 h-3.5 text-blue-600" />
              {activeSession?.network?.ssid_label || activeSession?.network?.name || 'Tidak tersedia'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Status jaringan:</span>
            <span className="font-bold text-slate-800">{activeSession?.network?.status || 'Tidak tersedia'}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Masa berlaku:</span>
            <span className="font-bold text-slate-800">{activeSession?.expires_at ? new Date(activeSession.expires_at).toLocaleString('id-ID') : 'Tidak tersedia'}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Status sesi:</span>
            <span className={`font-bold ${activeSession ? 'text-emerald-600' : 'text-amber-700'}`}>{activeSession?.status || 'Belum terverifikasi'}</span>
          </div>
        </div>

        {/* AI Bonus Banner */}
        <div className="p-4 rounded-2xl bg-gradient-to-r from-red-600 to-rose-600 text-white text-left flex items-center justify-between shadow-xs">
          <div>
            <span className="text-[9px] font-bold uppercase tracking-wider text-red-200 block">Saldo Wallet</span>
            <span className="text-sm font-black block mt-0.5">{loading ? 'Memuat…' : balance !== null && Number.isFinite(balance) ? balance.toLocaleString('id-ID') + ' ' + primaryWallet?.currency : 'Tidak tersedia'}</span>
            <span className="text-[10px] text-white/80">{partnerBenefit ? 'Entitlement Partner aktif tercatat pada akun.' : 'Tidak ada entitlement Partner aktif yang tercatat.'}</span>
          </div>
          <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center text-amber-300">
            <Gift className="w-5 h-5" />
          </div>
        </div>

        {error && <div role="alert" className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-left text-xs text-amber-900">{error}</div>}

        {/* Action Buttons */}
        <div className="space-y-2 pt-2">
          <button
            onClick={() => onNavigateTab('home')}
            className="w-full py-3.5 rounded-2xl bg-red-600 hover:bg-red-700 active:scale-95 text-white font-bold text-xs transition shadow-xs flex items-center justify-center gap-2"
          >
            <span>{activeSession ? 'Buka Workspace MoreAI' : 'Kembali ke Workspace'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <button
            onClick={() => onNavigateTab('wifi_session')}
            className="w-full py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition"
          >
            Lihat Monitor Sesi Wi-Fi
          </button>
        </div>
      </div>
    </div>
  );
};
