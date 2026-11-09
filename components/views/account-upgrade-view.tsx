'use client';

import React, { useState } from 'react';
import { ArrowLeft, Crown, Check, Sparkles, Shield, HardDrive, Zap } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';

interface AccountUpgradeViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

export const AccountUpgradeView: React.FC<AccountUpgradeViewProps> = ({
  onBack,
  onNavigateTab,
}) => {
  const { showToast } = useToast();
  const [selectedPlan, setSelectedPlan] = useState<'pro' | 'enterprise'>('pro');

  const handleUpgrade = (planName: string) => {
    showToast(`Akun berhasil ditingkatkan ke paket ${planName}! Fitur penuh telah aktif.`, 'success');
    onNavigateTab('profile');
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
            Sheet 3 Screen 11
          </span>
          <h1 className="text-sm sm:text-base font-bold text-slate-900 leading-tight">
            Upgrade ke Akun Penuh
          </h1>
        </div>
        <div className="w-5" />
      </div>

      {/* Hero Card */}
      <div className="p-5 rounded-3xl bg-gradient-to-br from-red-600 via-rose-600 to-red-700 text-white shadow-md space-y-3 text-center">
        <div className="w-12 h-12 rounded-2xl bg-white/20 backdrop-blur-xs text-amber-300 flex items-center justify-center mx-auto shadow-2xs">
          <Crown className="w-6 h-6" />
        </div>
        <div>
          <h2 className="text-lg font-black tracking-tight">Lebih Banyak Ruang &amp; Kuota AI</h2>
          <p className="text-xs text-red-100 mt-1 max-w-xs mx-auto">
            Simpan riwayat tugas permanen, akses AI tanpa batas kuota venue, dan aktifkan semua autonomous agent.
          </p>
        </div>
      </div>

      {/* Comparison: Akun Tamu vs Akun Penuh */}
      <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-xs space-y-3">
        <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
          Perbandingan Fitur:
        </h3>

        <div className="space-y-2 text-xs">
          <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-between">
            <span className="text-slate-600 font-medium">Penyimpanan Berkas Permanen Cloud</span>
            <span className="font-bold text-emerald-600 flex items-center gap-1">
              <Check className="w-3.5 h-3.5" /> 50 GB
            </span>
          </div>

          <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-between">
            <span className="text-slate-600 font-medium">Riwayat Percakapan &amp; Dokumen</span>
            <span className="font-bold text-emerald-600 flex items-center gap-1">
              <Check className="w-3.5 h-3.5" /> Tanpa Batas
            </span>
          </div>

          <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-between">
            <span className="text-slate-600 font-medium">Akses Autonomous AI Agent</span>
            <span className="font-bold text-emerald-600 flex items-center gap-1">
              <Check className="w-3.5 h-3.5" /> 5 Agent Aktif
            </span>
          </div>

          <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-between">
            <span className="text-slate-600 font-medium">Sinkronisasi Multi-Perangkat (HP/Laptop)</span>
            <span className="font-bold text-emerald-600 flex items-center gap-1">
              <Check className="w-3.5 h-3.5" /> Otomatis
            </span>
          </div>
        </div>
      </div>

      {/* Pricing Option Cards */}
      <div className="space-y-2.5">
        <div
          onClick={() => setSelectedPlan('pro')}
          className={`p-4 rounded-3xl border-2 cursor-pointer transition flex items-center justify-between ${
            selectedPlan === 'pro'
              ? 'border-red-500 bg-red-50/50 shadow-xs'
              : 'border-slate-200 bg-white hover:border-slate-300'
          }`}
        >
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-bold text-slate-900">MoreAI Pro Personal</h4>
              <span className="text-[10px] font-bold text-red-600 bg-red-100 px-2 py-0.5 rounded-full">
                Terpopuler
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">500.000 Poin / Bulan + 50 GB Storage</p>
          </div>
          <div className="text-right">
            <span className="text-sm font-black text-slate-900">Rp 49.000</span>
            <span className="text-[10px] text-slate-400 block">/ bulan</span>
          </div>
        </div>

        <button
          onClick={() => handleUpgrade('Pro Personal')}
          className="w-full py-3.5 rounded-2xl bg-red-600 hover:bg-red-700 active:scale-95 text-white font-bold text-xs transition shadow-xs"
        >
          Konfirmasi &amp; Upgrade Sekarang
        </button>
      </div>
    </div>
  );
};
