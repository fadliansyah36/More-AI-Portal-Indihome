'use client';

import React from 'react';
import { ArrowLeft, Shield, Sliders } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';

interface DeviceAccessControlViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

export const DeviceAccessControlView: React.FC<DeviceAccessControlViewProps> = ({
  onBack,
}) => {
  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <button onClick={onBack} className="p-1 rounded-lg text-slate-400 hover:text-slate-700">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="text-center">
          <span className="text-[10px] font-bold text-red-600 uppercase tracking-wider block">
            Sheet 5 Screen 8
          </span>
          <h1 className="text-sm sm:text-base font-bold text-slate-900 leading-tight">
            Kontrol Akses &amp; Bandwidth
          </h1>
        </div>
        <div className="w-5" />
      </div>

      <div className="p-4 rounded-3xl bg-slate-900 text-white flex items-center justify-between shadow-xs">
        <div>
          <span className="text-[10px] uppercase font-bold text-slate-400">Kontrol Gateway</span>
          <h2 className="text-sm font-bold text-white mt-0.5">Inventaris Perangkat Partner</h2>
          <p className="text-[11px] text-slate-300 mt-0.5">Kontrol jeda akses, bandwidth, dan filter konten memerlukan adapter gateway yang aktif.</p>
        </div>
        <div className="w-10 h-10 rounded-2xl bg-white/10 flex items-center justify-center text-emerald-400">
          <Sliders className="w-5 h-5" />
        </div>
      </div>

      <div className="rounded-3xl border border-slate-200 bg-white p-5 text-center text-xs text-slate-500">
        <Shield className="mx-auto mb-3 h-8 w-8 text-slate-300" />
        <h3 className="font-bold text-slate-800">Data perangkat belum tersedia</h3>
        <p className="mt-1 leading-relaxed">
          FastAPI saat ini menyediakan riwayat sesi jaringan akun, tetapi belum menyediakan inventaris perangkat gateway maupun endpoint untuk menjeda koneksi, mengubah prioritas bandwidth, atau mengatur Safe Browsing. Semua kontrol dinonaktifkan; tidak ada perubahan lokal yang diklaim berhasil.
        </p>
      </div>
    </div>
  );
};
