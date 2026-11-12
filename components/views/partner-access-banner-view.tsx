'use client';

import React from 'react';
import { ArrowLeft, Wifi, Gift, Sparkles, CheckCircle2 } from 'lucide-react';
import { MoreAiLogo, GlobalPartnerLogo } from '@/components/branding/logos';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';

interface PartnerAccessBannerViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

export const PartnerAccessBannerView: React.FC<PartnerAccessBannerViewProps> = ({
  onBack,
  onNavigateTab,
}) => {
  const { showToast } = useToast();
  return (
    <div className="min-h-[680px] flex flex-col justify-between py-6 px-4 bg-gradient-to-b from-red-600 via-rose-600 to-red-700 text-white rounded-3xl animate-fadeIn relative overflow-hidden">
      {/* Top Header */}
      <div className="flex items-center justify-between pb-2 border-b border-white/20">
        <button
          onClick={onBack}
          className="p-1 rounded-lg text-white/80 hover:text-white"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex items-center gap-2">
          <span className="font-bold text-xs text-white">Global Partner ISP</span>
          <span className="text-white/60">×</span>
          <span className="font-bold text-xs text-white">MoreAI</span>
        </div>
        <div className="w-5" />
      </div>

      {/* Main Content Area (Exact from Sheet 6 Screen 12) */}
      <div className="my-auto py-4 text-center space-y-4">
        {/* Customer Wifi Experience Illustration Card */}
        <div className="w-56 h-56 mx-auto rounded-3xl bg-white/10 border border-white/20 p-4 backdrop-blur-xs flex flex-col items-center justify-center relative shadow-lg">
          <div className="w-20 h-20 rounded-2xl bg-white text-red-600 flex items-center justify-center shadow-md mb-2">
            <Wifi className="w-10 h-10 animate-pulse" />
          </div>
          <span className="text-xs font-black uppercase tracking-wider text-amber-300">
            Status jaringan menunggu verifikasi
          </span>
          <span className="text-sm font-bold text-white mt-1">
            Jaringan partner
          </span>
          <span className="text-[10px] text-white/80 mt-0.5">
            Kecepatan belum dilaporkan gateway
          </span>
        </div>

        <div className="space-y-2 max-w-xs mx-auto">
          <h2 className="text-xl font-black tracking-tight leading-snug">
            AI Credit Free via Global Partner ISP
          </h2>
          <p className="text-xs text-red-100 leading-relaxed font-medium">
            Benefit jaringan dan AI ditampilkan setelah lokasi partner serta sesi gateway berhasil diverifikasi.
          </p>
        </div>

        <div className="p-3 rounded-2xl bg-black/20 border border-white/10 text-left text-xs space-y-1.5 max-w-xs mx-auto">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-300 shrink-0" />
            <span>Kuota sponsor mengikuti entitlement aktif dari backend</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-300 shrink-0" />
            <span>Kelayakan dan ketentuan mengikuti program partner</span>
          </div>
        </div>
      </div>

      {/* Button Lihat Status Benefit */}
      <div className="pb-2">
        <button
          onClick={() => {
            showToast('Status benefit akan ditampilkan setelah entitlement partner diverifikasi oleh backend.', 'info');
            onNavigateTab('benefits');
          }}
          className="w-full py-3.5 rounded-2xl bg-white text-red-600 hover:bg-red-50 active:scale-95 text-xs sm:text-sm font-bold transition shadow-lg"
        >
          Aktifkan Sekarang
        </button>
      </div>
    </div>
  );
};
