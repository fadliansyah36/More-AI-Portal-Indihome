'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { ArrowLeft, CheckCircle2, FileText, Image as ImageIcon, FileSpreadsheet, ArrowRight, Loader2, AlertCircle } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { moreAiApi } from '@/lib/api/client';

type ArtifactRecord = {
  id: string;
  storage_path: string;
  mime_type: string | null;
  size_bytes: number | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
};

interface ArtifactsResultViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

const categoryFor = (mime: string | null, path: string): 'pdf' | 'image' | 'xlsx' | 'other' => {
  const ext = path.split('.').pop()?.toLowerCase();
  if (mime === 'application/pdf' || ext === 'pdf') return 'pdf';
  if (mime?.startsWith('image/')) return 'image';
  if (mime?.includes('spreadsheet') || ['xlsx', 'xls', 'csv'].includes(ext || '')) return 'xlsx';
  return 'other';
};

export const ArtifactsResultView: React.FC<ArtifactsResultViewProps> = ({ onBack, onNavigateTab }) => {
  const [filter, setFilter] = useState<'semua' | 'pdf' | 'image' | 'xlsx'>('semua');
  const [files, setFiles] = useState<ArtifactRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    moreAiApi<ArtifactRecord[]>('/api/v1/artifacts')
      .then((rows) => { if (active) setFiles(rows); })
      .catch((cause) => { if (active) setError(cause instanceof Error ? cause.message : 'Artefak tidak dapat dimuat.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const filtered = useMemo(() => files.filter((file) => filter === 'semua' || categoryFor(file.mime_type, file.storage_path) === filter), [files, filter]);

  const nameOf = (file: ArtifactRecord) => typeof file.metadata?.filename === 'string'
    ? file.metadata.filename
    : file.storage_path.split('/').pop() || file.storage_path;
  const sizeOf = (file: ArtifactRecord) => file.size_bytes == null
    ? 'Ukuran tidak tersedia'
    : file.size_bytes < 1024 * 1024
      ? (file.size_bytes / 1024).toFixed(1) + ' KB'
      : (file.size_bytes / (1024 * 1024)).toFixed(2) + ' MB';

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <button onClick={onBack} className="p-1 rounded-lg text-slate-400 hover:text-slate-700"><ArrowLeft className="w-5 h-5" /></button>
        <div className="text-center">
          <h1 className="text-base font-bold text-slate-900 leading-tight">Hasil Pekerjaan</h1>
          <span className="text-[10px] text-slate-500 font-medium">Artefak yang benar-benar tersimpan</span>
        </div>
        <div className="w-5" />
      </div>

      <div className="p-4 rounded-3xl bg-emerald-50 border border-emerald-200 flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-emerald-600 text-white flex items-center justify-center shrink-0"><CheckCircle2 className="w-5 h-5" /></div>
        <div>
          <h3 className="text-xs font-bold text-emerald-900">Riwayat artefak workspace</h3>
          <p className="text-[11px] text-emerald-700">Daftar ini berasal dari metadata artefak milik akun yang sedang login.</p>
        </div>
      </div>

      <div className="flex items-center gap-1 p-1 bg-white rounded-2xl border border-slate-200 shadow-2xs">
        {([{ id: 'semua', label: 'Semua' }, { id: 'pdf', label: 'Dokumen' }, { id: 'image', label: 'Gambar' }, { id: 'xlsx', label: 'Data' }] as const).map((tab) => (
          <button key={tab.id} onClick={() => setFilter(tab.id)} className={`flex-1 py-1.5 text-xs font-semibold rounded-xl transition ${filter === tab.id ? 'bg-red-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'}`}>{tab.label}</button>
        ))}
      </div>

      <div className="space-y-2.5">
        {loading ? (
          <div className="p-8 flex items-center justify-center gap-2 text-xs text-slate-500"><Loader2 className="w-4 h-4 animate-spin" /> Memuat artefak...</div>
        ) : error ? (
          <div role="alert" className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex gap-2"><AlertCircle className="w-4 h-4 shrink-0" />{error}</div>
        ) : filtered.length === 0 ? (
          <div className="p-8 text-center rounded-3xl bg-white border border-slate-100 text-slate-500 text-xs">Belum ada artefak tersimpan pada filter ini.</div>
        ) : filtered.map((file) => {
          const category = categoryFor(file.mime_type, file.storage_path);
          return (
            <div key={file.id} className="p-3.5 rounded-2xl bg-white border border-slate-100 shadow-2xs flex items-center justify-between">
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-10 h-10 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-center shrink-0">
                  {category === 'pdf' ? <FileText className="w-5 h-5 text-red-600" /> : category === 'image' ? <ImageIcon className="w-5 h-5 text-amber-600" /> : <FileSpreadsheet className="w-5 h-5 text-emerald-600" />}
                </div>
                <div className="min-w-0">
                  <h4 className="text-xs font-bold text-slate-900 truncate">{nameOf(file)}</h4>
                  <p className="text-[10px] text-slate-500 mt-0.5">{sizeOf(file)} · {new Date(file.created_at).toLocaleString('id-ID')}</p>
                </div>
              </div>
              <span className="text-[10px] text-slate-400">Tersimpan</span>
            </div>
          );
        })}
      </div>

      <button onClick={() => onNavigateTab('files')} className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition shadow-xs flex items-center justify-center gap-2">
        <span>Buka di Workspace</span><ArrowRight className="w-4 h-4" />
      </button>
    </div>
  );
};
