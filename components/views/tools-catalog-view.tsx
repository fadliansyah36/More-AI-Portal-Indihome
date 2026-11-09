'use client';

import React, { useState } from 'react';
import {
  Search,
  FileSpreadsheet,
  FileText,
  Network,
  Calendar,
  Image as ImageIcon,
  Edit3,
  Video,
  Lightbulb,
  Languages,
  Mic,
  ChevronRight,
  Sparkles,
  ArrowRight,
} from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';

interface ToolsCatalogViewProps {
  onNavigateTab: (tab: NavigationTab) => void;
  onSelectToolForPrompt?: (toolName: string) => void;
}

export const ToolsCatalogView: React.FC<ToolsCatalogViewProps> = ({
  onNavigateTab,
  onSelectToolForPrompt,
}) => {
  const { showToast } = useToast();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCat, setFilterCat] = useState<'semua' | 'produktivitas' | 'kreatif'>('semua');

  const toolsList = [
    // Produktivitas
    {
      id: 'analisis-data',
      name: 'Analisis Data',
      desc: 'Analisis data spreadsheet & KPI bisnis secara terstruktur.',
      category: 'produktivitas',
      icon: FileSpreadsheet,
      color: 'bg-blue-50 text-blue-600',
      action: () => onNavigateTab('analyse'),
    },
    {
      id: 'ringkasan-pdf',
      name: 'Ringkasan PDF',
      desc: 'Pahami dokumen panjang dan laporan riset lebih cepat.',
      category: 'produktivitas',
      icon: FileText,
      color: 'bg-indigo-50 text-indigo-600',
      action: () => onNavigateTab('create'),
    },
    {
      id: 'mind-map',
      name: 'Mind Map',
      desc: 'Pemetaan konsep dan ide bisnis dalam struktur pohon visual.',
      category: 'produktivitas',
      icon: Network,
      color: 'bg-purple-50 text-purple-600',
      action: () => {
        if (onSelectToolForPrompt) onSelectToolForPrompt('Buatkan mind map terstruktur untuk rencana bisnis kafe');
        onNavigateTab('chat');
      },
    },
    {
      id: 'planner',
      name: 'Planner',
      desc: 'Penjadwalan tugas dan manajemen deadline otomatis.',
      category: 'produktivitas',
      icon: Calendar,
      color: 'bg-emerald-50 text-emerald-600',
      action: () => onNavigateTab('tasks'),
    },
    // Kreativitas
    {
      id: 'desain-gambar',
      name: 'Desain Gambar',
      desc: 'Ubah ide jadi visual menarik dan mockup produk tajam.',
      category: 'kreatif',
      icon: ImageIcon,
      color: 'bg-amber-50 text-amber-600',
      action: () => onNavigateTab('create'),
    },
    {
      id: 'edit-konten',
      name: 'Edit Konten',
      desc: 'Perbaiki tata bahasa, nada bicara, dan gaya penulisan copy.',
      category: 'kreatif',
      icon: Edit3,
      color: 'bg-rose-50 text-rose-600',
      action: () => onNavigateTab('create'),
    },
    {
      id: 'generate-video',
      name: 'Generate Video',
      desc: 'Buat storyboard, script video pendek, dan narasi promosi.',
      category: 'kreatif',
      icon: Video,
      color: 'bg-red-50 text-red-600',
      action: () => onNavigateTab('create'),
    },
    {
      id: 'ide-kreatif',
      name: 'Ide Kreatif',
      desc: 'Brainstorming kampanye pemasaran dan solusi pemecahan masalah.',
      category: 'kreatif',
      icon: Lightbulb,
      color: 'bg-yellow-50 text-yellow-600',
      action: () => {
        if (onSelectToolForPrompt) onSelectToolForPrompt('Berikan 10 ide promosi kreatif untuk UMKM kuliner');
        onNavigateTab('chat');
      },
    },
    {
      id: 'translator',
      name: 'Translator',
      desc: 'Terjemahkan berbagai bahasa asing dengan akurasi tata bahasa tinggi.',
      category: 'produktivitas',
      icon: Languages,
      color: 'bg-cyan-50 text-cyan-600',
      action: () => onNavigateTab('create'),
    },
    {
      id: 'voice-generator',
      name: 'Voice Generator',
      desc: 'Ubah teks jadi suara natural audio dalam bahasa Indonesia.',
      category: 'kreatif',
      icon: Mic,
      color: 'bg-fuchsia-50 text-fuchsia-600',
      action: () => {
        showToast('Fitur Voice Generator: Siap menghasilkan sulih suara AI.', 'info');
      },
    },
  ];

  const filtered = toolsList.filter((tool) => {
    const matchesSearch = tool.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = filterCat === 'semua' ? true : tool.category === filterCat;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Title */}
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">MoreAI Tools Catalog</h1>
        <p className="text-xs text-slate-500">
          Akses berbagai tools AI populer untuk produktivitas &amp; kreativitas (Sheet 1 &amp; 3 &amp; 5)
        </p>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Cari tools AI..."
          className="w-full text-xs sm:text-sm pl-10 pr-4 py-2.5 rounded-2xl bg-white border border-slate-200 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500 transition shadow-2xs"
        />
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1 p-1 bg-white rounded-2xl border border-slate-200 shadow-2xs">
        {(['semua', 'produktivitas', 'kreatif'] as const).map((cat) => (
          <button
            key={cat}
            onClick={() => setFilterCat(cat)}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-xl capitalize transition ${
              filterCat === cat
                ? 'bg-red-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Tools List */}
      <div className="space-y-2.5">
        {filtered.map((tool) => {
          const Icon = tool.icon;
          return (
            <div
              key={tool.id}
              onClick={tool.action}
              className="cursor-pointer p-3.5 rounded-2xl bg-white border border-slate-100 hover:border-red-200 shadow-2xs hover:shadow-xs transition flex items-center justify-between group"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div
                  className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 shadow-2xs group-hover:scale-105 transition-transform ${tool.color}`}
                >
                  <Icon className="w-5 h-5" />
                </div>
                <div className="min-w-0">
                  <h3 className="text-xs sm:text-sm font-bold text-slate-900 group-hover:text-red-600 transition truncate">
                    {tool.name}
                  </h3>
                  <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-1">
                    {tool.desc}
                  </p>
                </div>
              </div>

              <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-red-600 group-hover:translate-x-0.5 transition shrink-0 ml-2" />
            </div>
          );
        })}
      </div>
    </div>
  );
};
