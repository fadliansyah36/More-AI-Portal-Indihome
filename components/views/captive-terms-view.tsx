'use client';

import React, { useState } from 'react';
import { ArrowLeft, ShieldCheck, FileText, CheckCircle2, AlertCircle } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';
import { MoreAiLogo, GlobalPartnerLogo } from '@/components/branding/logos';

interface CaptiveTermsViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

export const CaptiveTermsView: React.FC<CaptiveTermsViewProps> = ({
  onBack,
  onNavigateTab,
}) => {
  const { showToast } = useToast();
  const [agreedTerms, setAgreedTerms] = useState(false);
  const [agreedPrivacy, setAgreedPrivacy] = useState(false);

  const handleProceed = () => {
    if (!agreedTerms || !agreedPrivacy) {
      showToast('Harap setujui Syarat & Ketentuan serta Kebijakan Privasi untuk melanjutkan.', 'error');
      return;
    }
    showToast('Persetujuan berhasil dicatat. Melanjutkan ke verifikasi OTP...', 'success');
    onNavigateTab('captive_otp');
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
            Sheet 3 Screen 3
          </span>
          <h1 className="text-sm sm:text-base font-bold text-slate-900 leading-tight">
            Syarat &amp; Ketentuan Akses
          </h1>
        </div>
        <div className="w-5" />
      </div>

      {/* Brand Card */}
      <div className="p-4 rounded-3xl bg-slate-900 text-white flex items-center justify-between shadow-xs">
        <div>
          <span className="text-[10px] uppercase font-bold text-slate-400">Pratinjau Jaringan Partner</span>
          <h2 className="text-sm font-bold text-white mt-0.5">Akses Wi-Fi Partner &amp; MoreAI</h2>
          <p className="text-[11px] text-slate-300 mt-0.5">Kecepatan, durasi, dan benefit mengikuti konfigurasi partner serta verifikasi backend.</p>
        </div>
        <div className="w-10 h-10 rounded-2xl bg-white/10 flex items-center justify-center text-blue-400">
          <ShieldCheck className="w-5 h-5" />
        </div>
      </div>

      {/* Terms Content Box */}
      <div className="bg-white rounded-3xl p-4 sm:p-5 border border-slate-100 shadow-xs space-y-4 text-xs text-slate-600 leading-relaxed max-h-[380px] overflow-y-auto">
        <div className="space-y-1">
          <h3 className="font-bold text-slate-900 text-xs">1. Ketentuan Penggunaan Jaringan</h3>
          <p>
            Akses Wi-Fi hanya dapat diberikan setelah jaringan, lokasi partner, dan hasil verifikasi gateway dikonfirmasi backend. Pengguna wajib mematuhi kebijakan penggunaan jaringan yang berlaku.
          </p>
        </div>

        <div className="space-y-1">
          <h3 className="font-bold text-slate-900 text-xs">2. Hak Kuota AI Sponsor (Partner Free)</h3>
          <p>
            Benefit AI Credit hanya diberikan jika backend mengembalikan entitlement sponsor yang aktif. Besaran, masa berlaku, dan batas penggunaannya mengikuti konfigurasi partner; tidak ada nominal yang dijanjikan pada pratinjau ini.
          </p>
        </div>

        <div className="space-y-1">
          <h3 className="font-bold text-slate-900 text-xs">3. Kebijakan Privasi &amp; Keamanan Data</h3>
          <p>
            Pemrosesan data mengikuti Kebijakan Privasi MoreAI dan konfigurasi layanan yang berlaku. Detail penyimpanan, pemrosesan, dan pihak pemroses harus ditampilkan dari kebijakan resmi sebelum persetujuan diaktifkan.
          </p>
        </div>

        <div className="space-y-1">
          <h3 className="font-bold text-slate-900 text-xs">4. Batas Waktu Sesi (Fair Usage Policy)</h3>
          <p>
            Durasi sesi, batas kecepatan, dan perpanjangan ditentukan oleh konfigurasi jaringan partner dan dikonfirmasi melalui gateway. Tidak ada durasi atau performa yang dijanjikan pada pratinjau ini.
          </p>
        </div>
      </div>

      {/* Checkboxes */}
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-[11px] leading-relaxed text-amber-900">
          Pratinjau saja: gateway OTP belum terhubung. Centang dan tombol di halaman ini tidak merekam persetujuan, tidak mengirim OTP, dan tidak mengaktifkan akses Wi-Fi atau AI Credit.
        </div>

      <div className="bg-white rounded-3xl p-4 border border-slate-100 shadow-xs space-y-3 text-xs">
        <label className="flex items-start gap-2.5 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={agreedTerms}
            onChange={(e) => setAgreedTerms(e.target.checked)}
            className="w-4 h-4 rounded text-red-600 focus:ring-red-500 mt-0.5"
          />
          <span className="text-slate-700">
            Saya telah membaca pratinjau <strong>Syarat &amp; Ketentuan</strong>. Pilihan ini belum dikirim atau disimpan.
          </span>
        </label>

        <label className="flex items-start gap-2.5 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={agreedPrivacy}
            onChange={(e) => setAgreedPrivacy(e.target.checked)}
            className="w-4 h-4 rounded text-red-600 focus:ring-red-500 mt-0.5"
          />
          <span className="text-slate-700">
            Saya telah membaca informasi privasi. Persetujuan pemrosesan data belum dikirim atau disimpan.
          </span>
        </label>

        <button
          onClick={handleProceed}
          className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 active:scale-95 text-white font-bold text-xs transition shadow-xs mt-2"
        >
Lihat Status Integrasi
        </button>
      </div>
    </div>
  );
};
