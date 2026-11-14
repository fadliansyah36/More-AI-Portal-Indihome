'use client';

import { useCallback, useEffect, useState } from 'react';
import { createSupabaseBrowserClient } from '@/lib/supabase/client';
import { ShieldCheck, RefreshCw, Building2, Users, Activity, Bot, ClipboardList, AlertTriangle } from 'lucide-react';

type Overview = {
  totals: Record<string, number | null>;
  recent_agent_runs: Array<{ id: string; status: string; created_at: string; attempt: number; max_attempts: number }>;
  recent_partners: Array<{ id: string; display_name: string; status: string; created_at: string }>;
  count_note: string;
};
type Row = Record<string, string | number | boolean | null>;
type ProviderCatalog = { providers: Array<{id:string;key:string;display_name:string;enabled:boolean}>; models: Array<{id:string;provider_id:string;key:string;display_name:string;enabled:boolean;input_cost_per_million:number;output_cost_per_million:number;capabilities:string[]}>; routing_policies: Array<{id:string;task_type:string;model_id:string;fallback_model_id:string|null;priority:number;enabled:boolean}> };

const API = (process.env.NEXT_PUBLIC_MOREAI_API_URL || '').replace(/\/$/, '');

async function adminRequest<T>(path: string): Promise<T> {
  if (!API) throw new Error('NEXT_PUBLIC_MOREAI_API_URL belum dikonfigurasi.');
  const { data, error } = await createSupabaseBrowserClient().auth.getSession();
  if (error || !data.session?.access_token) throw new Error('Sesi login tidak ditemukan. Silakan masuk kembali.');
  const response = await fetch(API + path, {
    headers: { Authorization: 'Bearer ' + data.session.access_token, Accept: 'application/json' },
    cache: 'no-store',
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail || 'Akses Super Admin ditolak (' + response.status + ').');
  }
  return response.json() as Promise<T>;
}

const metricCards = [
  ['users', 'Pengguna', Users],
  ['partners', 'Organisasi Mitra', Building2],
  ['locations', 'Lokasi', Activity],
  ['active_network_sessions', 'Sesi Jaringan Aktif', Activity],
  ['agent_runs', 'Agent Runs', Bot],
  ['pending_tool_approvals', 'Approval Tertunda', ShieldCheck],
] as const;

