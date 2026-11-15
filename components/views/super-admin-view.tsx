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
type ProviderCatalog = {
  providers: Array<{id:string;key:string;display_name:string;enabled:boolean;base_url:string|null;secret_env_name:string|null;configured:boolean}>;
  models: Array<{id:string;provider_id:string;key:string;display_name:string;enabled:boolean;input_cost_per_million:number;output_cost_per_million:number;max_input_tokens:number|null;max_output_tokens:number|null;capabilities:string[]}>;
  routing_policies: Array<{id:string;task_type:string;model_id:string;fallback_model_id:string|null;priority:number;enabled:boolean}>;
};

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

async function adminMutation<T>(path: string, method: 'POST' | 'PATCH', body: Record<string, unknown>): Promise<T> {
  if (!API) throw new Error('NEXT_PUBLIC_MOREAI_API_URL belum dikonfigurasi.');
  const { data, error } = await createSupabaseBrowserClient().auth.getSession();
  if (error || !data.session?.access_token) throw new Error('Sesi login tidak ditemukan. Silakan masuk kembali.');
  const response = await fetch(API + path, {
    method, headers: { Authorization: 'Bearer ' + data.session.access_token, Accept: 'application/json', 'Content-Type': 'application/json' },
    body: JSON.stringify(body), cache: 'no-store',
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail || 'Perubahan Super Admin ditolak (' + response.status + ').');
  }
  return response.json() as Promise<T>;
}

