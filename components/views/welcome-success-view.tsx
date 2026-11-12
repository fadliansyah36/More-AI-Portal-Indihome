'use client';

import React from 'react';
import { Wifi, Home, Sparkles, ArrowRight, CheckCircle2 } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';

interface WelcomeSuccessViewProps {
  onNavigate: (tab: NavigationTab) => void;
}

export const WelcomeSuccessView: React.FC<WelcomeSuccessViewProps> = ({ onNavigate }) => {
  return (
    <div className="min-h-[680px] flex flex-col justify-between py-8 px-5 bg-white rounded-3xl text-center animate-fadeIn">
      <div className="pt-4 flex items-center justify-center gap-1.5 text-xs font-bold text-emerald-600 bg-emerald-50 py-1 px-3 rounded-full border border-emerald-200 w-fit mx-auto">
        <CheckCircle2 className="w-4 h-4" />
        <span>Akun Berhasil Dibuat</span>
      </div>

      {/* House with Wi-Fi symbol illustration (Exact matching Sheet 5 Screen 3) */}
      <div className="my-auto py-6 flex flex-col items-center">
        <div className="relative w-48 h-48 flex items-center justify-center">
          <div className="absolute inset-0 rounded-full bg-red-50 blur-xl scale-95" />

          {/* Stylized Modern House Card */}
          <div className="relative z-10 w-36 h-36 rounded-3xl bg-gradient-to-tr from-red-600 to-rose-500 p-1 shadow-xl flex items-center justify-center">
            <div className="w-full h-full rounded-[22px] bg-white flex flex-col items-center justify-center p-3 text-red-600">
              <div className="relative">
                <Home className="w-16 h-16 text-red-600" />
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 p-1.5 rounded-full bg-red-600 text-white shadow-md animate-bounce">
                  <Wifi className="w-4 h-4" />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 space-y-2 max-w-xs mx-auto">
          <h2 className="text-xl font-black text-slate-900 tracking-tight leading-snug">
            Selamat Datang di MoreAI
          </h2>
          <p className="text-xs text-slate-500 font-medium leading-relaxed">
            Akun MoreAI Anda siap digunakan. Akses jaringan partner dan benefit AI akan ditampilkan setelah diverifikasi oleh layanan terkait.
          </p>
        </div>

        <div className="mt-5 p-3.5 rounded-2xl bg-slate-50 border border-slate-100 text-left text-xs text-slate-700 w-full max-w-xs space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>AI Credit: <strong>Menunggu entitlement</strong></span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>Koneksi Wi-Fi Partner <strong>Belum diverifikasi</strong></span>
          </div>
        </div>
      </div>

      {/* Button Mulai */}
      <div className="pb-2">
        <button
          onClick={() => onNavigate('home')}
          className="w-full py-3.5 rounded-2xl bg-red-600 hover:bg-red-700 active:scale-95 text-white text-xs sm:text-sm font-bold transition shadow-xs flex items-center justify-center gap-2"
        >
          <span>Mulai Gunakan MoreAI</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
