'use client';

import React, { useState } from 'react';
import {
  UploadCloud,
  FileSpreadsheet,
  FileText,
  CheckCircle2,
  Sparkles,
  ArrowRight,
  TrendingUp,
  BarChart2,
  PieChart,
} from 'lucide-react';

export const AnalyseView: React.FC = () => {
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<{
    summary: string;
    kpis: { label: string; value: string; trend: string }[];
    recommendations: string[];
  } | null>(null);

  const handleSelectSample = (name: string) => {
    setSelectedFileName(name);
    setAnalysisResult(null);
  };

  const handleStartAnalysis = () => {
    if (!selectedFileName) return;
    setIsAnalyzing(true);
    setTimeout(() => {
      setIsAnalyzing(false);
      setAnalysisResult({
        summary: `Analisis untuk "${selectedFileName}" selesai dilakukan oleh MoreAI Engine. Terdeteksi efisiensi performa 88% dengan potensi penghematan biaya operasional hingga 25%.`,
        kpis: [
          { label: 'Efisiensi Biaya', value: '+24.5%', trend: 'Positif' },
          { label: 'Akurasi Model', value: '98.2%', trend: 'Tinggi' },
          { label: 'Waktu Eksekusi', value: '1.4s', trend: 'Ultra Cepat' },
        ],
        recommendations: [
          'Terapkan automasi reporting harian untuk mengurangi beban staf hingga 8 jam/minggu.',
          'Gunakan koneksi Wi-Fi Global Partner ISP dedicated untuk stabilisasi pemrosesan file besar.',
          'Manfaatkan kuota AI Credit Free untuk pemindaian massal berkala.',
        ],
      });
    }, 1200);
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
            Mendukung file PDF, DOC, XLS, CSV hingga 25 MB
          </p>
        </div>

        <div>
          <label className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-900 text-white text-xs font-semibold hover:bg-slate-800 transition cursor-pointer shadow-xs active:scale-95">
            <span>Pilih File dari Perangkat</span>
            <input
              type="file"
              className="hidden"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  setSelectedFileName(e.target.files[0].name);
                  setAnalysisResult(null);
                }
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

      {/* Contoh File Analisis Siap Pakai */}
      <div className="space-y-2">
        <span className="text-xs font-bold text-slate-700">Contoh Berkas untuk Dianalisis:</span>
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => handleSelectSample('Laporan_Penjualan_Q1_2026.xlsx')}
            className="p-3 rounded-2xl bg-white border border-slate-200 text-left hover:border-red-200 transition text-xs group"
          >
            <div className="flex items-center gap-2">
              <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
              <span className="font-semibold text-slate-800 group-hover:text-red-600 truncate">
                Laporan_Penjualan_Q1.xlsx
              </span>
            </div>
            <span className="text-[10px] text-slate-400 mt-1 block">Spreadsheet data transaksi</span>
          </button>

          <button
            onClick={() => handleSelectSample('Proposal_Strategi_Bisnis.pdf')}
            className="p-3 rounded-2xl bg-white border border-slate-200 text-left hover:border-red-200 transition text-xs group"
          >
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-red-600" />
              <span className="font-semibold text-slate-800 group-hover:text-red-600 truncate">
                Proposal_Strategi.pdf
              </span>
            </div>
            <span className="text-[10px] text-slate-400 mt-1 block">Rangkuman 24 halaman</span>
          </button>
        </div>
      </div>

      {/* Button Jalankan Analisis */}
      <button
        onClick={handleStartAnalysis}
        disabled={!selectedFileName || isAnalyzing}
        className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 disabled:opacity-40 text-white text-xs font-bold transition shadow-xs flex items-center justify-center gap-2 active:scale-98"
      >
        <Sparkles className="w-4 h-4" />
        <span>{isAnalyzing ? 'Sedang Memproses Analisis Data...' : 'Mulai Analisis AI Sekarang'}</span>
      </button>

      {/* Analysis Result Card */}
      {analysisResult && (
        <div className="p-4 rounded-3xl bg-white border border-emerald-200 shadow-xs space-y-3.5 animate-fadeIn">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
            <div className="flex items-center gap-1.5 text-xs font-bold text-slate-900">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Hasil Analisis AI MoreAI</span>
            </div>
            <span className="text-[10px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full font-semibold">
              Terverifikasi
            </span>
          </div>

          <p className="text-xs text-slate-700 leading-relaxed bg-slate-50 p-3 rounded-2xl border border-slate-100">
            {analysisResult.summary}
          </p>

          {/* Metric KPI cards */}
          <div className="grid grid-cols-3 gap-2">
            {analysisResult.kpis.map((kpi, idx) => (
              <div key={idx} className="p-2.5 rounded-2xl bg-slate-50 border border-slate-100 text-center">
                <span className="text-[10px] text-slate-400 block truncate">{kpi.label}</span>
                <span className="text-sm font-extrabold text-slate-900 leading-tight block mt-0.5">
                  {kpi.value}
                </span>
                <span className="text-[9px] text-emerald-600 font-semibold">{kpi.trend}</span>
              </div>
            ))}
          </div>

          {/* Recommendations */}
          <div className="space-y-1.5">
            <span className="text-xs font-bold text-slate-900">Rekomendasi Strategis:</span>
            <ul className="space-y-1">
              {analysisResult.recommendations.map((rec, idx) => (
                <li key={idx} className="flex items-start gap-2 text-xs text-slate-600">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-500 mt-1.5 shrink-0" />
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Contoh Analisis checklist from Sheet 2 */}
      <div className="bg-slate-50 p-4 rounded-3xl border border-slate-200/80 space-y-2">
        <h4 className="text-xs font-bold text-slate-800">Cakupan Kemampuan Analisis MoreAI:</h4>
        <div className="space-y-1.5 text-xs text-slate-600">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
            <span>Analisis dokumen hukum, kontrak, dan perjanjian kerja</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
            <span>Ringkasan laporan tahunan dan performa marketing</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
            <span>Insight data numerik dan visualisasi korelasi variabel bisnis</span>
          </div>
        </div>
      </div>
    </div>
  );
};