type SkillReviewRow = {
  id: string; owner_user_id: string; slug: string; name: string;
  source_repository: string; source_commit: string; source_path: string;
  license_id: string; license_url: string | null; license_evidence: string | null;
  license_status: string; validation_status: string; publication_status: string;
  validation_report: { findings?: string[]; file_count?: number; total_bytes?: number; source_inventory?: { license_files?: Array<{path:string;sha256:string}>; manifest_files?: string[]; dependency_manifests?: string[]; dependency_count?: number; exact_version_count?: number; unresolved_dependency_count?: number; warning?: string; dependencies?: Array<{ecosystem?:string;name?:string;exact_version?:string|null;license_declared?:string;license_declared_raw?:string|null;registry_metadata_status?:string}>; registry_resolution?: { exact_version_count?: number; registry_metadata_resolved_count?: number; license_assertion_count?: number; unresolved_count?: number; note?: string } } };
  requested_permissions: string[];
  installations: Array<{
    id: string; owner_user_id: string; status: string;
    permission_request: string[]; permission_status: string;
    granted_permissions: string[]; execution_enabled: boolean;
  }>;
};

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
  const [skillReviews, setSkillReviews] = useState<SkillReviewRow[]>([]);
  const [skillReviewBusy, setSkillReviewBusy] = useState<string | null>(null);
  const [skillReviewError, setSkillReviewError] = useState<string | null>(null);
  const [skillPermissionChoices, setSkillPermissionChoices] = useState<Record<string, string[]>>({});
  const [skillEvidence, setSkillEvidence] = useState<Record<string, Array<{path:string;sha256:string;byte_size:number;text_content:string|null}>>>({});
  const [activeTab, setActiveTab] = useState<'overview' | 'partners' | 'runs' | 'audit' | 'providers' | 'skills'>('overview');
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

  const loadSkillReviews = useCallback(async () => {
    setSkillReviewError(null);
    try {
      const result = await adminRequest<{ items: SkillReviewRow[] }>('/api/v1/admin/skills/pending');
      setSkillReviews(result.items);
    } catch (cause) {
      setSkillReviewError(cause instanceof Error ? cause.message : 'Skill reviews tidak dapat dimuat.');
    }
  }, []);

  useEffect(() => {
    if (activeTab === 'skills') void loadSkillReviews();
  }, [activeTab, loadSkillReviews]);

  const loadSkillEvidence = async (skillId: string) => {
    setSkillReviewBusy('evidence:' + skillId);
    setSkillReviewError(null);
    try {
      const result = await adminRequest<{ files: Array<{path:string;sha256:string;byte_size:number;text_content:string|null}> }>(
        '/api/v1/admin/skills/' + encodeURIComponent(skillId) + '/source-evidence',
      );
      setSkillEvidence(current => ({ ...current, [skillId]: result.files }));
    } catch (cause) {
      setSkillReviewError(cause instanceof Error ? cause.message : 'Bukti source tidak dapat dimuat.');
    } finally {
      setSkillReviewBusy(null);
    }
  };

  const reviewPackage = async (skill: SkillReviewRow, licenseStatus: 'approved' | 'rejected') => {
    setSkillReviewBusy(skill.id);
    setSkillReviewError(null);
    try {
      await adminMutation('/api/v1/admin/skills/' + encodeURIComponent(skill.id) + '/review', 'PATCH', {
        license_status: licenseStatus,
        publication_status: licenseStatus === 'approved' && skill.validation_status === 'validated' ? 'published' : 'private',
        review_note: 'Reviewed from MoreAI Super Admin Skill Registry.',
      });
      await loadSkillReviews();
    } catch (cause) {
      setSkillReviewError(cause instanceof Error ? cause.message : 'Review skill gagal.');
    } finally {
      setSkillReviewBusy(null);
    }
  };

  const reviewInstall = async (skill: SkillReviewRow, install: SkillReviewRow['installations'][number], decision: 'approved' | 'rejected') => {
    setSkillReviewBusy(install.id);
    setSkillReviewError(null);
    try {
      await adminMutation(
        '/api/v1/admin/skills/' + encodeURIComponent(skill.id) + '/permissions?install_id=' + encodeURIComponent(install.id),
        'PATCH',
        {
          decision,
          granted_permissions: decision === 'approved' ? (skillPermissionChoices[install.id] || []) : [],
          review_note: 'Reviewed from MoreAI Super Admin Skill Registry.',
        },
      );
      await loadSkillReviews();
    } catch (cause) {
      setSkillReviewError(cause instanceof Error ? cause.message : 'Permission review gagal.');
    } finally {
      setSkillReviewBusy(null);
    }
  };

  const tabs = [
    ['overview', 'Ringkasan'],
    ['partners', 'Organisasi Mitra'],
    ['runs', 'Agent Runs'],
    ['audit', 'Audit Log'],
    ['providers', 'Provider & Model'],
    ['skills', 'AI Skills Review'],
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
        {!loading && activeTab === 'providers' && providerCatalog && <ProviderManagement catalog={providerCatalog} onRefresh={load} />}
        {!loading && activeTab === 'skills' && <section className="space-y-4">
          <div className="flex items-center justify-between gap-3"><div><h2 className="font-bold">AI Skills Trust & Permission Review</h2><p className="mt-1 text-xs text-slate-500">Review provenance, validation, license, publication dan permission sebelum skill dapat digunakan OpenManus.</p></div><button onClick={() => void loadSkillReviews()} className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold">Muat ulang</button></div>
          {skillReviewError && <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">{skillReviewError}</p>}
          {skillReviews.length === 0 ? <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500">Tidak ada review skill yang tertunda.</div> : skillReviews.map(skill => <article key={skill.id} className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-2"><div><h3 className="font-bold">{skill.name}</h3><p className="text-xs text-slate-500">{skill.slug} · {skill.source_repository} · {skill.source_path}</p></div><div className="flex flex-wrap gap-1 text-[10px]"><span className="rounded-full bg-slate-100 px-2 py-1">{skill.validation_status}</span><span className="rounded-full bg-amber-50 px-2 py-1 text-amber-800">{skill.license_status}</span><span className="rounded-full bg-slate-100 px-2 py-1">{skill.publication_status}</span></div></div>
            <div className="grid gap-2 rounded-xl bg-slate-50 p-3 text-[10px] text-slate-600 sm:grid-cols-2"><p>Commit: <span className="font-mono">{skill.source_commit}</span></p><p>License: {skill.license_id} · {skill.license_url || 'URL tidak tersedia'}</p><p>Files ingested: {skill.validation_report?.file_count ?? '—'}</p><p>Package bytes: {skill.validation_report?.total_bytes ?? '—'}</p></div>
            {skill.license_evidence && <p className="rounded-xl border border-slate-100 p-3 text-xs text-slate-600">{skill.license_evidence}</p>}
            {skill.validation_report?.findings?.length ? <ul className="list-disc space-y-1 pl-5 text-[11px] text-amber-800">{skill.validation_report.findings.map((finding,index)=><li key={index}>{finding}</li>)}</ul> : null}
            {skill.validation_report?.source_inventory && <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-[10px] text-slate-600">
              <p className="font-bold text-slate-800">Source manifest & dependency inventory</p>
              <p>Manifest: {(skill.validation_report.source_inventory.manifest_files||[]).join(', ')||'Belum ditemukan'}</p>
              <p>License/NOTICE: {(skill.validation_report.source_inventory.license_files||[]).map(file=>file.path).join(', ')||'Belum ditemukan'}</p>
              <p>Dependency manifests: {(skill.validation_report.source_inventory.dependency_manifests||[]).join(', ')||'Tidak ditemukan'}</p>
              <p>Dependencies: {skill.validation_report.source_inventory.exact_version_count||0} exact-version / {skill.validation_report.source_inventory.dependency_count||0} terdeteksi · {skill.validation_report.source_inventory.unresolved_dependency_count||0} belum exact</p>
              <p>Registry metadata: {skill.validation_report.source_inventory.registry_resolution?.registry_metadata_resolved_count||0} ter-resolve · {skill.validation_report.source_inventory.registry_resolution?.license_assertion_count||0} deklarasi lisensi · {skill.validation_report.source_inventory.registry_resolution?.unresolved_count||0} belum terselesaikan</p>
              {skill.validation_report.source_inventory.warning&&<p className="mt-1 text-amber-800">{skill.validation_report.source_inventory.warning}</p>}
              {(skill.validation_report.source_inventory.dependencies||[]).length>0&&<div className="mt-2 max-h-44 space-y-1 overflow-y-auto border-t border-slate-200 pt-2">
                <p className="font-bold text-slate-700">Dependency evidence (maks. 100)</p>
                {(skill.validation_report.source_inventory.dependencies||[]).slice(0,100).map((dependency,index)=><p key={index} className="break-all">{dependency.ecosystem} · {dependency.name} · {dependency.exact_version||'versi tidak exact'} · {dependency.license_declared||'NOASSERTION'} · {dependency.registry_metadata_status||'unresolved'}{dependency.license_declared_raw?' · raw: '+dependency.license_declared_raw:''}</p>)}
              </div>}
            </div>}

            <button disabled={skillReviewBusy==='evidence:'+skill.id} onClick={()=>void loadSkillEvidence(skill.id)} className="rounded-xl border border-slate-200 px-3 py-2 text-[11px] font-semibold text-slate-700">Lihat bukti LICENSE / NOTICE / manifest</button>
            {skillEvidence[skill.id]&&<div className="space-y-2 rounded-xl border border-slate-200 bg-slate-50 p-3">{skillEvidence[skill.id].map(file=><details key={file.path} className="rounded-lg border border-slate-200 bg-white p-2"><summary className="cursor-pointer text-[10px] font-semibold text-slate-800">{file.path} · {file.byte_size} bytes · SHA-256 {file.sha256.slice(0,16)}…</summary><pre className="mt-2 max-h-56 overflow-auto whitespace-pre-wrap break-words text-[10px] text-slate-600">{file.text_content || 'Konten teks tidak tersedia; gunakan hash dan referensi sumber untuk review manual.'}</pre></details>)}</div>}
            <div className="flex flex-wrap gap-2"><button disabled={skillReviewBusy===skill.id || skill.validation_status!=='validated'} onClick={()=>void reviewPackage(skill,'approved')} className="rounded-xl bg-red-600 px-3 py-2 text-[11px] font-bold text-white disabled:opacity-40">Setujui lisensi & publikasikan</button><button disabled={skillReviewBusy===skill.id} onClick={()=>void reviewPackage(skill,'rejected')} className="rounded-xl border border-rose-200 px-3 py-2 text-[11px] font-semibold text-rose-700 disabled:opacity-40">Tolak lisensi</button></div>
            {skill.installations.map(install=><div key={install.id} className="space-y-2 rounded-xl border border-slate-200 p-3">
              <div className="flex flex-wrap items-center justify-between gap-2"><p className="text-xs font-bold">Install {install.id.slice(0,8)} · {install.permission_status}</p><span className="text-[10px] text-slate-500">Owner {install.owner_user_id.slice(0,8)} · eksekusi {install.execution_enabled?'aktif':'nonaktif'}</span></div>
              <div className="grid gap-2 sm:grid-cols-3">{install.permission_request.map(permission=><label key={permission} className="flex items-center gap-2 text-[10px] text-slate-700"><input type="checkbox" checked={(skillPermissionChoices[install.id] || []).includes(permission)} onChange={event=>setSkillPermissionChoices(current=>({...current,[install.id]:event.target.checked?[...(current[install.id]||[]),permission]:(current[install.id]||[]).filter(item=>item!==permission)}))} className="accent-red-600"/>{permission}</label>)}</div>
              <div className="flex gap-2"><button disabled={skillReviewBusy===install.id || install.permission_status!=='pending_review'} onClick={()=>void reviewInstall(skill,install,'approved')} className="rounded-lg bg-red-600 px-3 py-1.5 text-[10px] font-bold text-white disabled:opacity-40">Setujui permission terpilih</button><button disabled={skillReviewBusy===install.id || install.permission_status!=='pending_review'} onClick={()=>void reviewInstall(skill,install,'rejected')} className="rounded-lg border border-rose-200 px-3 py-1.5 text-[10px] font-semibold text-rose-700 disabled:opacity-40">Tolak permission</button></div>
            </div>)}
          </article>)}
        </section>}

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


function ProviderManagement({ catalog, onRefresh }: { catalog: ProviderCatalog; onRefresh: () => Promise<void> }) {
  const [providerId, setProviderId] = useState('');
  const [providerKey, setProviderKey] = useState<'google' | 'openai'>('openai');
  const [providerName, setProviderName] = useState('OpenAI Compatible');
  const [baseUrl, setBaseUrl] = useState('');
  const [secretEnvName, setSecretEnvName] = useState('MOREAI_PROVIDER_OPENAI_API_KEY');
  const [credentialsReady, setCredentialsReady] = useState(false);
  const [modelProviderId, setModelProviderId] = useState('');
  const [modelKey, setModelKey] = useState('');
  const [modelName, setModelName] = useState('');
  const [inputCost, setInputCost] = useState('');
  const [outputCost, setOutputCost] = useState('');
  const [modelEnabled, setModelEnabled] = useState(false);
  const [maxInputTokens, setMaxInputTokens] = useState('');
  const [maxOutputTokens, setMaxOutputTokens] = useState('');
  const [routeTask, setRouteTask] = useState<'chat' | 'planning' | 'general'>('chat');
  const [routeModelId, setRouteModelId] = useState('');
  const [routePriority, setRoutePriority] = useState('100');
  const [routeEnabled, setRouteEnabled] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const providerRows: Row[] = catalog.providers.map(provider => ({
    id: provider.id, provider: provider.display_name, key: provider.key,
    endpoint: provider.base_url || 'Not configured',
    secret_reference: provider.secret_env_name || 'Not configured',
    status: provider.enabled ? 'Enabled' : 'Disabled · readiness gate',
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
  const selectedProvider = catalog.providers.find(provider => provider.id === providerId);

  async function submitProvider(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy('provider'); setNotice(null); setFormError(null);
    try {
      const suffix = providerId ? '?provider_id=' + encodeURIComponent(providerId) : '';
      await adminMutation('/api/v1/admin/providers' + suffix, 'POST', {
        key: selectedProvider?.key || providerKey,
        display_name: providerName,
        enabled: credentialsReady,
        credentials_ready: credentialsReady,
        base_url: baseUrl,
        secret_env_name: secretEnvName,
      });
      setNotice(credentialsReady ? 'Provider diaktifkan berdasarkan konfirmasi pemasangan secret host. Worker tetap harus melewati pemeriksaan readiness sebelum menerima Agent Run.' : 'Metadata provider dan referensi secret tersimpan. Provider tetap nonaktif.');
      await onRefresh();
    } catch (error) {
      setFormError(error instanceof Error ? error.message : 'Konfigurasi provider gagal disimpan.');
    } finally { setBusy(null); }
  }

  async function submitModel(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy('model'); setNotice(null); setFormError(null);
    try {
      await adminMutation('/api/v1/admin/models', 'POST', {
        provider_id: modelProviderId, key: modelKey.trim(), display_name: modelName.trim(),
        input_cost_per_million: Number(inputCost), output_cost_per_million: Number(outputCost),
        max_input_tokens: maxInputTokens ? Number(maxInputTokens) : null,
        max_output_tokens: maxOutputTokens ? Number(maxOutputTokens) : null,
        capabilities: ['text'], enabled: modelEnabled,
      });
      setNotice(modelEnabled ? 'Model diaktifkan. Worker tetap memvalidasi provider secret dan route sebelum menerima pekerjaan.' : 'Model tersimpan dalam status nonaktif. Harga dan kemampuan harus disesuaikan dengan kontrak provider sebelum aktivasi.');
      await onRefresh();
    } catch (error) {
      setFormError(error instanceof Error ? error.message : 'Konfigurasi model gagal disimpan.');
    } finally { setBusy(null); }
  }

  async function submitRoute(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy('route'); setNotice(null); setFormError(null);
    try {
      await adminMutation('/api/v1/admin/routing-policies', 'POST', {
        task_type: routeTask, model_id: routeModelId, fallback_model_id: null,
        priority: Number(routePriority), enabled: routeEnabled,
      });
      setNotice('Routing policy ' + routeTask + (routeEnabled ? ' diaktifkan.' : ' tersimpan nonaktif.'));
      await onRefresh();
    } catch (error) {
      setFormError(error instanceof Error ? error.message : 'Routing policy gagal disimpan.');
    } finally { setBusy(null); }
  }

  const fieldClass = 'mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-red-400 focus:ring-2 focus:ring-red-100';
  const buttonClass = 'inline-flex min-h-10 items-center justify-center rounded-xl bg-[#E31E24] px-4 py-2 text-sm font-semibold text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50';
  const labelClass = 'block text-xs font-semibold text-slate-600';

  return <div className="space-y-5">
    <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div><h2 className="font-bold text-slate-900">LLM Provider Registry</h2><p className="mt-1 text-xs text-slate-500">Konfigurasi endpoint dan nama environment secret. Nilai API key tidak pernah dikirim atau disimpan di database.</p></div>
        <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">Activation locked</span>
      </div>
      <div className="mt-4"><DataTable title="Provider" rows={providerRows} columns={['provider', 'key', 'endpoint', 'secret_reference', 'status', 'models']} /></div>
      <form onSubmit={submitProvider} className="mt-5 grid gap-3 rounded-xl border border-slate-100 bg-slate-50 p-4 md:grid-cols-2">
        <div className="md:col-span-2"><h3 className="text-sm font-semibold text-slate-900">Configure provider endpoint</h3><p className="mt-1 text-xs text-slate-500">Gunakan HTTPS endpoint publik milik provider. Masukkan nama variabel environment yang akan dibuat di secret manager host worker.</p></div>
        <label className={labelClass}>Provider
          <select className={fieldClass} value={providerId} onChange={event => { const nextId = event.target.value; const nextProvider = catalog.providers.find(provider => provider.id === nextId); setProviderId(nextId); if (nextProvider) { setProviderName(nextProvider.display_name); setBaseUrl(nextProvider.base_url || ""); setSecretEnvName(nextProvider.secret_env_name || ""); setCredentialsReady(nextProvider.enabled); } else { setProviderName("OpenAI Compatible"); setBaseUrl(""); setSecretEnvName("MOREAI_PROVIDER_OPENAI_API_KEY"); setCredentialsReady(false); } }}>
            <option value="">Create new provider</option>
            {catalog.providers.map(provider => <option key={provider.id} value={provider.id}>{provider.display_name} ({provider.key})</option>)}
          </select>
        </label>
        {!providerId && <label className={labelClass}>Provider key
          <select className={fieldClass} value={providerKey} onChange={event => { setProviderKey(event.target.value as typeof providerKey); setProviderName(event.target.value === 'openai' ? 'OpenAI Compatible' : 'Google'); setSecretEnvName('MOREAI_PROVIDER_' + event.target.value.toUpperCase() + '_API_KEY'); }}>
            <option value="openai">openai</option><option value="google">google</option>
          </select>
        </label>}
        <label className={labelClass}>Display name
          <input className={fieldClass} value={providerName} onChange={event => setProviderName(event.target.value)} minLength={2} maxLength={120} required />
        </label>
        <label className={labelClass}>HTTPS base URL
          <input className={fieldClass} type="url" value={baseUrl} onChange={event => setBaseUrl(event.target.value)} placeholder="https://api.openai.com/v1" required />
        </label>
        <label className={labelClass}>Worker secret environment name
          <input className={fieldClass} value={secretEnvName} onChange={event => setSecretEnvName(event.target.value)} pattern="MOREAI_PROVIDER_[A-Z0-9_]+" minLength={17} maxLength={128} required />
        </label>
        <label className="md:col-span-2 flex items-start gap-2 text-xs text-slate-600">
          <input type="checkbox" className="mt-0.5 accent-[#E31E24]" checked={credentialsReady} onChange={event => setCredentialsReady(event.target.checked)} />
          I confirm the actual API key has already been installed in the persistent worker host secret manager under the exact environment name above.
        </label>
        <div className="md:col-span-2 flex flex-wrap items-center justify-between gap-3">
          <p className="max-w-2xl text-xs text-slate-500">Jangan masukkan API key di sini. Jika kotak konfirmasi tidak dicentang, provider tetap nonaktif. Worker akan memeriksa ulang keberadaan secret saat startup.</p>
          <button className={buttonClass} disabled={busy !== null}>{busy === 'provider' ? 'Saving…' : credentialsReady ? 'Save & enable provider' : 'Save disabled provider'}</button>
        </div>
      </form>
    </section>
    <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="font-bold text-slate-900">Model Catalog & Pricing</h2>
      <div className="mt-3"><DataTable title="Models" rows={modelRows} columns={['model', 'key', 'status', 'input_cost_per_million', 'output_cost_per_million', 'capabilities']} /></div>
      <form onSubmit={submitModel} className="mt-4 grid gap-3 rounded-xl border border-slate-100 bg-slate-50 p-4 md:grid-cols-2">
        <div className="md:col-span-2"><h3 className="text-sm font-semibold text-slate-900">Register model</h3><p className="mt-1 text-xs text-slate-500">Masukkan harga resmi provider per satu juta token. Model dibuat nonaktif sampai dikonfigurasi dan ditinjau.</p></div>
        <label className={labelClass}>Provider
          <select className={fieldClass} value={modelProviderId} onChange={event => setModelProviderId(event.target.value)} required>
            <option value="">Select provider</option>{catalog.providers.map(provider => <option key={provider.id} value={provider.id}>{provider.display_name}</option>)}
          </select>
        </label>
        <label className={labelClass}>Model key<input className={fieldClass} value={modelKey} onChange={event => setModelKey(event.target.value)} required maxLength={160} /></label>
        <label className={labelClass}>Display name<input className={fieldClass} value={modelName} onChange={event => setModelName(event.target.value)} required maxLength={160} /></label>
        <label className={labelClass}>Input cost / 1M tokens<input className={fieldClass} type="number" min="0" step="0.000001" value={inputCost} onChange={event => setInputCost(event.target.value)} required /></label>
        <label className={labelClass}>Output cost / 1M tokens<input className={fieldClass} type="number" min="0" step="0.000001" value={outputCost} onChange={event => setOutputCost(event.target.value)} required /></label>
        <label className={labelClass}>Max input tokens<input className={fieldClass} type="number" min="1" value={maxInputTokens} onChange={event => setMaxInputTokens(event.target.value)} /></label>
        <label className={labelClass}>Max output tokens<input className={fieldClass} type="number" min="1" value={maxOutputTokens} onChange={event => setMaxOutputTokens(event.target.value)} required={modelEnabled} /></label>
        <label className="md:col-span-2 flex items-start gap-2 text-xs text-slate-600"><input type="checkbox" className="mt-0.5 accent-[#E31E24]" checked={modelEnabled} onChange={event => setModelEnabled(event.target.checked)} />Enable model only when its provider is enabled and its pricing/token limits are verified.</label>
        <div className="md:col-span-2 flex justify-end"><button className={buttonClass} disabled={busy !== null || catalog.providers.length === 0}>{busy === 'model' ? 'Saving…' : modelEnabled ? 'Register enabled model' : 'Register disabled model'}</button></div>
      </form>
    </section>
    <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="font-bold text-slate-900">Platform Routing Policies</h2>
      <div className="mt-3"><DataTable title="Routes" rows={routeRows} columns={['task', 'model_id', 'fallback_model_id', 'priority', 'status']} /></div>
      <form onSubmit={submitRoute} className="mt-4 grid gap-3 rounded-xl border border-slate-100 bg-slate-50 p-4 md:grid-cols-3">
        <label className={labelClass}>Task type<select className={fieldClass} value={routeTask} onChange={event => setRouteTask(event.target.value as typeof routeTask)}><option value="chat">chat</option><option value="planning">planning</option><option value="general">general</option></select></label>
        <label className={labelClass}>Model<select className={fieldClass} value={routeModelId} onChange={event => setRouteModelId(event.target.value)} required><option value="">Select model</option>{catalog.models.map(model => <option key={model.id} value={model.id}>{model.display_name} · {model.enabled ? 'enabled' : 'disabled'}</option>)}</select></label>
        <label className={labelClass}>Priority<input className={fieldClass} type="number" min="0" max="10000" value={routePriority} onChange={event => setRoutePriority(event.target.value)} required /></label>
        <label className="md:col-span-3 flex items-start gap-2 text-xs text-slate-600"><input type="checkbox" className="mt-0.5 accent-[#E31E24]" checked={routeEnabled} onChange={event => setRouteEnabled(event.target.checked)} />Enable route only after its model and provider have been enabled and the worker secret is installed.</label>
        <div className="md:col-span-3 flex flex-wrap items-center justify-between gap-3"><p className="text-xs text-slate-500">Worker startup requires enabled chat and planning routes plus valid secret references, wallet, quota, and billing settings.</p><button className={buttonClass} disabled={busy !== null || catalog.models.length === 0}>{busy === 'route' ? 'Saving…' : routeEnabled ? 'Create enabled route' : 'Create disabled route'}</button></div>
      </form>
    </section>
    {notice && <p role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{notice}</p>}
    {formError && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{formError}</p>}
  </div>;
}
