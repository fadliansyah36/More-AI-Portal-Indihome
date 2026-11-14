'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { Archive, BookOpen, RefreshCw, Search, FileText, Loader2, RotateCcw } from 'lucide-react';
import { knowledgeApi, type CustomerKnowledgeDocument } from '@/lib/api/knowledge';

const statusLabel: Record<CustomerKnowledgeDocument['status'], string> = {
  processing: 'Sedang diproses',
  ready: 'Siap digunakan',
  failed: 'Gagal diproses',
  archived: 'Diarsipkan',
};

export const KnowledgeLibraryView: React.FC = () => {
  const [documents, setDocuments] = useState<CustomerKnowledgeDocument[]>([]);
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState<'all' | CustomerKnowledgeDocument['status']>('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const [paginationError, setPaginationError] = useState<string | null>(null);
  const [detailId, setDetailId] = useState<string | null>(null);
  const [detail, setDetail] = useState<Awaited<ReturnType<typeof knowledgeApi.get>> | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const result = await knowledgeApi.listPage({ limit: 50, ...(status === 'all' ? {} : { status }) });
      setDocuments(result.items);
      setNextCursor(result.nextCursor);
      setPaginationError(null);
      setError(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Knowledge Library tidak dapat dimuat.');
    } finally {
      setLoading(false);
    }
  }, [status]);

  useEffect(() => {
    let active = true;
    void Promise.resolve().then(() => { if (active) void load(); });
    return () => { active = false; };
  }, [load]);

  const openDocumentDetail = async (documentId: string) => {
    if (detailId === documentId) {
      setDetailId(null);
      setDetail(null);
      return;
    }
    setDetailId(documentId);
    setDetailLoading(true);
    setDetailError(null);
    try {
      const result = await knowledgeApi.get(documentId, { limit: 100 });
      setDetail(result);
    } catch (cause) {
      setDetailError(cause instanceof Error ? cause.message : 'Detail ingestion tidak dapat dimuat.');
    } finally {
      setDetailLoading(false);
    }
  };

  const loadMoreChunks = async () => {
    if (detail?.next_after_chunk_index === null || detail?.next_after_chunk_index === undefined || detailLoading || !detailId) return;
    setDetailLoading(true);
    setDetailError(null);
    try {
      const page = await knowledgeApi.chunksPage(detailId, 100, detail.next_after_chunk_index);
      setDetail((current) => current ? {
        ...page,
        chunks: [...current.chunks, ...page.chunks.filter((chunk) => !current.chunks.some((known) => known.id === chunk.id))],
      } : page);
    } catch (cause) {
      setDetailError(cause instanceof Error ? cause.message : 'Chunk knowledge berikutnya tidak dapat dimuat.');
    } finally {
      setDetailLoading(false);
    }
  };

  const loadMore = async () => {
    if (!nextCursor || loadingMore) return;
    setLoadingMore(true);
    setPaginationError(null);
    try {
      const page = await knowledgeApi.listPage({
        limit: 50, cursor: nextCursor, ...(status === 'all' ? {} : { status }),
      });
      setDocuments((current) => {
        const known = new Set(current.map((item) => item.id));
        return [...current, ...page.items.filter((item) => !known.has(item.id))];
      });
      setNextCursor(page.nextCursor);
    } catch (cause) {
      setPaginationError(cause instanceof Error ? cause.message : 'Halaman dokumen berikutnya tidak dapat dimuat.');
    } finally {
      setLoadingMore(false);
    }
  };

  const upload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    try {
      await knowledgeApi.upload(file);
      setStatus('all');
      setLoading(true);
      await knowledgeApi.listPage({ limit: 50 }).then((result) => { setDocuments(result.items); setNextCursor(result.nextCursor); });
    } catch (cause) {
      setUploadError(cause instanceof Error ? cause.message : 'File tidak dapat diunggah.');
    } finally {
      setUploading(false);
      setLoading(false);
    }
  };

  const retry = async (document: CustomerKnowledgeDocument) => {
    setBusyId(document.id);
    setError(null);
    try {
      await knowledgeApi.reindex(document.id);
      setDocuments((items) => items.map((item) => item.id === document.id ? { ...item, status: 'processing' } : item));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Dokumen tidak dapat dimasukkan kembali ke antrean.');
    } finally {
      setBusyId(null);
    }
  };

  const archive = async (document: CustomerKnowledgeDocument) => {
    if (document.status !== 'ready' && document.status !== 'failed') return;
    setBusyId(document.id);
    try {
      await knowledgeApi.archive(document.id);
      setDocuments((items) => items.map((item) => item.id === document.id ? { ...item, status: 'archived' } : item));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Dokumen tidak dapat diarsipkan.');
    } finally {
      setBusyId(null);
    }
  };

  const visible = documents.filter((document) => document.title.toLowerCase().includes(query.toLowerCase()));

  return (
    <section className="space-y-4 pb-20">
      <header className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">Knowledge Library</h1>
          <p className="mt-1 text-xs text-slate-500">Dokumen tenant-scoped yang dapat digunakan Agent Runtime melalui semantic retrieval.</p>
        </div>
        <div className="flex items-center gap-2">
          <label className="inline-flex cursor-pointer items-center gap-2 rounded-xl bg-red-600 px-3 py-2 text-xs font-semibold text-white hover:bg-red-700">
            <FileText className="h-4 w-4" /> {uploading ? 'Mengunggah…' : 'Upload file'}
            <input type="file" accept=".pdf,.jpg,.jpeg,.png,.webp,application/pdf,image/jpeg,image/png,image/webp" onChange={(event) => void upload(event)} disabled={uploading} className="sr-only" />
          </label>
          <button type="button" onClick={() => { setLoading(true); setError(null); void load(); }} disabled={loading} className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 disabled:opacity-50">
            <RefreshCw className={loading ? 'h-4 w-4 animate-spin' : 'h-4 w-4'} /> Refresh
          </button>
        </div>
      </header>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Cari judul knowledge…" className="w-full rounded-2xl border border-slate-200 bg-white py-3 pl-10 pr-4 text-sm text-slate-900 outline-none focus:border-red-500" />
      </div>

      <div className="flex flex-wrap gap-2">
        {(['all', 'ready', 'processing', 'failed', 'archived'] as const).map((value) => (
          <button key={value} type="button" onClick={() => { setLoading(true); setError(null); setStatus(value); }} className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${status === value ? 'bg-red-600 text-white' : 'border border-slate-200 bg-white text-slate-600'}`}>
            {value === 'all' ? 'Semua' : statusLabel[value]}
          </button>
        ))}
      </div>

      {(error || uploadError) && <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-3 text-xs text-red-700">{uploadError || error}</div>}
      <p className="text-[11px] text-slate-500">Pilih PDF atau gambar langsung dari file manager perangkat. Maksimum 25 MiB per file.</p>
      {loading ? (
        <div className="flex items-center justify-center gap-2 rounded-2xl border border-slate-100 bg-white p-10 text-sm text-slate-500"><Loader2 className="h-4 w-4 animate-spin" /> Memuat Knowledge Library…</div>
      ) : visible.length === 0 ? (
        <div className="rounded-2xl border border-slate-100 bg-white p-8 text-center">
          <BookOpen className="mx-auto mb-3 h-9 w-9 text-slate-300" />
          <p className="text-sm font-semibold text-slate-800">Belum ada dokumen knowledge</p>
          <p className="mt-1 text-xs text-slate-500">Dokumen akan muncul setelah Agent Runtime berhasil menjalankan knowledge_ingest.</p>
        </div>
      ) : visible.map((document) => (
        <article key={document.id} className="flex items-center gap-3 rounded-2xl border border-slate-100 bg-white p-4 shadow-xs">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-50 text-slate-600"><FileText className="h-5 w-5" /></div>
          <div className="min-w-0 flex-1">
            <h2 className="truncate text-sm font-semibold text-slate-900">{document.title}</h2>
            <p className="mt-1 text-[11px] text-slate-500">{statusLabel[document.status]} · {document.source_type} · {new Date(document.created_at).toLocaleString('id-ID')}</p>
            <p className="mt-1 truncate text-[10px] text-slate-400">SHA-256 {document.content_sha256}</p>
          </div>
          {(document.status === 'failed' || document.status === 'ready') && (
            <button type="button" onClick={() => void retry(document)} disabled={busyId === document.id} aria-label={document.status === "ready" ? "Bangun ulang indeks dokumen" : "Proses ulang dokumen"} title={document.status === "ready" ? "Re-index" : "Proses ulang"} className="rounded-xl border border-slate-200 p-2 text-slate-500 hover:bg-slate-50 disabled:opacity-50">
              {busyId === document.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <RotateCcw className="h-4 w-4" />}
            </button>
          )}
          {(document.status === 'ready' || document.status === 'failed') && (
            <button type="button" onClick={() => void archive(document)} disabled={busyId === document.id} aria-label="Arsipkan dokumen" className="rounded-xl border border-slate-200 p-2 text-slate-500 hover:bg-slate-50 disabled:opacity-50">
              {busyId === document.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Archive className="h-4 w-4" />}
            </button>
          )}
          <button type="button" onClick={() => void openDocumentDetail(document.id)} className="shrink-0 rounded-xl border border-slate-200 px-2.5 py-2 text-[10px] font-semibold text-slate-600">
            {detailId === document.id ? 'Tutup' : 'Chunks'}
          </button>
        </article>
      ))}
      {detailId && (
        <section className="rounded-2xl border border-slate-200 bg-white p-4">
          <div className="flex items-start justify-between gap-3">
            <div><h2 className="text-sm font-bold text-slate-900">Ingestion & chunk detail</h2><p className="mt-1 text-[11px] text-slate-500">Metadata chunk dari Knowledge API. Isi dokumen dan embedding privat tidak diekspos di panel ini.</p></div>
            <span className="rounded-full bg-slate-100 px-2 py-1 text-[10px] font-semibold text-slate-600">{detail ? detail.total_chunk_count + ' chunks' : 'Memuat'}</span>
          </div>
          {detailLoading && <p className="mt-3 text-xs text-slate-500">Memuat detail knowledge…</p>}
          {detailError && <p role="alert" className="mt-3 rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-700">{detailError}</p>}
          {detail && (
            <>
              <p className="mt-3 text-[11px] text-slate-600">Status ingestion: <strong>{detail.document.status}</strong> · Dimuat {detail.chunks.length} dari {detail.total_chunk_count} chunk</p>
              <div className="mt-3 space-y-2">
                {detail.chunks.map((chunk) => (
                  <div key={chunk.id} className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2">
                    <span className="text-[11px] font-medium text-slate-700">Chunk #{chunk.chunk_index}</span>
                    <span className="text-[10px] text-slate-500">{chunk.token_count === null ? 'Token count tidak tersedia' : chunk.token_count + ' tokens'}</span>
                  </div>
                ))}
              </div>
              {detail.next_after_chunk_index !== null && (
                <button type="button" onClick={() => void loadMoreChunks()} disabled={detailLoading} className="mt-3 w-full rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 disabled:opacity-50">
                  Muat chunk berikutnya
                </button>
              )}
            </>
          )}
        </section>
      )}
      {paginationError && <div role="alert" className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">{paginationError}</div>}
      {!loading && nextCursor && (
        <button type="button" onClick={() => void loadMore()} disabled={loadingMore}
          className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-xs font-semibold text-slate-700 disabled:opacity-50">
          {loadingMore ? 'Memuat dokumen…' : 'Muat dokumen berikutnya'}
        </button>
      )}
    </section>
  );
};
