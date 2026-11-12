'use client';

import React, { useState } from 'react';
import {
  Wifi,
  CheckCircle2,
  FileText,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  ChevronRight,
  Bot,
  GraduationCap,
  Wrench,
  Clock,
  RotateCcw,
} from 'lucide-react';
import { MoreAiLogo, GlobalPartnerLogo } from '@/components/branding/logos';
import { NavigationTab } from '@/types/moreai';

interface CaptivePortalViewProps {
  onBackToApp?: () => void;
  onNavigateTab?: (tab: NavigationTab) => void;
}

export const CaptivePortalView: React.FC<CaptivePortalViewProps> = ({
  onBackToApp,
  onNavigateTab,
}) => {
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3 | 4 | 5>(1);
  const [agreedTerms, setAgreedTerms] = useState(true);

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Title & Step Indicator */}
      <div className="flex items-center justify-between">
        <div>
          <span className="text-[10px] font-bold text-red-600 uppercase tracking-wider">
            Pratinjau Captive Portal · Gateway belum terhubung
          </span>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Wi-Fi & AI Customer Portal
          </h1>
        </div>
        <button
          onClick={() => setCurrentStep(1)}
          className="flex items-center gap-1 text-xs font-semibold text-slate-500 hover:text-red-600 p-1.5 rounded-lg hover:bg-slate-100"
          title="Ulangi Alur"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Reset Alur</span>
        </button>
      </div>

      {/* Visual Step Stepper */}
      <div className="flex items-center justify-between gap-1 p-2 bg-white rounded-2xl border border-slate-200 shadow-2xs text-[11px] font-semibold text-slate-600">
        <button
          onClick={() => setCurrentStep(1)}
          className={`flex-1 py-1 rounded-xl transition ${
            currentStep === 1 ? 'bg-red-600 text-white shadow-xs' : 'hover:bg-slate-50'
          }`}
        >
          1. Splash
        </button>
        <button
          onClick={() => setCurrentStep(2)}
          className={`flex-1 py-1 rounded-xl transition ${
            currentStep === 2 ? 'bg-red-600 text-white shadow-xs' : 'hover:bg-slate-50'
          }`}
        >
          2. Login
        </button>
        <button
          onClick={() => setCurrentStep(3)}
          className={`flex-1 py-1 rounded-xl transition ${
            currentStep === 3 ? 'bg-red-600 text-white shadow-xs' : 'hover:bg-slate-50'
          }`}
        >
          3. Syarat
        </button>
        <button
          onClick={() => setCurrentStep(4)}
          className={`flex-1 py-1 rounded-xl transition ${
            currentStep === 4 ? 'bg-red-600 text-white shadow-xs' : 'hover:bg-slate-50'
          }`}
        >
          4. Status Akses
        </button>
        <button
          onClick={() => setCurrentStep(5)}
          className={`flex-1 py-1 rounded-xl transition ${
            currentStep === 5 ? 'bg-red-600 text-white shadow-xs' : 'hover:bg-slate-50'
          }`}
        >
          5. Portal
        </button>
      </div>

      {/* STEP 1: SPLASH SCREEN (Sheet 3) */}
      {currentStep === 1 && (
        <div className="rounded-3xl bg-white p-6 border border-slate-100 shadow-xs text-center space-y-6">
          <div className="pt-4 flex flex-col items-center">
            <MoreAiLogo className="justify-center" />
            <p className="text-xs text-slate-500 font-medium mt-3">
              Akses Wi-Fi & AI menunggu integrasi gateway
            </p>
          </div>

          {/* Jakarta Skyline silhouette illustration placeholder */}
          <div className="py-6 px-4 bg-gradient-to-b from-slate-50 to-red-50/40 rounded-3xl border border-slate-100 flex flex-col items-center justify-center">
            <div className="w-16 h-16 rounded-full bg-red-600/10 text-red-600 flex items-center justify-center mb-3">
              <Wifi className="w-8 h-8 animate-pulse" />
            </div>
            <h3 className="text-sm font-bold text-slate-900">
              Akses Wi-Fi Global Partner ISP & Nikmati AI Terbaik
            </h3>
            <p className="text-xs text-slate-500 max-w-xs mt-1">
              Aktivasi akses dan benefit hanya dapat dikonfirmasi setelah layanan gateway dan entitlement backend terintegrasi.
            </p>
          </div>

          <div className="space-y-2 pt-2">
            <button
              onClick={() => setCurrentStep(2)}
              className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition shadow-xs"
            >
              Mulai Sekarang
            </button>
            <button
              onClick={() => setCurrentStep(4)}
              className="w-full py-2.5 rounded-2xl bg-slate-100 hover:bg-slate-200 text-slate-600 text-xs font-semibold transition"
            >
              Lewati (Tamu Cepat)
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: LOGIN / REGISTRASI (Sheet 3) */}
      {currentStep === 2 && (
        <div className="rounded-3xl bg-white p-6 border border-slate-100 shadow-xs space-y-5">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <MoreAiLogo />
            <GlobalPartnerLogo />
          </div>

          <div className="text-center pt-2">
            <div className="w-12 h-12 rounded-2xl bg-red-50 text-red-600 flex items-center justify-center mx-auto mb-2">
              <Wifi className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-slate-900">
              Selamat Datang di MoreAI Wi-Fi
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Silakan masuk atau daftar untuk melanjutkan akses internet dan bonus AI Credit.
            </p>
          </div>

          <div className="space-y-2.5 pt-2">
            <button
              onClick={() => setCurrentStep(3)}
              className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition shadow-xs flex items-center justify-center gap-2"
            >
              <span>Masuk Akun Tamu / Partner</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            <button
              onClick={() => setCurrentStep(3)}
              className="w-full py-3 rounded-2xl bg-white border border-slate-300 hover:bg-slate-50 text-slate-800 text-xs font-semibold transition shadow-2xs"
            >
              Daftar Akun Baru
            </button>

            <button
              onClick={() => setCurrentStep(3)}
              className="w-full py-2 text-slate-400 hover:text-slate-600 text-xs font-medium"
            >
              Nanti Saja
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: SYARAT DAN KETENTUAN (Sheet 3) */}
      {currentStep === 3 && (
        <div className="rounded-3xl bg-white p-6 border border-slate-100 shadow-xs space-y-4">
          <div className="text-center">
            <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-2">
              <FileText className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-slate-900">
              Syarat dan Ketentuan
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Dengan melanjutkan, Anda menyetujui syarat dan ketentuan penggunaan layanan MoreAI di jaringan Global Partner ISP/Network.
            </p>
          </div>

          <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-600 space-y-2 max-h-40 overflow-y-auto">
            <p>1. Akses Wi-Fi disediakan secara cuma-cuma oleh venue mitra bekerjasama dengan Global Partner ISP/Network.</p>
            <p>2. Pengguna mendapatkan kuota sponsor AI Credit Free selama berada di jangkauan lokasi Wi-Fi.</p>
            <p>3. Keamanan privasi data dan perlindungan informasi pribadi dipantau oleh MoreAI Guard Protocol.</p>
          </div>

          <label className="flex items-center gap-2.5 p-2 cursor-pointer text-xs font-semibold text-slate-800">
            <input
              type="checkbox"
              checked={agreedTerms}
              onChange={(e) => setAgreedTerms(e.target.checked)}
              className="w-4 h-4 rounded text-red-600 focus:ring-red-500"
            />
            <span>Saya setuju dengan Syarat dan Ketentuan</span>
          </label>

          <button
            onClick={() => setCurrentStep(4)}
            disabled={!agreedTerms}
            className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 disabled:opacity-40 text-white text-xs font-bold transition shadow-xs"
          >
            Lanjutkan
          </button>
        </div>
      )}

      {/* STEP 4: KONEKSI BERHASIL (Sheet 3) */}
      {currentStep === 4 && (
        <div className="rounded-3xl bg-white p-6 border border-slate-100 shadow-xs text-center space-y-5">
          <div className="w-16 h-16 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto">
            <CheckCircle2 className="w-10 h-10" />
          </div>

          <div>
            <h3 className="text-lg font-bold text-slate-900">Pratinjau Status Akses</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-xs mx-auto">
              Selamat! Anda sudah terkoneksi ke jaringan Wi-Fi Global Partner ISP/Network dengan performa optimal.
            </p>
          </div>

          <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-left text-xs space-y-1">
            <div className="flex justify-between">
              <span className="text-slate-400">Info Koneksi:</span>
              <span className="font-bold text-emerald-600">● Global Partner Wi-Fi Aktif</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Kecepatan:</span>
              <span className="font-semibold text-slate-800">Belum dilaporkan gateway</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Bonus Kuota:</span>
              <span className="font-bold text-red-600">Menunggu entitlement backend</span>
            </div>
          </div>

          <button
            onClick={() => setCurrentStep(5)}
            className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition shadow-xs"
          >
            Lanjut ke MoreAI
          </button>
        </div>
      )}

      {/* STEP 5: BERANDA CUSTOMER PORTAL (Sheet 3) */}
      {currentStep === 5 && (
        <div className="space-y-4">
          <div className="p-4 rounded-3xl bg-white border border-slate-100 shadow-xs flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-red-50 text-red-600 flex items-center justify-center font-bold">
                M
              </div>
              <div>
                <h3 className="text-xs font-bold text-slate-900">Halo, Pengguna!</h3>
                <p className="text-[11px] text-slate-500">Selamat menikmati layanan MoreAI di jaringan Global Partner ISP/Network</p>
              </div>
            </div>
          </div>

          {/* Akses AI Premium Gratis banner */}
          <div className="p-4 rounded-3xl bg-gradient-to-r from-red-600 to-rose-600 text-white shadow-xs flex items-center justify-between">
            <div>
              <span className="text-[10px] font-bold text-amber-300 uppercase block">Benefit Venue Terverifikasi</span>
              <h4 className="text-sm font-bold mt-0.5">Akses AI Premium Gratis untuk Anda</h4>
              <p className="text-[11px] text-red-100 mt-0.5">Kredit 100K poin aktif selama berada di jaringan ini.</p>
            </div>
            <button
              onClick={() => onNavigateTab && onNavigateTab('benefits')}
              className="px-3 py-1.5 rounded-xl bg-white text-red-600 font-bold text-xs shrink-0 shadow-2xs"
            >
              Lihat Detail
            </button>
          </div>

          {/* Menu Utama Customer Portal */}
          <div className="grid grid-cols-4 gap-2">
            <button
              onClick={() => onNavigateTab && onNavigateTab('chat')}
              className="p-3 rounded-2xl bg-white border border-slate-100 hover:border-red-200 flex flex-col items-center text-center shadow-2xs transition"
            >
              <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center mb-1">
                <Bot className="w-4 h-4" />
              </div>
              <span className="text-[11px] font-bold text-slate-800">Chat AI</span>
            </button>

            <button
              onClick={() => onNavigateTab && onNavigateTab('create')}
              className="p-3 rounded-2xl bg-white border border-slate-100 hover:border-red-200 flex flex-col items-center text-center shadow-2xs transition"
            >
              <div className="w-8 h-8 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center mb-1">
                <Wrench className="w-4 h-4" />
              </div>
              <span className="text-[11px] font-bold text-slate-800">Tools</span>
            </button>

            <button
              onClick={() => onNavigateTab && onNavigateTab('edutech')}
              className="p-3 rounded-2xl bg-white border border-slate-100 hover:border-red-200 flex flex-col items-center text-center shadow-2xs transition"
            >
              <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-1">
                <GraduationCap className="w-4 h-4" />
              </div>
              <span className="text-[11px] font-bold text-slate-800">EduTech</span>
            </button>

            <button
              onClick={() => onNavigateTab && onNavigateTab('home')}
              className="p-3 rounded-2xl bg-white border border-slate-100 hover:border-red-200 flex flex-col items-center text-center shadow-2xs transition"
            >
              <div className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center mb-1">
                <Sparkles className="w-4 h-4" />
              </div>
              <span className="text-[11px] font-bold text-slate-800">Lainnya</span>
            </button>
          </div>

          <button
            onClick={onBackToApp}
            className="w-full py-3 rounded-2xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition shadow-xs flex items-center justify-center gap-2"
          >
            <span>Buka Dashboard Utama MoreAI</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};
