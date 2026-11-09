'use client';

import React, { useState } from 'react';
import { usePWAInstall } from '@/hooks/use-pwa-install';
import { useToast } from '@/components/ui/toast-context';
import { Download, Share2, PlusSquare, X } from 'lucide-react';

export const PWAInstallButton: React.FC<{ compact?: boolean }> = ({ compact = false }) => {
  const { isInstallable, isInstalled, isIOS, install } = usePWAInstall();
  const [showIOSGuide, setShowIOSGuide] = useState(false);
  const { showToast } = useToast();

  // If already running as an installed PWA, hide the button
  if (isInstalled) {
    return null;
  }

  // Chromium / Android / Desktop flow
  if (isInstallable) {
    return (
      <button
        onClick={install}
        className={`flex items-center gap-1.5 font-medium rounded-xl bg-gradient-to-r from-red-600 to-rose-600 text-white shadow-sm hover:from-red-700 hover:to-rose-700 active:scale-95 transition-all ${
          compact ? 'px-2.5 py-1 text-xs' : 'px-3.5 py-1.5 text-xs'
        }`}
        title="Install Aplikasi PWA MoreAI"
      >
        <Download className="w-3.5 h-3.5 shrink-0" />
        <span className="hidden sm:inline">Install PWA</span>
        <span className="sm:hidden text-[11px] font-semibold">Install</span>
      </button>
    );
  }

  // iOS Safari flow
  if (isIOS) {
    return (
      <>
        <button
          onClick={() => setShowIOSGuide(true)}
          className={`flex items-center gap-1.5 font-medium rounded-xl border border-red-200 bg-red-50 text-red-700 hover:bg-red-100 transition-all ${
            compact ? 'px-2.5 py-1 text-xs' : 'px-3 py-1.5 text-xs'
          }`}
          title="Install MoreAI di iPhone/iPad"
        >
          <Download className="w-3.5 h-3.5 shrink-0" />
          <span className="hidden sm:inline">Install App</span>
          <span className="sm:hidden text-[11px] font-semibold">Install</span>
        </button>

        {showIOSGuide && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-fadeIn">
            <div className="w-full max-w-sm rounded-2xl bg-white p-5 shadow-2xl border border-slate-100 text-slate-800">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-red-600 flex items-center justify-center text-white font-bold text-sm">
                    M
                  </div>
                  <h3 className="text-base font-semibold text-slate-900">Install di iOS</h3>
                </div>
                <button
                  onClick={() => setShowIOSGuide(false)}
                  className="p-1 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="mt-4 space-y-3 text-xs text-slate-600">
                <div className="flex items-start gap-3 p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                  <Share2 className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
                  <p>
                    1. Buka halaman ini di <strong>Safari</strong> lalu ketuk tombol <strong>Bagikan (Share)</strong> di bilah bawah.
                  </p>
                </div>
                <div className="flex items-start gap-3 p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                  <PlusSquare className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
                  <p>
                    2. Gulir ke bawah dan pilih <strong>Tambahkan ke Layar Utama (Add to Home Screen)</strong>.
                  </p>
                </div>
              </div>

              <button
                onClick={() => setShowIOSGuide(false)}
                className="mt-5 w-full rounded-xl bg-slate-900 py-2.5 text-xs font-medium text-white hover:bg-slate-800 transition"
              >
                Mengerti
              </button>
            </div>
          </div>
        )}
      </>
    );
  }

  // Fallback direct install button for browser exploration
  return (
    <button
      onClick={() => showToast('PWA Siap: Anda dapat menambahkan MoreAI ke Layar Utama melalui menu browser Anda atau klik Pasang.', 'info')}
      className={`flex items-center gap-1.5 font-medium rounded-xl border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 active:scale-95 transition-all ${
        compact ? 'px-2 py-1 text-xs' : 'px-3 py-1.5 text-xs'
      }`}
      title="Aplikasi PWA Siap Dipasang"
    >
      <Download className="w-3.5 h-3.5 text-red-600 shrink-0" />
      <span className="hidden sm:inline">Install PWA</span>
      <span className="sm:hidden text-[11px] font-semibold">Install</span>
    </button>
  );
};
