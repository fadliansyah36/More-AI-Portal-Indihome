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
import { customerApi, type CustomerAgentConfiguration, type CustomerToolCatalogItem } from '@/lib/api/client';
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
  const [agentConfigurations, setAgentConfigurations] = useState<CustomerAgentConfiguration[]>([]);
  const [editingConfigurationId, setEditingConfigurationId] = useState<string | null>(null);
  const [configurationName, setConfigurationName] = useState('');
  const [configurationRuntime, setConfigurationRuntime] = useState<'manus' | 'toolcall'>('manus');
  const [configurationDescription, setConfigurationDescription] = useState('');
  const [configurationPrompt, setConfigurationPrompt] = useState('');
  const [configurationToolKeys, setConfigurationToolKeys] = useState<string[]>([]);
  const [savingConfiguration, setSavingConfiguration] = useState(false);
  const [configurationError, setConfigurationError] = useState<string | null>(null);
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
          capabilityTags: row.capability_tags, toolKeys: row.tool_keys,
          runtimeAvailable: row.runtime_available, activeWorkers: row.active_workers,
          liveToolKeys: row.live_tool_keys, lastSeenAt: row.last_seen_at,
        }));
        setAgents(mapped);
        setSelectedAgentId(mapped[0]?.id || '');
      })
      .catch((cause) => { if (active) setAgentLoadError(cause instanceof Error ? cause.message : 'Katalog agent tidak tersedia.'); })
      .finally(() => { if (active) setIsLoadingAgents(false); });
    customerApi.tools()
      .then((rows) => {
        if (!active) return;
        setToolCatalog(rows);
        setConfigurationToolKeys(rows
          .filter((tool) => tool.available_by_default.includes('manus') && tool.enabled_by_default)
          .map((tool) => tool.key));
      })
      .catch((cause) => { if (active) setToolCatalogError(cause instanceof Error ? cause.message : 'Katalog tool tidak tersedia.'); });
    customerApi.agentConfigurations()
      .then((rows) => { if (active) setAgentConfigurations(rows); })
      .catch((cause) => { if (active) setConfigurationError(cause instanceof Error ? cause.message : 'Konfigurasi Agent tidak dapat dimuat.'); });
    return () => { active = false; };
  }, []);

  const availableConfigurationTools = toolCatalog.filter((tool) =>
    tool.available_by_default.includes(configurationRuntime) && tool.enabled_by_default,
  );

  const resetConfigurationForm = () => {
    setEditingConfigurationId(null);
    setConfigurationName('');
    setConfigurationDescription('');
    setConfigurationPrompt('');
    setConfigurationToolKeys(availableConfigurationTools.map((tool) => tool.key));
    setConfigurationError(null);
  };

  const saveConfiguration = async () => {
    if (!configurationName.trim()) {
      setConfigurationError('Nama Agent wajib diisi.');
      return;
    }
    setSavingConfiguration(true);
    setConfigurationError(null);
    try {
      const payload = {
        runtime_key: configurationRuntime,
        name: configurationName.trim(),
        description: configurationDescription.trim(),
        system_prompt: configurationPrompt.trim(),
        tool_keys: configurationToolKeys,
      };
      const saved = editingConfigurationId
        ? await customerApi.updateAgentConfiguration(editingConfigurationId, payload)
        : await customerApi.createAgentConfiguration(payload);
      setAgentConfigurations((current) => [
        saved,
        ...current.filter((item) => item.id !== saved.id),
      ]);
      resetConfigurationForm();
      showToast('Konfigurasi Agent tersimpan di backend.', 'success');
    } catch (cause) {
      setConfigurationError(cause instanceof Error ? cause.message : 'Konfigurasi Agent gagal disimpan.');
    } finally {
      setSavingConfiguration(false);
    }
  };

  const editConfiguration = (configuration: CustomerAgentConfiguration) => {
    setEditingConfigurationId(configuration.id);
    setConfigurationRuntime(configuration.runtime_key);
    setConfigurationName(configuration.name);
    setConfigurationDescription(configuration.description);
    setConfigurationPrompt(configuration.system_prompt);
    setConfigurationToolKeys(configuration.tool_keys);
    setConfigurationError(null);
  };

  const removeConfiguration = async (configuration: CustomerAgentConfiguration) => {
    try {
      await customerApi.deleteAgentConfiguration(configuration.id);
      setAgentConfigurations((current) => current.filter((item) => item.id !== configuration.id));
      if (editingConfigurationId === configuration.id) resetConfigurationForm();
      showToast('Konfigurasi Agent dihapus.', 'success');
    } catch (cause) {
      setConfigurationError(cause instanceof Error ? cause.message : 'Konfigurasi Agent gagal dihapus.');
    }
  };

  const useConfiguration = (configuration: CustomerAgentConfiguration) => {
    const runtimeAgent = agents.find((agent) => agent.id === configuration.runtime_key);
    if (!runtimeAgent || !onSelectAgentForChat) return;
    onSelectAgentForChat({
      ...runtimeAgent,
      id: configuration.runtime_key,
      name: configuration.name,
      description: configuration.description || runtimeAgent.description,
      configurationId: configuration.id,
      toolKeys: configuration.tool_keys,
    });
  };

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
            {selectedAgent.capabilityTags && selectedAgent.capabilityTags.length > 0 && (
              <div className="space-y-1.5">
                <p className="text-[10px] font-bold uppercase tracking-wide text-slate-400">Kapabilitas runtime</p>
                <div className="flex flex-wrap gap-1.5">
                  {selectedAgent.capabilityTags.map((tag) => (
                    <span key={tag} className="rounded-lg border border-slate-200 bg-slate-50 px-2 py-1 text-[10px] font-medium text-slate-700">{tag}</span>
                  ))}
                </div>
              </div>
            )}
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
                <span className={selectedAgent.runtimeAvailable ? 'font-bold text-emerald-600' : 'font-bold text-amber-700'}>
                  {selectedAgent.runtimeAvailable ? `Worker online · ${selectedAgent.activeWorkers || 0}` : 'Worker belum terdeteksi'}
                </span>
              </div>
            </div>

            <button
              onClick={() => {
                showToast('Membuka Chat Workspace. Eksekusi mengikuti ketersediaan backend.', 'info');
                if (onSelectAgentForChat) onSelectAgentForChat(selectedAgent);
              }}
              disabled={!selectedAgent.runtimeAvailable}
              title={!selectedAgent.runtimeAvailable ? 'Worker runtime belum melaporkan heartbeat aktif' : 'Gunakan Agent ini'}
              className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 active:scale-95 text-white text-xs font-bold transition shadow-xs flex items-center justify-center gap-2 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Zap className="w-3.5 h-3.5 fill-current" />
              <span>Gunakan Agent Ini</span>
            </button>
          </div>

          <section className="rounded-3xl border border-slate-200 bg-white p-4 shadow-xs space-y-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Konfigurasi Agent Saya</h3>
              <p className="mt-1 text-[11px] leading-relaxed text-slate-500">Simpan instruksi dan batas tool untuk Agent pribadi. Backend tetap membatasi tool pada runtime yang benar-benar terdaftar dan aktif.</p>
            </div>
            {agentConfigurations.length > 0 && (
              <div className="space-y-2">
                {agentConfigurations.map((configuration) => (
                  <div key={configuration.id} className="rounded-2xl border border-slate-200 p-3 flex items-start gap-2">
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-bold text-slate-900">{configuration.name}</p>
                      <p className="mt-0.5 text-[10px] text-slate-500">{configuration.runtime_key} · {configuration.tool_keys.length} tool · v{configuration.version}</p>
                      {configuration.description && <p className="mt-1 text-[10px] text-slate-600">{configuration.description}</p>}
                    </div>
                    <button type="button" disabled={!agents.some((agent) => agent.id === configuration.runtime_key && agent.runtimeAvailable)} onClick={() => useConfiguration(configuration)} title={!agents.some((agent) => agent.id === configuration.runtime_key && agent.runtimeAvailable) ? 'Worker runtime belum online' : 'Gunakan konfigurasi ini'} className="rounded-lg bg-red-600 px-2.5 py-1.5 text-[10px] font-bold text-white disabled:cursor-not-allowed disabled:opacity-40">Gunakan</button>
                    <button type="button" onClick={() => editConfiguration(configuration)} className="rounded-lg border border-slate-200 px-2.5 py-1.5 text-[10px] font-semibold text-slate-700">Edit</button>
                    <button type="button" onClick={() => void removeConfiguration(configuration)} className="rounded-lg border border-rose-200 px-2.5 py-1.5 text-[10px] font-semibold text-rose-700">Hapus</button>
                  </div>
                ))}
              </div>
            )}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <label className="space-y-1 text-[10px] font-semibold text-slate-600">
                Nama Agent
                <input value={configurationName} onChange={(event) => setConfigurationName(event.target.value)} maxLength={80} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-900 outline-none focus:border-red-400" placeholder="Contoh: Research Assistant" />
              </label>
              <label className="space-y-1 text-[10px] font-semibold text-slate-600">
                Runtime OpenManus
                <select value={configurationRuntime} disabled={!!editingConfigurationId} onChange={(event) => {
                  const runtime = event.target.value as 'manus' | 'toolcall';
                  setConfigurationRuntime(runtime);
                  setConfigurationToolKeys(toolCatalog.filter((tool) => tool.available_by_default.includes(runtime) && tool.enabled_by_default).map((tool) => tool.key));
                }} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-900">
                  <option value="manus">Manus</option>
                  <option value="toolcall">ToolCall</option>
                </select>
              </label>
            </div>
            <label className="block space-y-1 text-[10px] font-semibold text-slate-600">
              Deskripsi
              <input value={configurationDescription} onChange={(event) => setConfigurationDescription(event.target.value)} maxLength={500} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-900 outline-none focus:border-red-400" placeholder="Fokus dan spesialisasi Agent" />
            </label>
            <label className="block space-y-1 text-[10px] font-semibold text-slate-600">
              Instruksi Agent
              <textarea value={configurationPrompt} onChange={(event) => setConfigurationPrompt(event.target.value)} maxLength={12000} rows={4} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-900 outline-none focus:border-red-400" placeholder="Instruksi kerja tambahan. Kebijakan platform dan keamanan runtime tetap berlaku." />
            </label>
            <div className="space-y-2">
              <p className="text-[10px] font-bold uppercase tracking-wide text-slate-500">Tool yang diizinkan</p>
              {availableConfigurationTools.length ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {availableConfigurationTools.map((tool) => (
                    <label key={tool.key} className="flex items-start gap-2 rounded-xl border border-slate-100 bg-slate-50 p-2 text-[10px] text-slate-700">
                      <input type="checkbox" checked={configurationToolKeys.includes(tool.key)} onChange={(event) => setConfigurationToolKeys((current) => event.target.checked ? [...current, tool.key] : current.filter((key) => key !== tool.key))} />
                      <span><strong>{tool.key}</strong><span className="block text-slate-500">{tool.risk} · {tool.approval_mode}</span></span>
                    </label>
                  ))}
                </div>
              ) : <p className="text-[10px] text-slate-500">Memuat katalog tool runtime…</p>}
            </div>
            {configurationError && <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-2 text-[10px] text-rose-700">{configurationError}</p>}
            <div className="flex gap-2">
              <button type="button" onClick={() => void saveConfiguration()} disabled={savingConfiguration || !configurationName.trim()} className="flex-1 rounded-xl bg-red-600 px-3 py-2.5 text-xs font-bold text-white disabled:opacity-50">{savingConfiguration ? 'Menyimpan…' : editingConfigurationId ? 'Simpan Perubahan' : 'Simpan Agent'}</button>
              {editingConfigurationId && <button type="button" onClick={resetConfigurationForm} className="rounded-xl border border-slate-200 px-3 py-2.5 text-xs font-semibold text-slate-700">Batal</button>}
            </div>
          </section>
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
