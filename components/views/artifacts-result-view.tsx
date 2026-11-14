'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { ArrowLeft, CheckCircle2, FileText, Image as ImageIcon, FileSpreadsheet, ArrowRight, Loader2, AlertCircle, Download, Video } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { artifactApi, browserSessionApi, type CustomerBrowserSession } from '@/lib/api/client';

type ArtifactRecord = {
  id: string;
  storage_path: string;
  mime_type: string | null;
  size_bytes: number | null;
  run_id: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
};

interface ArtifactsResultViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

const categoryFor = (mime: string | null, path: string): 'pdf' | 'image' | 'video' | 'xlsx' | 'other' => {
  const ext = path.split('.').pop()?.toLowerCase();
  if (mime === 'application/pdf' || ext === 'pdf') return 'pdf';
  if (mime?.startsWith('image/')) return 'image';
  if (mime?.startsWith('video/') || ['mp4', 'webm', 'mov', 'm4v'].includes(ext || '')) return 'video';
  if (mime?.includes('spreadsheet') || ['xlsx', 'xls', 'csv'].includes(ext || '')) return 'xlsx';
  return 'other';
};

export const ArtifactsResultView: React.FC<ArtifactsResultViewProps> = ({ onBack, onNavigateTab }) => {
  const [filter, setFilter] = useState<'semua' | 'pdf' | 'image' | 'video' | 'xlsx'>('semua');
  const [files, setFiles] = useState<ArtifactRecord[]>([]);
  const [sessions, setSessions] = useState<CustomerBrowserSession[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const [sessionError, setSessionError] = useState<string | null>(null);
  const [closingSessionId, setClosingSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloadingFile, setDownloadingFile] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const [paginationError, setPaginationError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    browserSessionApi.list().then((result) => { if (active) setSessions(result.items); })
      .catch((cause) => { if (active) setSessionError(cause instanceof Error ? cause.message : 'Sesi browser tidak dapat dimuat.'); })
      .finally(() => { if (active) setSessionsLoading(false); });
    artifactApi.listPage(50)
      .then((page) => { if (active) { setFiles(page.items); setNextCursor(page.nextCursor); } })
      .catch((cause) => { if (active) setError(cause instanceof Error ? cause.message : 'Artefak tidak dapat dimuat.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const closeBrowserSession = async (sessionId: string) => {
    if (closingSessionId) return;
    setClosingSessionId(sessionId); setSessionError(null);
    try { await browserSessionApi.close(sessionId); setSessions((current) => current.filter((session) => session.id !== sessionId)); }
    catch (cause) { setSessionError(cause instanceof Error ? cause.message : 'Sesi browser tidak dapat ditutup.'); }
    finally { setClosingSessionId(null); }
  };

  const loadMore = async () => {
    if (!nextCursor || loadingMore) return;
    setLoadingMore(true);
    setPaginationError(null);
    try {
      const page = await artifactApi.listPage(50, nextCursor);
      setFiles((current) => {
        const known = new Set(current.map((file) => file.id));
        return [...current, ...page.items.filter((file) => !known.has(file.id))];
      });
      setNextCursor(page.nextCursor);
    } catch (cause) {
      setPaginationError(cause instanceof Error ? cause.message : 'Halaman artefak berikutnya tidak dapat dimuat.');
    } finally {
      setLoadingMore(false);
    }
  };

  const filtered = useMemo(() => files.filter((file) => filter === 'semua' || categoryFor(file.mime_type, file.storage_path) === filter), [files, filter]);

  const nameOf = (file: ArtifactRecord) => typeof file.metadata?.filename === 'string'
    ? file.metadata.filename
    : file.storage_path.split('/').pop() || file.storage_path;
  const downloadArtifact = async (artifactId: string) => {
    if (downloadingFile) return;
    setDownloadingFile(artifactId);
    try {
      const result = await artifactApi.signedDownload(artifactId);
      window.open(result.url, '_blank', 'noopener,noreferrer');
      setError(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Tautan unduhan artefak tidak dapat dibuat.');
    } finally {
      setDownloadingFile(null);
    }
  };

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

      <section className="rounded-3xl border border-slate-200 bg-white p-4 space-y-3">
        <div className="flex items-center justify-between gap-2"><div><h2 className="text-sm font-bold text-slate-900">Browser Sessions</h2><p className="text-[11px] text-slate-500 mt-0.5">Sesi OpenFuse tersimpan untuk akun Anda</p></div><span className="rounded-full bg-slate-100 px-2.5 py-1 text-[10px] font-semibold text-slate-600">{sessions.length} aktif</span></div>
        {sessionsLoading ? <div className="py-3 text-xs text-slate-500 flex items-center gap-2"><Loader2 className="w-4 h-4 animate-spin" />Memuat sesi browser…</div>
          : sessionError ? <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">{sessionError}</div>
          : sessions.length === 0 ? <p className="rounded-xl bg-slate-50 p-3 text-xs text-slate-500">Tidak ada sesi browser aktif.</p>
          : sessions.map((session) => <div key={session.id} className="rounded-2xl border border-slate-100 p-3 space-y-2">
            <div className="flex items-center justify-between gap-2"><span className="truncate text-xs font-bold text-slate-900">{session.origin_host}</span><span className="rounded-full bg-emerald-50 px-2 py-1 text-[10px] font-semibold text-emerald-700">Aktif</span></div>
            <p className="text-[10px] text-slate-500">Terakhir digunakan: {new Date(session.last_used_at).toLocaleString('id-ID')}</p>
            <p className="text-[10px] text-slate-500">Berakhir: {new Date(session.expires_at).toLocaleString('id-ID')}</p>
            <p className="text-[10px] text-slate-500">Agent Run: {(session.last_run_id || session.run_id).slice(0, 12)}</p>
            <button type="button" disabled={closingSessionId === session.id} onClick={() => void closeBrowserSession(session.id)} className="rounded-xl border border-rose-200 px-3 py-2 text-[10px] font-semibold text-rose-700 disabled:opacity-50">{closingSessionId === session.id ? 'Menutup…' : 'Tutup sesi'}</button>
          </div>)}
      </section>

      <div className="p-4 rounded-3xl bg-emerald-50 border border-emerald-200 flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-emerald-600 text-white flex items-center justify-center shrink-0"><CheckCircle2 className="w-5 h-5" /></div>
        <div>
          <h3 className="text-xs font-bold text-emerald-900">Riwayat artefak workspace</h3>
          <p className="text-[11px] text-emerald-700">Daftar ini berasal dari metadata artefak milik akun yang sedang login.</p>
        </div>
      </div>

      <div className="flex items-center gap-1 p-1 bg-white rounded-2xl border border-slate-200 shadow-2xs">
        {([{ id: 'semua', label: 'Semua' }, { id: 'pdf', label: 'Dokumen' }, { id: 'image', label: 'Gambar' }, { id: 'video', label: 'Video' }, { id: 'xlsx', label: 'Data' }] as const).map((tab) => (
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
                  {category === 'pdf' ? <FileText className="w-5 h-5 text-red-600" /> : category === 'image' ? <ImageIcon className="w-5 h-5 text-amber-600" /> : category === 'video' ? <Video className="w-5 h-5 text-blue-600" /> : <FileSpreadsheet className="w-5 h-5 text-emerald-600" />}
                </div>
                <div className="min-w-0">
                  <h4 className="text-xs font-bold text-slate-900 truncate">{nameOf(file)}</h4>
                  <p className="text-[10px] text-slate-500 mt-0.5">{sizeOf(file)} · {new Date(file.created_at).toLocaleString('id-ID')}</p>
                  <p className="mt-1 text-[10px] text-slate-500">{file.run_id ? 'Agent Run ' + file.run_id.slice(0, 8) : 'Belum ditautkan ke Agent Run'}</p>
                  {file.metadata?.source === 'openfuse_browser_download' && <p className="mt-1 text-[10px] text-slate-600">OpenFuse Browser · Scan: {String(file.metadata.scan_status || 'tidak tersedia')}</p>}
                </div>
              </div>
              <button type="button" onClick={() => void downloadArtifact(file.id)} disabled={downloadingFile === file.id} className="inline-flex shrink-0 items-center gap-1 rounded-xl border border-slate-200 px-3 py-2 text-[10px] font-semibold text-slate-700 disabled:opacity-50">
                {downloadingFile === file.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />}
                Unduh
              </button>
            </div>
          );
        })}
      </div>

      {paginationError && <div role="alert" className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">{paginationError}</div>}
      {!loading && nextCursor && (
        <button type="button" onClick={() => void loadMore()} disabled={loadingMore}
          className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-xs font-semibold text-slate-700 disabled:opacity-50">
          {loadingMore ? 'Memuat artefak…' : 'Muat artefak berikutnya'}
        </button>
      )}
      <button onClick={() => onNavigateTab('files')} className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition shadow-xs flex items-center justify-center gap-2">
        <span>Buka di Workspace</span><ArrowRight className="w-4 h-4" />
      </button>
    </div>
  );
};
