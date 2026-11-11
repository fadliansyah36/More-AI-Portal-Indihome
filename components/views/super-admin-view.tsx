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
type Row = Record<string, string | number | null>;

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
  const [activeTab, setActiveTab] = useState<'overview' | 'partners' | 'runs' | 'audit'>('overview');
  const [principal, setPrincipal] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [context, summary, partnerRows, runRows, auditRows] = await Promise.all([
        adminRequest<{ principal: { roles: string[] } }>('/api/v1/admin/context'),
        adminRequest<Overview>('/api/v1/admin/overview'),
        adminRequest<{ items: Row[] }>('/api/v1/admin/partners?limit=50'),
        adminRequest<{ items: Row[] }>('/api/v1/admin/agent-runs?limit=50'),
        adminRequest<{ items: Row[] }>('/api/v1/admin/audit?limit=50'),
      ]);
      setPrincipal(context.principal.roles);
      setOverview(summary);
      setPartners(partnerRows.items);
      setRuns(runRows.items);
      setAudit(auditRows.items);
    } catch (err) {
      setOverview(null);
      setPartners([]);
      setRuns([]);
      setAudit([]);
      setError(err instanceof Error ? err.message : 'Workspace Super Admin gagal dimuat.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const tabs = [
    ['overview', 'Ringkasan'],
    ['partners', 'Organisasi Mitra'],
    ['runs', 'Agent Runs'],
    ['audit', 'Audit Log'],
  ] as const;

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-red-600 text-white"><ShieldCheck className="h-5 w-5" /></div>
            <div><p className="text-xs font-bold uppercase tracking-wider text-red-600">MoreAI Platform</p><h1 className="text-lg font-bold">Super Admin</h1></div>
          </div>
          <button onClick={() => void load()} disabled={loading} className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold hover:bg-slate-50 disabled:opacity-50">
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
        <footer className="border-t border-slate-200 pt-4 text-xs text-slate-500">MoreAI · Administrative data is read-only in this release. Mutations require explicit permission contracts and audit coverage.</footer>
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
