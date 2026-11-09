'use client';

import React from 'react';
import { ArrowLeft, CheckCircle2, Wifi, Sparkles, Gift, ArrowRight } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { MoreAiLogo, IndiHomeLogo } from '@/components/branding/logos';

interface CaptiveSuccessViewProps {
  onNavigateTab: (tab: NavigationTab) => void;
}

export const CaptiveSuccessView: React.FC<CaptiveSuccessViewProps> = ({
  onNavigateTab,
}) => {
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
        <div className="w-20 h-20 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto shadow-sm ring-8 ring-emerald-500/10">
          <CheckCircle2 className="w-10 h-10" />
        </div>

        <div>
          <h1 className="text-xl font-black text-slate-900 tracking-tight">
            Sukses Terhubung!
          </h1>
          <p className="text-xs text-slate-500 mt-1 max-w-xs mx-auto">
            Perangkat Anda kini telah terhubung ke jaringan internet IndiHome &amp; siap menggunakan platform MoreAI.
          </p>
        </div>

        {/* Network Details Card */}
        <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 text-left text-xs space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Nama Wi-Fi (SSID):</span>
            <span className="font-bold text-slate-900 flex items-center gap-1">
              <Wifi className="w-3.5 h-3.5 text-red-600" />
              CoffeeHouse_IndiHome
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Kecepatan:</span>
            <span className="font-bold text-emerald-600">100 Mbps Simetris</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Durasi Sesi Aktif:</span>
            <span className="font-bold text-slate-800">3 Jam (Dapat Diperpanjang)</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Status Keamanan:</span>
            <span className="font-bold text-slate-800">WPA3 Enterprise Enkripsi</span>
          </div>
        </div>

        {/* AI Bonus Banner */}
        <div className="p-4 rounded-2xl bg-gradient-to-r from-red-600 to-rose-600 text-white text-left flex items-center justify-between shadow-xs">
          <div>
            <span className="text-[9px] font-bold uppercase tracking-wider text-red-200 block">Bonus Aktivasi Otomatis</span>
            <span className="text-sm font-black block mt-0.5">100.000 Poin AI Credit</span>
            <span className="text-[10px] text-white/80">Langsung aktif untuk model AI &amp; tools riset</span>
          </div>
          <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center text-amber-300">
            <Gift className="w-5 h-5" />
          </div>
        </div>

        {/* Action Buttons */}
        <div className="space-y-2 pt-2">
          <button
            onClick={() => onNavigateTab('home')}
            className="w-full py-3.5 rounded-2xl bg-red-600 hover:bg-red-700 active:scale-95 text-white font-bold text-xs transition shadow-xs flex items-center justify-center gap-2"
          >
            <span>Buka Workspace MoreAI</span>
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
