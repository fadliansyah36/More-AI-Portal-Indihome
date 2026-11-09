'use client';

import React from 'react';
import { ArrowLeft, Megaphone, Image as ImageIcon, FileText, Download, CheckCircle2 } from 'lucide-react';
import { useToast } from '@/components/ui/toast-context';

interface PartnerPromoViewProps {
  onBack: () => void;
}

export const PartnerPromoView: React.FC<PartnerPromoViewProps> = ({ onBack }) => {
  const { showToast } = useToast();
  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <button onClick={onBack} className="p-1 rounded-lg text-slate-400 hover:text-slate-700">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="text-center">
          <h1 className="text-base font-bold text-slate-900 leading-tight">Promo &amp; Materi Partner</h1>
          <span className="text-[10px] text-slate-500 font-medium">Kit pemasaran fisik &amp; digital venue</span>
        </div>
        <div className="w-5" />
      </div>

      {/* Top Banner */}
      <div className="p-4 rounded-3xl bg-gradient-to-r from-red-600 to-rose-600 text-white shadow-xs">
        <h3 className="text-sm font-bold">Dukung Penggunaan MoreAI di Lokasi Anda</h3>
        <p className="text-xs text-red-100 mt-0.5">
          Tingkatkan kepuasan pengunjung dan durasi kunjungan dengan materi promosi resmi Wi-Fi &amp; AI gratis.
        </p>
      </div>

      {/* Promo Material Categories (Sheet 4 Screen 12) */}
      <div className="space-y-2.5">
        <div className="p-4 rounded-2xl bg-white border border-slate-100 shadow-2xs space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-red-50 text-red-600 flex items-center justify-center">
                <ImageIcon className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-900">Materi Promosi Fisik</h4>
                <p className="text-[10px] text-slate-500">Poster A3, X-Banner Standing, &amp; Stiker Meja QR</p>
              </div>
            </div>
            <button
              onClick={() => showToast('Mengunduh Bundle Cetak Promosi (PDF Siap Cetak 300 DPI)...', 'success')}
              className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700"
              title="Unduh Paket Cetak"
            >
              <Download className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-slate-100 shadow-2xs space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                <FileText className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-900">Template Konten Media Sosial</h4>
                <p className="text-[10px] text-slate-500">Feeds Instagram, Stories, &amp; Storyboard Video Reels</p>
              </div>
            </div>
            <button
              onClick={() => showToast('Mengunduh Template Canva & Figma Media Sosial...', 'success')}
              className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700"
              title="Unduh Template"
            >
              <Download className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-slate-100 shadow-2xs space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
                <Megaphone className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-900">Program &amp; Kampanye Khusus</h4>
                <p className="text-[10px] text-slate-500">Reward aktivasi pengunjung &amp; giveaway kuota AI</p>
              </div>
            </div>
            <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
              Aktif
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
