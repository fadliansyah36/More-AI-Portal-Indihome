'use client';

import React, { useEffect, useState } from 'react';
import { knowledgeApi, type CustomerKnowledgeDocument } from '@/lib/api/knowledge';
import {
  UploadCloud,
    CheckCircle2,
  Sparkles,
} from 'lucide-react';

interface AnalyseViewProps { onNavigateToChat?: (prompt: string) => void; }

export const AnalyseView: React.FC<AnalyseViewProps> = ({ onNavigateToChat }) => {
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadState, setUploadState] = useState<'idle' | 'queued' | 'error'>('idle');
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [documents, setDocuments] = useState<CustomerKnowledgeDocument[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState('');
  const [documentsLoading, setDocumentsLoading] = useState(true);
  const [documentsError, setDocumentsError] = useState<string | null>(null);
  const [refreshingDocuments, setRefreshingDocuments] = useState(false);

  useEffect(() => {
    let active = true;
    knowledgeApi.list({ limit: 50 }).then(({ items }) => {
      if (active) {
        setDocuments(items);
        setSelectedDocumentId((current) => current || items.find((item) => item.status === 'ready')?.id || items[0]?.id || '');
      }
    }).catch((cause) => {
      if (active) setDocumentsError(cause instanceof Error ? cause.message : 'Knowledge Library tidak dapat dimuat.');
    }).finally(() => { if (active) setDocumentsLoading(false); });
    return () => { active = false; };
  }, []);

  const refreshDocuments = async () => {
    setRefreshingDocuments(true);
    setDocumentsError(null);
    try {
      const result = await knowledgeApi.list({ limit: 50 });
      setDocuments(result.items);
      setSelectedDocumentId((current) => current || result.items.find((item) => item.status === 'ready')?.id || result.items[0]?.id || '');
    } catch (cause) {
      setDocumentsError(cause instanceof Error ? cause.message : 'Knowledge Library tidak dapat dimuat.');
    } finally {
      setRefreshingDocuments(false);
    }
  };

  const analyzeSelectedDocument = () => {
    const document = documents.find((item) => item.id === selectedDocumentId);
    if (!document || document.status !== 'ready') {
      setDocumentsError('Dokumen harus selesai diindeks sebelum dapat dianalisis oleh Agent.');
      return;
    }
    if (!onNavigateToChat) {
      setDocumentsError('Chat AI belum terhubung. Tidak ada Agent Run yang dibuat.');
      return;
    }
    onNavigateToChat(
      'Lakukan analisis mendalam terhadap dokumen Knowledge Library yang dipilih. Wajib gunakan tool knowledge_search dengan query yang relevan dan document_ids berisi hanya ID berikut: [' + document.id + ']. Gunakan isi chunk sebagai sumber utama, kutip temuan secara jelas, pisahkan fakta dan inferensi, serta jangan mengarang isi yang tidak ditemukan. Judul dokumen: ' + document.title + '.'
    );
  };

  const handleStartAnalysis = async () => {
    if (!selectedFile || isAnalyzing) return;
    setIsAnalyzing(true);
    setUploadState('idle');
    setUploadMessage(null);
    try {
      const result = await knowledgeApi.upload(selectedFile);
      setUploadState(result.status === 'failed' ? 'error' : 'queued');
      setUploadMessage(result.status === 'ready'
        ? 'File identik sudah terindeks dan tersedia di Knowledge Library.'
        : result.status === 'failed'
          ? 'File identik sebelumnya gagal diproses. Buka Knowledge Library untuk menjalankan proses ulang.'
          : result.reused
            ? 'File identik sudah berada dalam antrean ingestion.'
            : 'File tersimpan secara privat dan masuk antrean ingestion. Status ekstraksi dan indexing dapat dipantau di Knowledge Library.');
      setSelectedFileName(result.upload.filename);
      setSelectedDocumentId(result.document.id);
      void refreshDocuments();
    } catch (cause) {
      setUploadState('error');
      setUploadMessage(cause instanceof Error ? cause.message : 'File gagal dikirim ke backend.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">Data & Document Analyse</h1>
        <p className="text-xs text-slate-500">
          Ekstrak insight kunci, ringkasan laporan keuangan, dan tren data secara instan
        </p>
      </div>

      {/* Upload Box (Exact from Sheet 2) */}
      <div className="p-6 rounded-3xl bg-white border-2 border-dashed border-slate-200 text-center space-y-3 hover:border-red-400 transition group">
        <div className="w-14 h-14 rounded-2xl bg-red-50 text-red-600 flex items-center justify-center mx-auto group-hover:scale-110 transition-transform">
          <UploadCloud className="w-7 h-7" />
        </div>

        <div>
          <h3 className="text-sm font-bold text-slate-900">
            Unggah file atau seret di sini
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Mendukung PDF dan gambar JPG, PNG, WEBP hingga 25 MiB
          </p>
        </div>

        <div>
          <label className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-900 text-white text-xs font-semibold hover:bg-slate-800 transition cursor-pointer shadow-xs active:scale-95">
            <span>Pilih File dari Perangkat</span>
            <input
              type="file"
              className="hidden"
              accept=".pdf,.jpg,.jpeg,.png,.webp,application/pdf,image/jpeg,image/png,image/webp"
              onChange={(e) => {
                const file = e.target.files?.[0] || null;
                setSelectedFile(file);
                setSelectedFileName(file?.name || null);
                setUploadState('idle');
                setUploadMessage(null);
                e.target.value = '';
              }}
            />
          </label>
        </div>

        {/* Selected File Notice */}
        {selectedFileName && (
          <div className="pt-2 text-xs font-semibold text-emerald-600 bg-emerald-50 py-1.5 px-3 rounded-xl border border-emerald-200 inline-flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4" />
            <span>File terpilih: {selectedFileName}</span>
          </div>
        )}
      </div>

      {/* Button Jalankan Analisis */}
      <button
        onClick={handleStartAnalysis}
        disabled={!selectedFile || isAnalyzing}
        className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 disabled:opacity-40 text-white text-xs font-bold transition shadow-xs flex items-center justify-center gap-2 active:scale-98"
      >
        <Sparkles className="w-4 h-4" />
        <span>{isAnalyzing ? 'Mengirim file ke backend…' : 'Unggah & Indeks Dokumen'}</span>
      </button>

      {uploadMessage && (
        <div role="status" className={`rounded-2xl border p-3 text-xs ${uploadState === 'error' ? 'border-red-200 bg-red-50 text-red-700' : 'border-emerald-200 bg-emerald-50 text-emerald-800'}`}>
          {uploadMessage}
        </div>
      )}

      <div className="rounded-3xl border border-slate-100 bg-white p-4 shadow-xs space-y-3">
        <div className="flex items-center justify-between gap-2">
          <div>
            <h2 className="text-xs font-bold text-slate-900">Dokumen Knowledge Library</h2>
            <p className="text-[10px] text-slate-500 mt-0.5">Pilih dokumen yang sudah terindeks untuk ditautkan ke Agent Run analisis.</p>
          </div>
          <button type="button" onClick={() => void refreshDocuments()} disabled={refreshingDocuments} className="rounded-lg border border-slate-200 px-2.5 py-1.5 text-[10px] font-semibold text-slate-600 disabled:opacity-50">
            {refreshingDocuments ? 'Memuat…' : 'Perbarui'}
          </button>
        </div>
        {documentsError && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 p-2.5 text-[10px] text-red-700">{documentsError}</p>}
        {documentsLoading ? <p className="text-[11px] text-slate-500">Memuat dokumen…</p> : documents.length === 0 ? (
          <p className="rounded-xl bg-slate-50 p-3 text-[11px] text-slate-500">Belum ada dokumen. Unggah PDF atau gambar di atas untuk memulai.</p>
        ) : (
          <div className="space-y-2">
            {documents.map((document) => (
              <button key={document.id} type="button" onClick={() => setSelectedDocumentId(document.id)} className={`w-full rounded-xl border p-3 text-left transition ${selectedDocumentId === document.id ? 'border-red-300 bg-red-50/50' : 'border-slate-200 bg-white'}`}>
                <div className="flex items-center justify-between gap-2">
                  <span className="min-w-0 truncate text-[11px] font-semibold text-slate-800">{document.title}</span>
                  <span className={`shrink-0 rounded-full px-2 py-0.5 text-[9px] font-semibold ${document.status === 'ready' ? 'bg-emerald-50 text-emerald-700' : document.status === 'failed' ? 'bg-red-50 text-red-700' : 'bg-amber-50 text-amber-700'}`}>{document.status}</span>
                </div>
                <p className="mt-1 text-[9px] text-slate-400">ID {document.id.slice(0, 8)} · {new Date(document.updated_at).toLocaleString('id-ID')}</p>
              </button>
            ))}
          </div>
        )}
        <button type="button" onClick={analyzeSelectedDocument} disabled={!onNavigateToChat || !documents.some((item) => item.id === selectedDocumentId && item.status === 'ready')} className="w-full rounded-2xl bg-red-600 py-3 text-xs font-bold text-white transition hover:bg-red-700 disabled:opacity-40">
          Analisis Dokumen dengan Agent AI
        </button>
        <p className="text-[10px] text-slate-500">Analisis membuat Agent Run baru melalui Chat. Retrieval dibatasi ke ID dokumen terpilih; hasil dan artefak run mengikuti lifecycle backend.</p>
      </div>

    </div>
  );
};
