'use client';

import React, { useState } from 'react';
import { knowledgeApi } from '@/lib/api/knowledge';
import {
  UploadCloud,
    CheckCircle2,
  Sparkles,
} from 'lucide-react';

export const AnalyseView: React.FC = () => {
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadState, setUploadState] = useState<'idle' | 'queued' | 'error'>('idle');
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

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

    </div>
  );
};
