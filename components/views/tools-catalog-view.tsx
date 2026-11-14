'use client';

import React, { useEffect, useState } from 'react';
import {
  Search,
  Wrench,
  ShieldCheck,
  Code,
  Search as SearchIcon,
  Database,
  Brain,
} from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { platformCatalogApi, type CustomerToolCatalogItem } from '@/lib/api/client';

interface ToolsCatalogViewProps {
  onNavigateTab: (tab: NavigationTab) => void;
  onSelectToolForPrompt?: (toolName: string) => void;
}

export const ToolsCatalogView: React.FC<ToolsCatalogViewProps> = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCat, setFilterCat] = useState<'semua' | 'produktivitas' | 'kreatif'>('semua');
  const [toolsList, setToolsList] = useState<CustomerToolCatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    platformCatalogApi.tools().then((items) => { if (active) setToolsList(items); })
      .catch((cause) => { if (active) setError(cause instanceof Error ? cause.message : 'Katalog tools tidak dapat dimuat.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const iconFor = (item: CustomerToolCatalogItem) => {
    const tags = item.capability_tags || [];
    if (tags.includes('knowledge')) return Brain;
    if (tags.includes('search') || tags.includes('web')) return SearchIcon;
    if (tags.includes('filesystem') || tags.includes('workspace')) return Code;
    if (tags.includes('storage') || tags.includes('artifact')) return Database;
    if (item.risk === 'critical' || item.approval_mode !== 'none') return ShieldCheck;
    return Wrench;
  };
  const categoryFor = (item: CustomerToolCatalogItem) => {
    const tags = item.capability_tags || [];
    return tags.some((tag) => ['image', 'video', 'audio', 'creative'].includes(tag)) ? 'kreatif' : 'produktivitas';
  };



  const filtered = toolsList.filter((tool) => {
    const matchesSearch = (tool.key + ' ' + tool.description).toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = filterCat === 'semua' || categoryFor(tool) === filterCat;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Title */}
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">MoreAI Tools Catalog</h1>
        <p className="text-xs text-slate-500">
          Katalog tool dari registry OpenManus dan kebijakan runtime MoreAI
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
      {error && <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-700">{error}</div>}
      {loading ? <div className="rounded-2xl border border-slate-100 bg-white p-8 text-center text-xs text-slate-500">Memuat registry tools…</div> : (
        <div className="space-y-2.5">
          {filtered.map((tool) => {
            const Icon = iconFor(tool);
            return (
              <article key={tool.key} className="flex items-center justify-between gap-3 rounded-2xl border border-slate-100 bg-white p-3.5 shadow-2xs">
                <div className="flex min-w-0 items-center gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-50 text-slate-600 shadow-2xs"><Icon className="h-5 w-5" /></div>
                  <div className="min-w-0">
                    <h3 className="truncate text-xs font-bold text-slate-900">{tool.key}</h3>
                    <p className="mt-0.5 line-clamp-2 text-[11px] text-slate-500">{tool.description}</p>
                    <p className="mt-1 text-[10px] text-slate-400">Risiko: {tool.risk} · Approval: {tool.approval_mode} · {tool.execution_environment}</p>
                  </div>
                </div>
                <div className="shrink-0 text-right">
                  <span className={`rounded-full border px-2 py-1 text-[9px] font-semibold ${tool.registered ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-amber-200 bg-amber-50 text-amber-700'}`}>
                    {tool.registered ? `Tersedia · ${tool.active_workers} worker` : 'Belum tersedia'}
                  </span>
                  <p className="mt-1 text-[9px] text-slate-400">{tool.enabled_by_default ? 'Policy default aktif' : 'Policy default nonaktif'}</p>
                </div>
              </article>
            );
          })}
          {filtered.length === 0 && <div className="rounded-2xl border border-slate-100 bg-white p-8 text-center text-xs text-slate-500">Tidak ada tool dari registry yang cocok.</div>}
        </div>
      )}
    </div>
  );
};
