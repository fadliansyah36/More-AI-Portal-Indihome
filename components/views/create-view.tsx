'use client';

import React, { useState } from 'react';
import {
  Sparkles,
  FileText,
  Image as ImageIcon,
  Video,
  Languages,
  Presentation,
  Send,
  Copy,
  Check,
  ChevronRight,
  ArrowRight,
  Wand2,
} from 'lucide-react';

interface CreateViewProps {
  onNavigateToChat?: (prompt: string) => void;
}

export const CreateView: React.FC<CreateViewProps> = ({ onNavigateToChat }) => {
  const [activeTab, setActiveTab] = useState<'semua' | 'teks' | 'gambar' | 'video'>('semua');
  const [selectedTool, setSelectedTool] = useState<string | null>(null);
  const [customPrompt, setCustomPrompt] = useState('');
  const [generatedOutput, setGeneratedOutput] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [copied, setCopied] = useState(false);

  const tools = [
    {
      id: 'text-doc',
      name: 'Teks ke Dokumen',
      altName: 'Tulis Konten',
      category: 'teks',
      desc: 'Buat konten artikel, proposal, dan draft profesional dengan AI cerdas.',
      icon: FileText,
      color: 'bg-blue-50 text-blue-600 border-blue-200',
      samplePrompt: 'Buat outline artikel tentang pentingnya koneksi Wi-Fi stabil bagi produktivitas kerja jarak jauh.',
    },
    {
      id: 'img-gen',
      name: 'Generate Gambar',
      altName: 'Gambar ke Gambar',
      category: 'gambar',
      desc: 'Ubah ide dan imajinasi menjadi karya visual realistis dengan resolusi tajam.',
      icon: ImageIcon,
      color: 'bg-amber-50 text-amber-600 border-amber-200',
      samplePrompt: 'Ilustrasi modern flat 3D interior kedai kopi hangat di Jakarta dengan barista sedang menyajikan espresso.',
    },
    {
      id: 'doc-summary',
      name: 'Ringkasan Dokumen',
      altName: 'Pahami Dokumen',
      category: 'teks',
      desc: 'Pahami dokumen panjang, PDF riset, dan laporan dalam hitungan detik.',
      icon: Wand2,
      color: 'bg-emerald-50 text-emerald-600 border-emerald-200',
      samplePrompt: 'Ringkas poin krusial dari laporan keuangan kuartal 3 ke dalam 3 poin actionable rekomendasi.',
    },
    {
      id: 'translate',
      name: 'Terjemahkan Bahasa',
      altName: 'Multi-bahasa',
      category: 'teks',
      desc: 'Terjemahkan dokumen teknis, email bisnis, atau materi promosi dengan akurasi tata bahasa tinggi.',
      icon: Languages,
      color: 'bg-purple-50 text-purple-600 border-purple-200',
      samplePrompt: 'Terjemahkan penawaran kerjasama B2B ini ke dalam Bahasa Inggris formal dan persuasif.',
    },
    {
      id: 'presentation',
      name: 'Presentasi AI',
      altName: 'Slide Otomatis',
      category: 'teks',
      desc: 'Buat struktur slide presentasi menarik dan ringkas untuk pitch deck bisnis.',
      icon: Presentation,
      color: 'bg-rose-50 text-rose-600 border-rose-200',
      samplePrompt: 'Buat 5 slide pitch deck untuk solusi program kemitraan Wi-Fi kafe dengan benefit AI gratis.',
    },
    {
      id: 'video-gen',
      name: 'Generate Video',
      altName: 'Script ke Video',
      category: 'video',
      desc: 'Rancang storyboard video promosi pendek dan narasi suara natural.',
      icon: Video,
      color: 'bg-indigo-50 text-indigo-600 border-indigo-200',
      samplePrompt: 'Buat script video TikTok 15 detik tentang kemudahan akses AI di jaringan Global Partner ISP.',
    },
  ];

  const filteredTools = tools.filter((tool) => {
    if (activeTab === 'semua') return true;
    return tool.category === activeTab;
  });

  const handleRunTool = (tool: typeof tools[0]) => {
    setSelectedTool(tool.id);
    setCustomPrompt(tool.samplePrompt);
    setGeneratedOutput(null);
  };

  const handleGenerate = () => {
    if (!customPrompt.trim()) return;
    setIsGenerating(true);
    setTimeout(() => {
      setIsGenerating(false);
      setGeneratedOutput(`[Hasil AI Generated - ${selectedTool ? tools.find(t => t.id === selectedTool)?.name : 'MoreAI'}]
      
Judul: Solusi Produktivitas Digital UMKM Indonesia
Tanggal: ${new Date().toLocaleDateString('id-ID')}

1. Ringkasan Eksekutif:
   Pemanfaatan AI terintegrasi pada jaringan Wi-Fi lokal membuka peluang peningkatan omset hingga 40% bagi pemilik usaha mikro melalui otomatisasi konten dan personalisasi layanan pelanggan.

2. Rencana Eksekusi:
   - Peluncuran program Wi-Fi bersponsor di 5 titik kafe percontohan.
   - Distribusi AI Credit Free Partner ISP untuk pengunjung tetap.
   - Evaluasi mingguan melalui Dashboard Partner MoreAI.`);
    }, 1000);
  };

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Title */}
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">Create Studio</h1>
        <p className="text-xs text-slate-500">
          Ubah ide menjadi dokumen, gambar visual, presentasi, dan media promosi dengan AI
        </p>
      </div>

      {/* Category Tabs */}
      <div className="flex items-center gap-1.5 p-1 bg-white rounded-2xl border border-slate-200 shadow-2xs">
        {(['semua', 'teks', 'gambar', 'video'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-xl capitalize transition ${
              activeTab === tab
                ? 'bg-red-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tool Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        {filteredTools.map((tool) => {
          const Icon = tool.icon;
          const isSelected = selectedTool === tool.id;

          return (
            <div
              key={tool.id}
              onClick={() => handleRunTool(tool)}
              className={`cursor-pointer p-4 rounded-3xl border transition-all flex items-start gap-3.5 group ${
                isSelected
                  ? 'bg-red-50/50 border-red-300 ring-2 ring-red-500/10 shadow-xs'
                  : 'bg-white border-slate-100 hover:border-red-200 shadow-2xs hover:shadow-xs'
              }`}
            >
              <div
                className={`w-11 h-11 rounded-2xl border flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform ${tool.color}`}
              >
                <Icon className="w-5 h-5" />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-slate-900 group-hover:text-red-600 transition">
                    {tool.name}
                  </h3>
                  <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-red-500 group-hover:translate-x-0.5 transition" />
                </div>
                <p className="text-[11px] text-slate-500 mt-1 line-clamp-2 leading-relaxed">
                  {tool.desc}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Interactive Creator Panel */}
      {selectedTool && (
        <div className="p-4 rounded-3xl bg-white border border-red-200 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-red-600" />
              <span>Jalankan {tools.find((t) => t.id === selectedTool)?.name}</span>
            </span>
            <span className="text-[10px] text-red-600 font-semibold bg-red-50 px-2 py-0.5 rounded-full border border-red-200">
              Biaya: 50 Poin
            </span>
          </div>

          <textarea
            value={customPrompt}
            onChange={(e) => setCustomPrompt(e.target.value)}
            rows={3}
            className="w-full text-xs p-3 rounded-2xl bg-slate-50 border border-slate-200 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500"
            placeholder="Ketik instruksi prompt detail di sini..."
          />

          <div className="flex gap-2">
            <button
              onClick={handleGenerate}
              disabled={isGenerating || !customPrompt.trim()}
              className="flex-1 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 disabled:opacity-40 text-white text-xs font-bold transition shadow-xs flex items-center justify-center gap-1.5"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>{isGenerating ? 'Membuat Konten...' : 'Generate Sekarang'}</span>
            </button>

            {onNavigateToChat && (
              <button
                onClick={() => onNavigateToChat(customPrompt)}
                className="px-3 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition"
                title="Buka di Chat AI"
              >
                Ke Chat AI
              </button>
            )}
          </div>

          {/* Output Display */}
          {generatedOutput && (
            <div className="mt-3 p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-800 space-y-2">
              <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                <span className="font-bold text-slate-900 text-[11px]">Hasil Pekerjaan</span>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(generatedOutput);
                    setCopied(true);
                    setTimeout(() => setCopied(false), 2000);
                  }}
                  className="flex items-center gap-1 text-[10px] text-slate-600 hover:text-slate-900"
                >
                  {copied ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                  <span>{copied ? 'Tersalin' : 'Salin'}</span>
                </button>
              </div>
              <pre className="whitespace-pre-wrap font-sans text-xs text-slate-700 leading-relaxed">
                {generatedOutput}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
