'use client';

import React, { useState, useEffect } from 'react';
import { ArrowLeft, Clock, Wifi, Activity, Sparkles, RefreshCw, LogOut, Plus } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';

interface WifiSessionViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

export const WifiSessionView: React.FC<WifiSessionViewProps> = ({
  onBack,
  onNavigateTab,
}) => {
  const { showToast } = useToast();
  const [secondsLeft, setSecondsLeft] = useState(9918); // ~2 jam 45 menit 18 detik
  const [quotaUsed, setQuotaUsed] = useState(1250);
  const totalQuota = 100000;

  useEffect(() => {
    const timer = setInterval(() => {
      setSecondsLeft((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (secs: number) => {
    const hours = Math.floor(secs / 3600);
    const minutes = Math.floor((secs % 3600) / 60);
    const seconds = secs % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes
      .toString()
      .padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  const handleExtend = () => {
    setSecondsLeft((prev) => prev + 7200); // tambah 2 jam
    showToast('Sesi akses Wi-Fi berhasil diperpanjang (+2 Jam). Selamat menikmati!', 'success');
  };

  const handleDisconnect = () => {
    showToast('Sesi Wi-Fi telah diakhiri.', 'info');
    onNavigateTab('captive');
  };

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <button onClick={onBack} className="p-1 rounded-lg text-slate-400 hover:text-slate-700">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="text-center">
          <span className="text-[10px] font-bold text-red-600 uppercase tracking-wider block">
            Sheet 3 Screen 10
          </span>
          <h1 className="text-sm sm:text-base font-bold text-slate-900 leading-tight">
            Sesi Wi-Fi &amp; Kuota Real-Time
          </h1>
        </div>
        <div className="w-5" />
      </div>

      {/* Main Countdown Timer Card */}
      <div className="p-5 rounded-3xl bg-slate-900 text-white shadow-md text-center space-y-3 relative overflow-hidden">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-[10px] font-bold border border-emerald-500/30">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span>Sesi Aktif &amp; Terhubung</span>
        </div>

        <div>
          <span className="text-[11px] text-slate-400 font-medium block">Sisa Waktu Akses Wi-Fi</span>
          <div className="font-mono text-3xl sm:text-4xl font-black text-white tracking-wider my-1">
            {formatTime(secondsLeft)}
          </div>
          <span className="text-[10px] text-slate-400">
            Lokasi: <strong>CoffeeHouse Semarang (Meja 08)</strong>
          </span>
        </div>

        <div className="pt-2 flex gap-2">
          <button
            onClick={handleExtend}
            className="flex-1 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-xs transition flex items-center justify-center gap-1.5 shadow-xs"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Perpanjang Sesi (+2 Jam)</span>
          </button>
          <button
            onClick={handleDisconnect}
            className="px-3.5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs transition flex items-center justify-center"
            title="Keluar Sesi"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Real-Time Speed & Bandwidth Gauges */}
      <div className="grid grid-cols-2 gap-2.5">
        <div className="p-4 rounded-3xl bg-white border border-slate-100 shadow-xs">
          <div className="flex items-center gap-1.5 text-slate-400 mb-1">
            <Activity className="w-3.5 h-3.5 text-emerald-600" />
            <span className="text-[10px] uppercase font-bold">Download Saat Ini</span>
          </div>
          <span className="text-xl font-black text-slate-900 font-mono">98.4</span>
          <span className="text-[10px] text-slate-400 ml-1 font-semibold">Mbps</span>
        </div>

        <div className="p-4 rounded-3xl bg-white border border-slate-100 shadow-xs">
          <div className="flex items-center gap-1.5 text-slate-400 mb-1">
            <Activity className="w-3.5 h-3.5 text-blue-600" />
            <span className="text-[10px] uppercase font-bold">Upload Saat Ini</span>
          </div>
          <span className="text-xl font-black text-slate-900 font-mono">48.2</span>
          <span className="text-[10px] text-slate-400 ml-1 font-semibold">Mbps</span>
        </div>
      </div>

      {/* AI Quota Meter */}
      <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-red-50 text-red-600 flex items-center justify-center">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-slate-900">Kuota AI Partner Free</h3>
              <p className="text-[10px] text-slate-400">Kredit pemakaian model &amp; agent</p>
            </div>
          </div>
          <span className="text-xs font-bold text-slate-900 font-mono">
            {quotaUsed.toLocaleString('id-ID')} / {totalQuota.toLocaleString('id-ID')}
          </span>
        </div>

        {/* Progress bar */}
        <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-red-600 to-rose-500 rounded-full"
            style={{ width: `${(quotaUsed / totalQuota) * 100}%` }}
          />
        </div>

        <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
          <span>Tersisa: <strong>98.750 Poin</strong></span>
          <button
            onClick={() => onNavigateTab('account_upgrade')}
            className="text-red-600 font-bold hover:underline"
          >
            Upgrade Kuota &gt;
          </button>
        </div>
      </div>
    </div>
  );
};
