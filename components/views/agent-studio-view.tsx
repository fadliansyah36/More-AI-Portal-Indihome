'use client';

import React, { useEffect, useState } from 'react';
import {
  Bot,
  Search,
  TrendingUp,
  PenTool,
  Palette,
  BarChart3,
  CheckCircle2,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import { customerApi, type CustomerToolCatalogItem } from '@/lib/api/client';
import { AIAgent } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';

interface AgentStudioViewProps {
  onSelectAgentForChat?: (agent: AIAgent) => void;
  onOpenWorkflow?: () => void;
}

export const AgentStudioView: React.FC<AgentStudioViewProps> = ({ onSelectAgentForChat, onOpenWorkflow }) => {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<'agent' | 'workflow'>('agent');
  const [selectedAgentId, setSelectedAgentId] = useState<string>('');
  const [agents, setAgents] = useState<AIAgent[]>([]);
  const [isLoadingAgents, setIsLoadingAgents] = useState(true);
  const [agentLoadError, setAgentLoadError] = useState<string | null>(null);
  const [toolCatalog, setToolCatalog] = useState<CustomerToolCatalogItem[]>([]);
  const [toolCatalogError, setToolCatalogError] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    customerApi.agents()
      .then((rows) => {
        if (!active) return;
        // The current FastAPI chat enqueue contract accepts these three
        // runtime keys. Do not present catalog entries as runnable until the
        // transport contract explicitly supports their key.
        const supportedRuntimeKeys = new Set(['manus', 'planning', 'toolcall']);
        const mapped = rows.filter((row) => row.enabled && supportedRuntimeKeys.has(row.key)).map((row) => ({
          id: row.key, name: row.name, specialty: 'Runtime ' + row.version,
          description: row.description, iconName: 'Bot', color: 'bg-slate-500',
          creditsRequired: 0, active: row.enabled,
        }));
        setAgents(mapped);
        setSelectedAgentId(mapped[0]?.id || '');
      })
      .catch((cause) => { if (active) setAgentLoadError(cause instanceof Error ? cause.message : 'Katalog agent tidak tersedia.'); })
      .finally(() => { if (active) setIsLoadingAgents(false); });
    customerApi.tools()
      .then((rows) => { if (active) setToolCatalog(rows); })
      .catch((cause) => { if (active) setToolCatalogError(cause instanceof Error ? cause.message : 'Katalog tool tidak tersedia.'); });
    return () => { active = false; };
  }, []);

  const selectedAgent = agents.find((a) => a.id === selectedAgentId) || agents[0] || null;

  if (!selectedAgent) {
    return (
      <div className="space-y-4 pb-20 animate-fadeIn">
        <div><h1 className="text-xl font-bold text-slate-900 tracking-tight">AI Agent Studio</h1><p className="text-xs text-slate-500">Katalog agent dari FastAPI dan OpenManus.</p></div>
        <div className="p-8 rounded-3xl bg-white border border-slate-100 text-center text-xs text-slate-500">
          {isLoadingAgents ? 'Memuat katalog agent...' : agentLoadError || 'Belum ada agent dengan runtime key yang didukung Chat API (manus, planning, toolcall).'}
        </div>
      </div>
    );
  }

  const getAgentIcon = (id: string) => {
    switch (id) {
      case 'research':
        return <Search className="w-5 h-5 text-blue-600" />;
      case 'marketing':
        return <TrendingUp className="w-5 h-5 text-amber-600" />;
      case 'writing':
        return <PenTool className="w-5 h-5 text-emerald-600" />;
      case 'design':
        return <Palette className="w-5 h-5 text-purple-600" />;
      case 'data':
        return <BarChart3 className="w-5 h-5 text-rose-600" />;
      default:
        return <Bot className="w-5 h-5 text-slate-600" />;
    }
  };

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Title */}
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">AI Agent Studio</h1>
        <p className="text-xs text-slate-500">
          Agent yang diaktifkan dan dipublikasikan oleh backend MoreAI.
        </p>
      </div>

      {/* Tabs (Agent vs Workflow) matching Sheet 6 */}
      <div className="flex items-center gap-1 p-1 bg-white rounded-2xl border border-slate-200 shadow-2xs">
        <button
          onClick={() => setActiveTab('agent')}
          className={`flex-1 py-1.5 text-xs font-semibold rounded-xl transition ${
            activeTab === 'agent'
              ? 'bg-red-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          Daftar Agent
        </button>
        <button
          onClick={() => setActiveTab('workflow')}
          className={`flex-1 py-1.5 text-xs font-semibold rounded-xl transition ${
            activeTab === 'workflow'
              ? 'bg-red-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          Multi-Agent Workflow
        </button>
      </div>

      {activeTab === 'agent' ? (
        <div className="space-y-3">
          {/* Agent Cards List */}
          <div className="space-y-2">
            {agents.map((agent) => {
              const isSelected = agent.id === selectedAgentId;
              return (
                <div
                  key={agent.id}
                  onClick={() => setSelectedAgentId(agent.id)}
                  className={`cursor-pointer p-3.5 rounded-2xl border transition-all flex items-center justify-between group ${
                    isSelected
                      ? 'bg-red-50/60 border-red-300 ring-2 ring-red-500/10 shadow-xs'
                      : 'bg-white border-slate-100 hover:border-slate-200 shadow-2xs'
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-10 h-10 rounded-xl bg-white border border-slate-200 flex items-center justify-center shrink-0 shadow-2xs group-hover:scale-105 transition-transform">
                      {getAgentIcon(agent.id)}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5">
                        <h3 className="text-xs sm:text-sm font-bold text-slate-900 truncate">
                          {agent.name}
                        </h3>
                        {isSelected && (
                          <CheckCircle2 className="w-4 h-4 text-red-600 shrink-0" />
                        )}
                      </div>
                      <p className="text-[11px] text-slate-500 mt-0.5 truncate">
                        {agent.specialty}
                      </p>
                    </div>
                  </div>

                  <span className="text-[10px] font-bold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-full shrink-0">
                    {agent.specialty}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Selected Agent Detail Card */}
          <div className="p-4 rounded-3xl bg-white border border-slate-200 shadow-xs space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-red-50 flex items-center justify-center">
                  {getAgentIcon(selectedAgent.id)}
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-900">{selectedAgent.name}</h4>
                  <span className="text-[10px] text-slate-500">{selectedAgent.specialty}</span>
                </div>
              </div>
              <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                Enabled
              </span>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              {selectedAgent.description}
            </p>
            <section className="rounded-2xl border border-slate-100 bg-slate-50 p-3 space-y-2">
              <div className="flex items-center justify-between gap-2">
                <h5 className="text-[11px] font-bold text-slate-800">Tool Policy · OpenManus</h5>
                <span className="text-[9px] text-slate-500">Runtime {selectedAgent.id}</span>
              </div>
              {toolCatalogError ? (
                <p className="text-[10px] text-amber-700">{toolCatalogError}</p>
              ) : (
                <>
                  {toolCatalog.filter((tool) => tool.available_by_default.includes(selectedAgent.id) && tool.enabled_by_default).length ? (
                    <div className="flex flex-wrap gap-1.5">
                      {toolCatalog.filter((tool) => tool.available_by_default.includes(selectedAgent.id) && tool.enabled_by_default).map((tool) => (
                        <span key={tool.key} title={tool.description + ' · ' + tool.permission_scope + ' · ' + tool.approval_mode}
                          className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2 py-1 text-[10px] font-medium text-slate-700">
                          {tool.key}
                          <span className={tool.risk === 'critical' || tool.risk === 'high' ? 'text-rose-600' : 'text-slate-400'}>{tool.risk}</span>
                        </span>
                      ))}
                    </div>
                  ) : <p className="text-[10px] text-slate-500">Belum ada tool default yang dipetakan untuk runtime ini.</p>}
                  <p className="text-[10px] leading-relaxed text-slate-500">
                    Katalog menjelaskan kontrak, permission, dan kebutuhan approval. Tool yang memerlukan provider, sandbox, browser, atau adapter tetap mengikuti gate konfigurasi backend; katalog bukan bukti bahwa layanan eksternal sedang aktif.
                  </p>
                </>
              )}
            </section>

            <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-600">
              <div className="p-2 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-slate-400 block text-[9px] uppercase font-bold">Versi Runtime</span>
                <span className="font-bold text-slate-900">{selectedAgent.specialty}</span>
              </div>
              <div className="p-2 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-slate-400 block text-[9px] uppercase font-bold">Status Backend</span>
                <span className="font-bold text-emerald-600">Enabled oleh backend</span>
              </div>
            </div>

            <button
              onClick={() => {
                showToast('Membuka Chat Workspace. Eksekusi mengikuti ketersediaan backend.', 'info');
                if (onSelectAgentForChat) onSelectAgentForChat(selectedAgent);
              }}
              className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 active:scale-95 text-white text-xs font-bold transition shadow-xs flex items-center justify-center gap-2"
            >
              <Zap className="w-3.5 h-3.5 fill-current" />
              <span>Gunakan Agent Ini</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="p-5 rounded-3xl bg-white border border-slate-100 shadow-xs space-y-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Multi-Agent Workflow</h3>
            <p className="text-xs text-slate-500">Pantau workflow yang benar-benar dibuat dan dijalankan melalui backend OpenManus.</p>
          </div>
          <button onClick={() => onOpenWorkflow?.()} className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition">
            Buka Workflow & Agent Runs
          </button>
        </div>
      )}
    </div>
  );
};
