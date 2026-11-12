'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { Search, TrendingUp, Sparkles, BookOpen, Clock, ChevronRight, ArrowLeft } from 'lucide-react';
import { customerApi, type CustomerAgentRun } from '@/lib/api/client';
import { useToast } from '@/components/ui/toast-context';

interface ResearchViewProps {
  onBack?: () => void;
  onSelectTopic?: (topicTitle: string) => void;
}

export const ResearchView: React.FC<ResearchViewProps> = ({ onBack, onSelectTopic }) => {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<'populer' | 'riwayat'>('populer');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTopic, setSelectedTopic] = useState<CustomerAgentRun | null>(null);
  const [runs, setRuns] = useState<CustomerAgentRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    customerApi.agentRuns().then((items) => { if (active) setRuns(items); })
      .catch((cause) => { if (active) setError(cause instanceof Error ? cause.message : 'Riwayat riset tidak dapat dimuat.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const runTitle = (run: CustomerAgentRun) => {
    const candidate = run.input?.content ?? run.input?.prompt ?? run.input?.message ?? run.input?.task;
    return typeof candidate === 'string' && candidate.trim() ? candidate.trim() : 'Agent run ' + run.id.slice(0, 8);
  };
  const filteredRuns = useMemo(() => runs.filter((run) => runTitle(run).toLowerCase().includes(searchQuery.toLowerCase())), [runs, searchQuery]);
  const resultText = (run: CustomerAgentRun) => {
    const value = run.output?.text ?? run.output?.content ?? run.output?.result;
    return typeof value === 'string' ? value : run.status === 'failed' ? 'Run gagal. Detail error dapat dilihat pada Workflow.' : 'Belum ada output final yang tersimpan.';
  };

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

      {error && <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-700">{error}</div>}
      {activeTab === 'populer' ? (
        <div className="rounded-3xl border border-slate-100 bg-white p-6 text-center">
          <BookOpen className="mx-auto mb-2 h-8 w-8 text-slate-300" />
          <p className="text-xs font-semibold text-slate-800">Topik riset publik belum tersedia</p>
          <p className="mt-1 text-[11px] text-slate-500">Daftar topik populer akan ditampilkan setelah sumber publik resmi terhubung. Tidak ada topik contoh yang ditampilkan sebagai data nyata.</p>
          <button onClick={() => setActiveTab('riwayat')} className="mt-3 text-xs font-bold text-red-600">Lihat riwayat riset akun</button>
        </div>
      ) : loading ? (
        <div className="rounded-3xl border border-slate-100 bg-white p-8 text-center text-xs text-slate-500">Memuat riwayat dari backend…</div>
      ) : filteredRuns.length ? (
        <div className="space-y-2.5">
          {filteredRuns.map((run) => (
            <button key={run.id} type="button" onClick={() => setSelectedTopic(run)} className="flex w-full items-start gap-3.5 rounded-3xl border border-slate-100 bg-white p-4 text-left shadow-2xs transition hover:border-red-200">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border border-red-100 bg-red-50 text-red-600"><TrendingUp className="h-5 w-5" /></div>
              <div className="min-w-0 flex-1">
                <h3 className="truncate text-xs font-bold text-slate-900">{runTitle(run)}</h3>
                <p className="mt-1 text-[11px] text-slate-500">Status: {run.status} · {run.created_at ? new Date(run.created_at).toLocaleString('id-ID') : 'Waktu tidak tersedia'}</p>
              </div>
              <ChevronRight className="h-4 w-4 shrink-0 text-slate-300" />
            </button>
          ))}
        </div>
      ) : (
        <div className="rounded-3xl border border-slate-100 bg-white p-8 text-center text-xs text-slate-500">Belum ada riwayat agent run yang cocok dengan pencarian ini.</div>
      )}
      {/* Topic Detail Modal */}
      {selectedTopic && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-fadeIn">
          <div className="w-full max-w-sm rounded-3xl bg-white p-5 shadow-2xl border border-slate-100 text-slate-800 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <span className="text-[10px] font-bold text-red-600 uppercase tracking-wider">
                Run · {selectedTopic.status}
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
              {resultText(selectedTopic)}
            </p>

            <div className="space-y-1.5 text-xs text-slate-700">
              <div className="font-bold text-slate-900 text-[11px]">Metode Riset:</div>
              <ul className="list-disc pl-4 space-y-1 text-slate-600 text-[11px]">
                <li>Data ditampilkan dari agent run yang tersimpan.</li>
                <li>Hasil mengikuti status dan output backend.</li>
              </ul>
            </div>

            <div className="flex gap-2 pt-2">
              <button
                onClick={() => {
                  if (onSelectTopic) onSelectTopic(runTitle(selectedTopic));
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
