'use client';

import React from 'react';
import { MoreAiIcon, IndiHomeLogo } from '@/components/branding/logos';
import { ArrowRight, Sparkles } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';

interface SplashScreenViewProps {
  onNavigate: (tab: NavigationTab) => void;
}

export const SplashScreenView: React.FC<SplashScreenViewProps> = ({ onNavigate }) => {
  return (
    <div className="min-h-[680px] flex flex-col justify-between py-6 px-4 bg-gradient-to-b from-white via-rose-50/30 to-red-50/60 rounded-3xl text-center animate-fadeIn relative overflow-hidden">
      {/* Top Header */}
      <div className="pt-6 flex flex-col items-center">
        <div className="flex items-center gap-2 mb-2">
          <MoreAiIcon size={44} />
          <span className="text-3xl font-black tracking-tight text-slate-900">
            More<span className="text-red-600">AI</span>
          </span>
        </div>
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-widest">
          AI Workspace Platform
        </span>

        <div className="mt-4 inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-red-100/80 text-red-700 text-[11px] font-bold">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Akses AI x IndiHome</span>
        </div>
      </div>

      {/* Center Illustration: Jakarta Skyline & Monas Silhouette */}
      <div className="my-8 relative flex flex-col items-center justify-center">
        <div className="w-48 h-48 rounded-full bg-gradient-to-tr from-red-600/10 via-rose-500/15 to-amber-500/10 flex items-center justify-center p-4">
          <div className="w-36 h-36 rounded-full bg-white shadow-xl border border-red-100 flex flex-col items-center justify-center p-3 text-center">
            {/* Monas & Skyline Icon graphic */}
            <svg viewBox="0 0 100 100" className="w-20 h-20 text-red-600 fill-current">
              {/* Monas Monument silhouette */}
              <polygon points="46,10 54,10 52,40 48,40" />
              <polygon points="44,40 56,40 58,70 42,70" />
              <rect x="36" y="70" width="28" height="8" rx="1" />
              <rect x="30" y="78" width="40" height="12" rx="2" />
              {/* Surrounding city buildings */}
              <rect x="10" y="55" width="14" height="35" rx="1" opacity="0.3" />
              <rect x="76" y="50" width="16" height="40" rx="1" opacity="0.3" />
              <rect x="22" y="65" width="10" height="25" rx="1" opacity="0.2" />
              <rect x="68" y="62" width="10" height="28" rx="1" opacity="0.2" />
            </svg>
            <span className="text-[10px] font-black text-red-600 mt-1 uppercase tracking-wide">
              Indonesia
            </span>
          </div>
        </div>

        <div className="mt-6 space-y-1">
          <h2 className="text-xl font-black text-slate-900 tracking-tight">
            Akses AI untuk Semua
          </h2>
          <p className="text-xs text-slate-500 font-medium max-w-xs mx-auto">
            Produktivitas untuk Indonesia. Dari belajar, bekerja, hingga berkreasi, semua bisa lebih mudah dengan MoreAI.
          </p>
        </div>
      </div>

      {/* Bottom Action Buttons */}
      <div className="space-y-2.5 pb-2">
        <button
          onClick={() => onNavigate('onboarding')}
          className="w-full py-3.5 rounded-2xl bg-red-600 hover:bg-red-700 active:scale-95 text-white text-xs sm:text-sm font-bold transition shadow-md flex items-center justify-center gap-2"
        >
          <span>Mulai Sekarang</span>
          <ArrowRight className="w-4 h-4" />
        </button>

        <button
          onClick={() => onNavigate('login')}
          className="w-full py-2.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition"
        >
          Lewati &amp; Langsung Masuk
        </button>

        <div className="pt-2 flex items-center justify-center opacity-85">
          <IndiHomeLogo showTelkom={false} />
        </div>
      </div>
    </div>
  );
};