export default function SuperAdminPage() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [partners, setPartners] = useState<Row[]>([]);
  const [runs, setRuns] = useState<Row[]>([]);
  const [audit, setAudit] = useState<Row[]>([]);
  const [providerCatalog, setProviderCatalog] = useState<ProviderCatalog | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'partners' | 'runs' | 'audit' | 'providers'>('overview');
  const [principal, setPrincipal] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [context, summary, partnerRows, runRows, auditRows, providerRows] = await Promise.all([
        adminRequest<{ principal: { roles: string[] } }>('/api/v1/admin/context'),
        adminRequest<Overview>('/api/v1/admin/overview'),
        adminRequest<{ items: Row[] }>('/api/v1/admin/partners?limit=50'),
        adminRequest<{ items: Row[] }>('/api/v1/admin/agent-runs?limit=50'),
        adminRequest<{ items: Row[] }>('/api/v1/admin/audit?limit=50'),
        adminRequest<ProviderCatalog>('/api/v1/admin/providers'),
      ]);
      setPrincipal(context.principal.roles);
      setOverview(summary);
      setPartners(partnerRows.items);
      setRuns(runRows.items);
      setAudit(auditRows.items);
      setProviderCatalog(providerRows);
      setError(null);
    } catch (err) {
      setOverview(null);
      setPartners([]);
      setRuns([]);
      setAudit([]);
      setProviderCatalog(null);
      setError(err instanceof Error ? err.message : 'Workspace Super Admin gagal dimuat.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    void Promise.resolve().then(() => { if (active) void load(); });
    return () => { active = false; };
  }, [load]);

  const tabs = [
    ['overview', 'Ringkasan'],
    ['partners', 'Organisasi Mitra'],
    ['runs', 'Agent Runs'],
    ['audit', 'Audit Log'],
    ['providers', 'Provider & Model'],
  ] as const;

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-red-600 text-white"><ShieldCheck className="h-5 w-5" /></div>
            <div><p className="text-xs font-bold uppercase tracking-wider text-red-600">MoreAI Platform</p><h1 className="text-lg font-bold">Super Admin</h1></div>
          </div>
          <button onClick={() => { setLoading(true); setError(null); void load(); }} disabled={loading} className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold hover:bg-slate-50 disabled:opacity-50">
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /> Segarkan
          </button>
        </div>
      </header>
      <div className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6">
        <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div><h2 className="font-bold">Platform Control Center</h2><p className="mt-1 text-xs text-slate-500">Data live dari FastAPI dan Supabase. Akses ditentukan server berdasarkan role platform.</p></div>
            <div className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">{principal.length ? principal.join(' · ') : 'Memvalidasi akses'}</div>
          </div>
        </section>
        {error && <div role="alert" className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900"><AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />{error}</div>}
        <nav className="flex gap-2 overflow-x-auto border-b border-slate-200">
          {tabs.map(([key, label]) => <button key={key} onClick={() => setActiveTab(key)} className={`whitespace-nowrap border-b-2 px-3 py-3 text-sm font-semibold ${activeTab === key ? 'border-red-600 text-red-600' : 'border-transparent text-slate-500 hover:text-slate-900'}`}>{label}</button>)}
        </nav>
        {loading && <p className="py-10 text-center text-sm text-slate-500">Memuat data platform…</p>}
        {!loading && activeTab === 'overview' && overview && <>
          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {metricCards.map(([key, label, Icon]) => <article key={key} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"><div className="flex items-center justify-between text-slate-500"><span className="text-sm font-medium">{label}</span><Icon className="h-5 w-5" /></div><p className="mt-3 text-3xl font-black">{overview.totals[key] === null ? '500+' : (overview.totals[key] ?? 0).toLocaleString('id-ID')}</p></article>)}
          </section>
          <p className="text-xs text-slate-500">{overview.count_note}</p>
          <section className="grid gap-4 lg:grid-cols-2">
            <DataTable title="Agent Run Terbaru" rows={overview.recent_agent_runs as unknown as Row[]} columns={['id', 'status', 'created_at']} />
            <DataTable title="Mitra Terbaru" rows={overview.recent_partners as unknown as Row[]} columns={['display_name', 'status', 'created_at']} />
          </section>
        </>}
        {!loading && activeTab === 'partners' && <DataTable title="Organisasi Mitra" rows={partners} columns={['display_name', 'legal_name', 'status', 'created_at']} />}
        {!loading && activeTab === 'runs' && <DataTable title="Agent Runs" rows={runs} columns={['id', 'status', 'attempt', 'created_at']} />}
        {!loading && activeTab === 'audit' && <DataTable title="Audit Log" rows={audit} columns={['action', 'resource_type', 'outcome', 'created_at']} />}
        {!loading && activeTab === 'providers' && providerCatalog && <ProviderManagement catalog={providerCatalog} />}
        <footer className="border-t border-slate-200 pt-4 text-xs text-slate-500">MoreAI · Provider/model/routing changes use server-side platform permissions and audited database procedures. Credential values are never exposed to the browser.</footer>
      </div>
    </main>
  );
}

function DataTable({ title, rows, columns }: { title: string; rows: Row[]; columns: string[] }) {
  return <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
    <div className="border-b border-slate-100 px-4 py-3 font-bold">{title} <span className="ml-1 text-xs font-normal text-slate-400">({rows.length})</span></div>
    {rows.length === 0 ? <p className="p-5 text-sm text-slate-500">Belum ada data.</p> : <div className="overflow-x-auto"><table className="w-full min-w-[520px] text-left text-xs"><thead className="bg-slate-50 text-slate-500"><tr>{columns.map(column => <th key={column} className="px-4 py-3 font-semibold">{column.replaceAll('_', ' ')}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={String(row.id || index)} className="border-t border-slate-100">{columns.map(column => <td key={column} className="max-w-[260px] truncate px-4 py-3 text-slate-700">{row[column] == null ? '—' : String(row[column])}</td>)}</tr>)}</tbody></table></div>}
  </section>;
}


function ProviderManagement({ catalog }: { catalog: ProviderCatalog }) {
  const providerRows: Row[] = catalog.providers.map(provider => ({
    id: provider.id, provider: provider.display_name, key: provider.key,
    status: provider.enabled ? 'Enabled · credential gate enforced' : 'Disabled',
    models: catalog.models.filter(model => model.provider_id === provider.id).length,
  }));
  const modelRows: Row[] = catalog.models.map(model => ({
    id: model.id, model: model.display_name, key: model.key,
    status: model.enabled ? 'Enabled' : 'Disabled',
    input_cost_per_million: model.input_cost_per_million,
    output_cost_per_million: model.output_cost_per_million,
    capabilities: model.capabilities.join(', '),
  }));
  const routeRows: Row[] = catalog.routing_policies.map(route => ({
    id: route.id, task: route.task_type, model_id: route.model_id,
    fallback_model_id: route.fallback_model_id, priority: route.priority,
    status: route.enabled ? 'Enabled' : 'Disabled',
  }));
  return <div className="space-y-5">
    <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="font-bold">LLM Provider Registry</h2>
      <p className="mt-1 text-xs text-slate-500">Metadata only. Secret values and provider config are never returned. Activation requires verified server-side credentials and provider readiness.</p>
      <div className="mt-4"><DataTable title="Provider" rows={providerRows} columns={['provider', 'key', 'status', 'models']} /></div>
    </section>
    <DataTable title="Model Catalog & Pricing" rows={modelRows} columns={['model', 'key', 'status', 'input_cost_per_million', 'output_cost_per_million', 'capabilities']} />
    <DataTable title="Platform Routing Policies" rows={routeRows} columns={['task', 'model_id', 'fallback_model_id', 'priority', 'status']} />
  </div>;
}
