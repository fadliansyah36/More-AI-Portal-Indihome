'use client';

import React, { useState } from 'react';
import { Search, TrendingUp, Sparkles, BookOpen, Clock, ChevronRight, ArrowLeft } from 'lucide-react';
import { RESEARCH_TOPICS } from '@/lib/data';
import { useToast } from '@/components/ui/toast-context';

interface ResearchViewProps {
  onBack?: () => void;
  onSelectTopic?: (topicTitle: string) => void;
}

export const ResearchView: React.FC<ResearchViewProps> = ({ onBack, onSelectTopic }) => {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<'populer' | 'riwayat'>('populer');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTopic, setSelectedTopic] = useState<typeof RESEARCH_TOPICS[0] | null>(null);

  const filtered = RESEARCH_TOPICS.filter((t) =>
    t.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {onBack && (
            <button
              onClick={onBack}
              className="p-1.5 rounded-xl text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition -ml-1"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
          )}
          <div>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">Research AI</h1>
            <p className="text-xs text-slate-500">Riset pasar terstruktur dan sintesis wawasan mendalam</p>
          </div>
        </div>
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Cari topik riset, industri, atau tren pasar..."
          className="w-full text-xs sm:text-sm pl-10 pr-4 py-2.5 rounded-2xl bg-white border border-slate-200 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500 transition shadow-2xs"
        />
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 p-1 bg-white rounded-2xl border border-slate-200 shadow-2xs">
        <button
          onClick={() => setActiveTab('populer')}
          className={`flex-1 py-1.5 text-xs font-semibold rounded-xl transition ${
            activeTab === 'populer'
              ? 'bg-red-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          Topik Populer
        </button>
        <button
          onClick={() => setActiveTab('riwayat')}
          className={`flex-1 py-1.5 text-xs font-semibold rounded-xl transition ${
            activeTab === 'riwayat'
              ? 'bg-red-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          Riwayat Riset
        </button>
      </div>

      {/* Topics List */}
      <div className="space-y-2.5">
        {filtered.map((topic) => (
          <div
            key={topic.id}
            onClick={() => setSelectedTopic(topic)}
            className="cursor-pointer p-4 rounded-3xl bg-white border border-slate-100 hover:border-red-200 shadow-2xs hover:shadow-xs transition flex items-start gap-3.5 group"
          >
            <div className="w-10 h-10 rounded-2xl bg-red-50 text-red-600 flex items-center justify-center shrink-0 border border-red-100 group-hover:scale-105 transition-transform">
              <TrendingUp className="w-5 h-5" />
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <h3 className="text-xs sm:text-sm font-bold text-slate-900 group-hover:text-red-600 transition">
                  {topic.title}
                </h3>
                <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-red-500 group-hover:translate-x-0.5 transition" />
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5">{topic.category}</p>
              <p className="text-xs text-slate-600 mt-1 line-clamp-2 leading-relaxed">
                {topic.summary}
              </p>
              <div className="flex items-center gap-3 text-[10px] text-slate-400 mt-2 font-medium">
                <span>{topic.views} pembaca</span>
                <span>·</span>
                <span>{topic.date}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Button Eksplor Topik Lainnya */}
      <button
        onClick={() => showToast('Memuat topik riset terkini dari basis data MoreAI & Telkom Insight...', 'info')}
        className="w-full py-3 rounded-2xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition flex items-center justify-center gap-1.5"
      >
        <span>Eksplor Topik Lainnya</span>
        <ChevronRight className="w-4 h-4" />
      </button>

      {/* Topic Detail Modal */}
      {selectedTopic && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-fadeIn">
          <div className="w-full max-w-sm rounded-3xl bg-white p-5 shadow-2xl border border-slate-100 text-slate-800 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <span className="text-[10px] font-bold text-red-600 uppercase tracking-wider">
                {selectedTopic.category}
              </span>
              <button
                onClick={() => setSelectedTopic(null)}
                className="text-slate-400 hover:text-slate-600 text-xs font-bold"
              >
                ✕
              </button>
            </div>

            <h3 className="text-base font-bold text-slate-900 leading-tight">
              {selectedTopic.title}
            </h3>

            <p className="text-xs text-slate-600 leading-relaxed bg-slate-50 p-3 rounded-2xl border border-slate-100">
              {selectedTopic.summary}
            </p>

            <div className="space-y-1.5 text-xs text-slate-700">
              <div className="font-bold text-slate-900 text-[11px]">Metode Riset:</div>
              <ul className="list-disc pl-4 space-y-1 text-slate-600 text-[11px]">
                <li>Penyisiran web terstruktur & sumber jurnal terverifikasi</li>
                <li>Sintesis komparatif data statistik pasar Indonesia</li>
                <li>Validasi kepatuhan privasi data oleh MoreAI Guard</li>
              </ul>
            </div>

            <div className="flex gap-2 pt-2">
              <button
                onClick={() => {
                  if (onSelectTopic) onSelectTopic(selectedTopic.title);
                  setSelectedTopic(null);
                }}
                className="flex-1 py-2.5 rounded-xl bg-red-600 text-white text-xs font-bold hover:bg-red-700 transition"
              >
                Gunakan Topik di Chat AI
              </button>
              <button
                onClick={() => setSelectedTopic(null)}
                className="px-3 py-2.5 rounded-xl bg-slate-100 text-slate-700 text-xs font-semibold hover:bg-slate-200 transition"
              >
                Tutup
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
