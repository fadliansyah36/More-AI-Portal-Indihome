'use client';

import React, { useState } from 'react';
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
import { INITIAL_AGENTS } from '@/lib/data';
import { AIAgent } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';

interface AgentStudioViewProps {
  onSelectAgentForChat?: (agent: AIAgent) => void;
}

export const AgentStudioView: React.FC<AgentStudioViewProps> = ({ onSelectAgentForChat }) => {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<'agent' | 'workflow'>('agent');
  const [selectedAgentId, setSelectedAgentId] = useState<string>('marketing');
  const [agents, setAgents] = useState<AIAgent[]>(INITIAL_AGENTS);

  const selectedAgent = agents.find((a) => a.id === selectedAgentId) || agents[0];

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
          Tim agen AI spesialis mandiri untuk riset, kampanye, konten, visual, dan analitik
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
                    {agent.creditsRequired} Poin
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
                Ready to Deploy
              </span>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              {selectedAgent.description}
            </p>

            <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-600">
              <div className="p-2 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-slate-400 block text-[9px] uppercase font-bold">Kebutuhan Quota</span>
                <span className="font-bold text-slate-900">{selectedAgent.creditsRequired} AI Poin / Run</span>
              </div>
              <div className="p-2 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-slate-400 block text-[9px] uppercase font-bold">Status Lisensi</span>
                <span className="font-bold text-emerald-600">Aktif via Partner ISP</span>
              </div>
            </div>

            <button
              onClick={() => {
                showToast(`Agent "${selectedAgent.name}" siap digunakan! Membuka Chat Workspace.`, 'success');
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
        /* Multi-Agent Workflow Builder View */
        <div className="p-5 rounded-3xl bg-white border border-slate-100 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Pipeline Multi-Agent Otomatis</h3>
              <p className="text-xs text-slate-500">Menghubungkan beberapa agent secara berantai</p>
            </div>
            <span className="text-[10px] font-bold text-red-600 bg-red-50 px-2 py-0.5 rounded-full border border-red-200">
              Auto-Orchestrator
            </span>
          </div>

          <div className="space-y-3">
            <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200 flex items-center gap-3">
              <div className="w-7 h-7 rounded-lg bg-blue-500 text-white font-bold text-xs flex items-center justify-center">
                1
              </div>
              <div className="flex-1">
                <span className="text-xs font-bold text-slate-900 block">Research Agent</span>
                <span className="text-[10px] text-slate-500">Menganalisis topik & mengumpulkan fakta valid</span>
              </div>
            </div>

            <div className="w-0.5 h-4 bg-slate-300 mx-auto" />

            <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200 flex items-center gap-3">
              <div className="w-7 h-7 rounded-lg bg-amber-500 text-white font-bold text-xs flex items-center justify-center">
                2
              </div>
              <div className="flex-1">
                <span className="text-xs font-bold text-slate-900 block">Marketing & Writing Agent</span>
                <span className="text-[10px] text-slate-500">Menyusun strategi campaign & copywriting</span>
              </div>
            </div>

            <div className="w-0.5 h-4 bg-slate-300 mx-auto" />

            <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200 flex items-center gap-3">
              <div className="w-7 h-7 rounded-lg bg-purple-500 text-white font-bold text-xs flex items-center justify-center">
                3
              </div>
              <div className="flex-1">
                <span className="text-xs font-bold text-slate-900 block">Design & Data Analyst</span>
                <span className="text-[10px] text-slate-500">Membuat visualisasi materi & laporan spreadsheet</span>
              </div>
            </div>
          </div>

          <button
            onClick={() => showToast('Workflow Multi-Agent baru telah dijadwalkan ke queue executor!', 'success')}
            className="w-full py-3 rounded-2xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition shadow-xs flex items-center justify-center gap-1.5"
          >
            <span>Jalankan Pipeline Lengkap</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};
