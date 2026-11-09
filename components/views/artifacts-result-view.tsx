'use client';

import React, { useState } from 'react';
import { ArrowLeft, CheckCircle2, FileText, Image as ImageIcon, FileSpreadsheet, Download, ArrowRight } from 'lucide-react';
import { ARTIFACT_FILES } from '@/lib/data';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';

interface ArtifactsResultViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

export const ArtifactsResultView: React.FC<ArtifactsResultViewProps> = ({
  onBack,
  onNavigateTab,
}) => {
  const { showToast } = useToast();
  const [filter, setFilter] = useState<'semua' | 'pdf' | 'image' | 'xlsx'>('semua');

  const filtered = ARTIFACT_FILES.slice(0, 3).filter((f) =>
    filter === 'semua' ? true : f.type === filter
  );

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <button onClick={onBack} className="p-1 rounded-lg text-slate-400 hover:text-slate-700">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="text-center">
          <h1 className="text-base font-bold text-slate-900 leading-tight">Hasil Pekerjaan</h1>
          <span className="text-[10px] text-slate-500 font-medium">Output campaign &amp; berkas final</span>
        </div>
        <div className="w-5" />
      </div>

      {/* Success Notification Banner (Sheet 6 Screen 8) */}
      <div className="p-4 rounded-3xl bg-emerald-50 border border-emerald-200 flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-emerald-600 text-white flex items-center justify-center shrink-0">
          <CheckCircle2 className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-xs font-bold text-emerald-900">Pekerjaan berhasil diselesaikan!</h3>
          <p className="text-[11px] text-emerald-700">Semua agent telah merampungkan tugas dan menyimpan artefak.</p>
        </div>
      </div>

      {/* Tabs Filter (Semua, Dokumen, Gambar, Data) */}
      <div className="flex items-center gap-1 p-1 bg-white rounded-2xl border border-slate-200 shadow-2xs">
        <button
          onClick={() => setFilter('semua')}
          className={`flex-1 py-1.5 text-xs font-semibold rounded-xl transition ${
            filter === 'semua' ? 'bg-red-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          Semua
        </button>
        <button
          onClick={() => setFilter('pdf')}
          className={`flex-1 py-1.5 text-xs font-semibold rounded-xl transition ${
            filter === 'pdf' ? 'bg-red-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          Dokumen
        </button>
        <button
          onClick={() => setFilter('image')}
          className={`flex-1 py-1.5 text-xs font-semibold rounded-xl transition ${
            filter === 'image' ? 'bg-red-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          Gambar
        </button>
        <button
          onClick={() => setFilter('xlsx')}
          className={`flex-1 py-1.5 text-xs font-semibold rounded-xl transition ${
            filter === 'xlsx' ? 'bg-red-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          Data
        </button>
      </div>

      {/* Artifact Files List (Sheet 6 Screen 8) */}
      <div className="space-y-2.5">
        {filtered.map((file) => (
          <div
            key={file.id}
            className="p-3.5 rounded-2xl bg-white border border-slate-100 shadow-2xs flex items-center justify-between"
          >
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-10 h-10 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-center shrink-0">
                {file.type === 'pdf' && <FileText className="w-5 h-5 text-red-600" />}
                {file.type === 'image' && <ImageIcon className="w-5 h-5 text-amber-600" />}
                {file.type === 'xlsx' && <FileSpreadsheet className="w-5 h-5 text-emerald-600" />}
              </div>
              <div className="min-w-0">
                <h4 className="text-xs font-bold text-slate-900 truncate">{file.name}</h4>
                <p className="text-[10px] text-slate-500 mt-0.5">{file.size}</p>
              </div>
            </div>

            <button
              onClick={() => showToast(`Mengunduh berkas ${file.name}... Berkas siap dibuka.`, 'success')}
              className="p-2 rounded-xl bg-slate-50 hover:bg-red-50 text-slate-600 hover:text-red-600 border border-slate-200 transition"
              title="Unduh"
            >
              <Download className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>

      {/* Button Buka di Workspace */}
      <button
        onClick={() => onNavigateTab('files')}
        className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition shadow-xs flex items-center justify-center gap-2"
      >
        <span>Buka di Workspace</span>
        <ArrowRight className="w-4 h-4" />
      </button>
    </div>
  );
};
