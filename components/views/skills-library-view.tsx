'use client';

import React, { useEffect, useState } from 'react';
import { ShieldCheck, PackagePlus, RefreshCw, LockKeyhole, AlertCircle, Plus, X, Search } from 'lucide-react';
import { customerSkillApi, type CustomerSkillPackage, type PinnedSkillCatalogItem } from '@/lib/api/client';

const permissionOptions = ['network.read','workspace.read','workspace.write','browser.navigate','browser.download','search.web','files.read','files.write','calendar.read','calendar.write','gmail.read','gmail.send'];

const emptyForm = {
  slug: '', name: '', description: '', source_repository: 'smixs/visual-skills',
  source_ref: 'main', source_commit: '', source_path: '', source_blob_sha: '',
  content_sha256: '', version: '1.0.0', license_id: 'CC-BY-4.0',
  license_url: 'https://creativecommons.org/licenses/by/4.0/',
  license_evidence: '', requested_permissions: [] as string[],
};

export function SkillsLibraryView() {
  const [items, setItems] = useState<CustomerSkillPackage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [showImport, setShowImport] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [showCatalog, setShowCatalog] = useState(false);
  const [catalogItems, setCatalogItems] = useState<PinnedSkillCatalogItem[]>([]);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [catalogSearch, setCatalogSearch] = useState('');
  const [bulkProgress, setBulkProgress] = useState<{ total: number; completed: number; failed: number; current: string; failures: string[] } | null>(null);

  const refresh = async () => {
    setLoading(true); setError(null);
    try { setItems((await customerSkillApi.list()).items); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Skill Registry tidak dapat dimuat.'); }
    finally { setLoading(false); }
  };
  useEffect(() => { void refresh(); }, []);

  const loadCatalog = async () => {
    setCatalogLoading(true); setError(null);
    try { setCatalogItems((await customerSkillApi.catalog()).items); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Katalog pinned skills tidak tersedia.'); }
    finally { setCatalogLoading(false); }
  };

  const toggleCatalog = async () => {
    const next = !showCatalog;
    setShowCatalog(next);
    if (next && catalogItems.length === 0) await loadCatalog();
  };

  const importPinned = async (item: PinnedSkillCatalogItem) => {
    setBusy(item.source_path); setError(null);
    try {
      await customerSkillApi.importPinned({
        source_repository: item.source_repository,
        source_commit: item.source_commit,
        source_path: item.source_path,
      });
      setCatalogItems(current => current.map(value =>
        value.source_path === item.source_path && value.source_repository === item.source_repository
          ? { ...value, imported: true } : value,
      ));
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Import pinned skill gagal.');
    } finally { setBusy(null); }
  };

  const ingestAllMotion = async () => {
    const motion = catalogItems.filter(item => item.source_repository.startsWith('iart-ai/'));
    if (!motion.length) {
      setError('Pinned Motion Skills belum dimuat atau katalog kosong.');
      return;
    }
    setBusy('motion-bulk');
    setError(null);
    const failures: string[] = [];
    let completed = 0;
    try {
      let packages = (await customerSkillApi.list()).items;
      setItems(packages);
      setBulkProgress({ total: motion.length, completed: 0, failed: 0, current: 'Menyiapkan katalog Motion…', failures: [] });
      for (const source of motion) {
        setBulkProgress({ total: motion.length, completed, failed: failures.length, current: source.name, failures: failures.slice(0, 5) });
        try {
          let skill = packages.find(item =>
            item.source_repository === source.source_repository
            && item.source_path === source.source_path
            && item.source_commit === source.source_commit,
          );
          if (!skill) {
            skill = await customerSkillApi.importPinned({
              source_repository: source.source_repository,
              source_commit: source.source_commit,
              source_path: source.source_path,
            });
            packages = [...packages, skill];
          }
          // Recursive ingestion fetches the complete skill directory and local
          // references with the existing path, blob-hash and size boundaries.
          // Validation records SBOM/license findings but never publishes or installs.
          await customerSkillApi.ingest(skill.id);
          await customerSkillApi.validate(skill.id);
        } catch (cause) {
          failures.push(source.name + ': ' + (cause instanceof Error ? cause.message : 'ingest/validation gagal'));
        }
        completed += 1;
        setBulkProgress({ total: motion.length, completed, failed: failures.length, current: source.name, failures: failures.slice(0, 5) });
      }
      await refresh();
      await loadCatalog();
      setBulkProgress({
        total: motion.length, completed, failed: failures.length, current: 'Selesai',
        failures: failures.slice(0, 5),
      });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Batch Motion Skills gagal dimulai.');
    } finally {
      setBusy(null);
    }
  };

  const validate = async (id: string) => {
    setBusy(id); setError(null);
    try { await customerSkillApi.validate(id); await refresh(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Validasi metadata gagal.'); }
    finally { setBusy(null); }
  };

  const ingest = async (id: string) => { setBusy(id); setError(null); try { const result = await customerSkillApi.ingest(id); setError(null); window.alert('Integritas sumber diverifikasi: ' + result.file_count + ' file, ' + result.total_bytes + ' bytes. Status eksekusi tetap nonaktif.'); await refresh(); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Source ingestion gagal. Pastikan repository, commit, path dan hash cocok dengan sumber pinned.'); } finally { setBusy(null); } };

  const install = async (id: string) => { setBusy(id); setError(null); try { await customerSkillApi.install(id); await refresh(); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Instalasi ditolak oleh gate registry.'); } finally { setBusy(null); } };

  const requestPermissions = async (skill: CustomerSkillPackage) => { setBusy(skill.id); setError(null); try { await customerSkillApi.requestPermissions(skill.id, skill.requested_permissions); await refresh(); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Permintaan permission gagal.'); } finally { setBusy(null); } };

  const revokePermissions = async (skill: CustomerSkillPackage) => { setBusy(skill.id); setError(null); try { await customerSkillApi.revokePermissions(skill.id); await refresh(); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Pencabutan permission gagal.'); } finally { setBusy(null); } };

  const importSkill = async (event: React.FormEvent) => {
    event.preventDefault(); setBusy('import'); setError(null);
    try {
      await customerSkillApi.import({
        ...form,
        manifest: { name: form.name, version: form.version, description: form.description },
      });
      setForm(emptyForm); setShowImport(false); await refresh();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Registrasi skill gagal.'); }
    finally { setBusy(null); }
  };

  const update = (key: keyof typeof emptyForm, value: string) => setForm(current => ({ ...current, [key]: value }));
  const togglePermission = (key: string) => setForm(current => ({
    ...current, requested_permissions: current.requested_permissions.includes(key)
      ? current.requested_permissions.filter(item => item !== key)
      : [...current.requested_permissions, key],
  }));

  return <div className="space-y-4 pb-20 animate-fadeIn">
    <div className="flex items-start justify-between gap-3">
      <div><h1 className="text-xl font-bold tracking-tight text-slate-900">AI Skills Library</h1>
        <p className="mt-1 text-xs text-slate-500">Registry terpusat untuk provenance, versi, lisensi, validasi, dan izin eksekusi Agent OpenManus.</p></div>
      <div className="flex gap-2">
        <button onClick={() => void refresh()} className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"><RefreshCw className="h-3.5 w-3.5"/>Muat ulang</button>
        <button onClick={() => void toggleCatalog()} className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"><Search className="h-3.5 w-3.5"/>Jelajahi pinned</button>
        <button onClick={() => setShowImport(value => !value)} className="inline-flex items-center gap-1.5 rounded-xl bg-red-600 px-3 py-2 text-xs font-semibold text-white hover:bg-red-700"><Plus className="h-3.5 w-3.5"/>Registrasi</button>
      </div>
    </div>
    <div className="rounded-2xl border border-blue-100 bg-blue-50/60 p-3 text-xs leading-relaxed text-blue-900">
      Import hanya menyimpan metadata dan provenance, bukan mengunduh atau menjalankan kode. Eksekusi tetap nonaktif sampai validasi isi, pemeriksaan lisensi, publikasi, dan persetujuan permission selesai.
    </div>
    {error && <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700"><AlertCircle className="mr-1 inline h-4 w-4"/>{error}</div>}
    {showCatalog && <section className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div><h2 className="text-sm font-bold text-slate-900">Pinned Visual, Scenario & Motion Skills</h2><p className="text-[10px] text-slate-500">Sumber commit tetap: 2 Visual Skills, 172 Scenario product skills, dan 56 Motion Skills dari 19 repository pack.</p></div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[10px] font-semibold text-slate-500">{catalogItems.filter(item => item.imported).length}/{catalogItems.length} terdaftar</span>
          <button type="button" disabled={busy !== null || catalogLoading || !catalogItems.some(item => item.source_repository.startsWith('iart-ai/'))}
            onClick={() => void ingestAllMotion()}
            className="rounded-xl bg-red-600 px-3 py-2 text-[10px] font-semibold text-white hover:bg-red-700 disabled:opacity-50">
            {busy === 'motion-bulk' ? 'Memproses Motion…' : 'Ingest 56 Motion Skills'}
          </button>
        </div>
      </div>
      <div className="relative">
        <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400"/>
        <input value={catalogSearch} onChange={event => setCatalogSearch(event.target.value)} placeholder="Cari skill, kategori, atau repository…" className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2 pl-9 pr-3 text-xs text-slate-800 outline-none focus:border-red-500"/>
      </div>
      <p className="rounded-xl border border-amber-100 bg-amber-50 p-3 text-[10px] leading-relaxed text-amber-900">
        Import hanya mengambil entrypoint SKILL.md dan menghitung hash sumber. Status lisensi tetap unverified, publikasi private, permission kosong, dan eksekusi nonaktif sampai recursive ingestion, SBOM, pemeriksaan hak aset/NOTICE, review manusia, dan approval selesai.
      </p>
      {bulkProgress && (
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-[10px] leading-relaxed text-slate-700">
          <div className="flex items-center justify-between gap-2 font-semibold">
            <span>{bulkProgress.current}</span>
            <span>{bulkProgress.completed}/{bulkProgress.total} · gagal {bulkProgress.failed}</span>
          </div>
          <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-200">
            <div className="h-full rounded-full bg-red-600 transition-all" style={{ width: (bulkProgress.completed / Math.max(1, bulkProgress.total) * 100) + '%' }} />
          </div>
          <p className="mt-2 text-slate-500">Batch hanya mengimpor, melakukan recursive ingestion dan validasi. Skill tidak otomatis dipublikasikan, di-install, diberi permission, atau dieksekusi.</p>
          {bulkProgress.failures.length > 0 && <ul className="mt-2 list-disc pl-4 text-amber-700">{bulkProgress.failures.map((failure,index) => <li key={index}>{failure}</li>)}</ul>}
        </div>
      )}
      {catalogLoading ? <div className="p-6 text-center text-xs text-slate-500">Memuat pinned source inventory…</div> : (
        <div className="max-h-[440px] space-y-2 overflow-y-auto pr-1">
          {catalogItems.filter(item => {
            const q = catalogSearch.trim().toLowerCase();
            return !q || [item.name,item.slug,item.source_repository,item.source_path].some(value => value.toLowerCase().includes(q));
          }).map(item => (
            <div key={item.source_repository + ':' + item.source_path} className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-slate-100 p-3">
              <div className="min-w-0 flex-1">
                <p className="text-xs font-semibold text-slate-900">{item.name}</p>
                <p className="mt-0.5 break-all text-[10px] text-slate-500">{item.source_repository} · {item.source_path}</p>
                <p className="mt-0.5 text-[10px] text-amber-700">{item.license_id} · review belum selesai · {item.source_commit.slice(0,12)}</p>
              </div>
              <button type="button" disabled={item.imported || busy !== null} onClick={() => void importPinned(item)}
                className="rounded-lg border border-slate-200 px-3 py-2 text-[10px] font-semibold text-slate-700 disabled:opacity-50">
                {item.imported ? 'Sudah terdaftar' : busy === item.source_path ? 'Mengimpor…' : 'Import private'}
              </button>
            </div>
          ))}
          {catalogItems.length > 0 && catalogItems.filter(item => {
            const q = catalogSearch.trim().toLowerCase();
            return !q || [item.name,item.slug,item.source_repository,item.source_path].some(value => value.toLowerCase().includes(q));
          }).length === 0 && <p className="p-4 text-center text-xs text-slate-500">Tidak ada skill yang cocok.</p>}
        </div>
      )}
    </section>}
    {showImport && <form onSubmit={importSkill} className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4">
      <div className="flex items-center justify-between"><h2 className="text-sm font-bold text-slate-900">Registrasi provenance skill</h2><button type="button" onClick={() => setShowImport(false)} className="rounded-lg p-1 text-slate-500"><X className="h-4 w-4"/></button></div>
      <p className="text-[11px] text-slate-500">Masukkan referensi commit dan hash yang sudah diperoleh dari proses source review. Jangan mengisi hash perkiraan.</p>
      <div className="grid gap-2 sm:grid-cols-2">
        {([
          ['slug','Slug unik'],['name','Nama skill'],['source_repository','Repository (owner/name)'],['source_ref','Ref/tag'],['source_commit','Commit SHA-1 (40 karakter)'],['source_path','Path entrypoint'],['source_blob_sha','Git blob SHA (40 karakter)'],['content_sha256','SHA-256 konten (64 karakter)'],['version','Versi'],['license_id','SPDX / License ID'],['license_url','URL lisensi'],
        ] as const).map(([key,label]) => <label key={key} className="space-y-1"><span className="text-[10px] font-semibold text-slate-600">{label}</span><input required value={form[key]} onChange={event => update(key,event.target.value)} className="w-full rounded-xl border border-slate-200 px-3 py-2 text-xs text-slate-800 outline-none focus:border-red-500"/></label>)}
      </div>
      <label className="block space-y-1"><span className="text-[10px] font-semibold text-slate-600">Deskripsi</span><textarea value={form.description} onChange={event => update('description',event.target.value)} rows={2} className="w-full rounded-xl border border-slate-200 px-3 py-2 text-xs"/></label>
      <label className="block space-y-1"><span className="text-[10px] font-semibold text-slate-600">Bukti lisensi / attribution note</span><textarea required value={form.license_evidence} onChange={event => update('license_evidence',event.target.value)} rows={2} placeholder="Sertakan lokasi LICENSE/NOTICE dan kewajiban atribusi yang telah diperiksa." className="w-full rounded-xl border border-slate-200 px-3 py-2 text-xs"/></label>
      <div><p className="mb-2 text-[10px] font-semibold text-slate-600">Permission yang diminta (tidak otomatis diberikan)</p><div className="grid grid-cols-2 gap-2 sm:grid-cols-3">{permissionOptions.map(key => <label key={key} className="flex items-center gap-2 text-[10px] text-slate-600"><input type="checkbox" checked={form.requested_permissions.includes(key)} onChange={() => togglePermission(key)} className="accent-red-600"/>{key}</label>)}</div></div>
      <button disabled={busy === 'import'} className="rounded-xl bg-red-600 px-4 py-2.5 text-xs font-semibold text-white disabled:opacity-50">{busy === 'import' ? 'Menyimpan…' : 'Simpan provenance'}</button>
    </form>}
    {loading ? <div className="rounded-2xl border border-slate-100 bg-white p-8 text-center text-xs text-slate-500">Memuat Skill Registry…</div>
      : items.length === 0 ? <div className="rounded-2xl border border-slate-100 bg-white p-8 text-center"><PackagePlus className="mx-auto mb-2 h-7 w-7 text-slate-400"/><p className="text-sm font-semibold text-slate-800">Belum ada skill terdaftar</p><p className="mt-1 text-xs text-slate-500">Gunakan Registrasi setelah source review dan hash file tersedia.</p></div>
      : <div className="grid gap-3 lg:grid-cols-2">{items.map(skill => <article key={skill.id} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-2xs">
        <div className="flex items-start justify-between gap-2"><div><h2 className="text-sm font-bold text-slate-900">{skill.name}</h2><p className="mt-0.5 text-[11px] text-slate-500">{skill.slug} · v{skill.version}</p></div>
          <span className="rounded-full border border-amber-200 bg-amber-50 px-2 py-1 text-[10px] font-semibold text-amber-800">{skill.validation_status.replace('_',' ')}</span></div>
        <p className="mt-2 text-xs leading-relaxed text-slate-600">{skill.description || 'Tidak ada deskripsi.'}</p>
        <div className="mt-3 space-y-1 rounded-xl bg-slate-50 p-3 text-[10px] text-slate-600">
          <p><b>Sumber:</b> {skill.source_repository} · {skill.source_ref}</p><p><b>Commit:</b> <span className="font-mono">{skill.source_commit.slice(0,12)}</span></p>
          <p><b>Lisensi:</b> {skill.license_id} · {skill.license_status}</p><p><b>SHA-256:</b> <span className="font-mono">{skill.content_sha256.slice(0,16)}…</span></p>
          <p><b>Publikasi:</b> {skill.publication_status} · <b>Install:</b> {skill.installation?.status || 'belum'}</p>
          {skill.installation && <p><b>Permission:</b> {skill.installation.permission_status} · <b>Eksekusi server:</b> {skill.installation.execution_enabled ? 'diizinkan' : 'dinonaktifkan'}</p>}
          {skill.installation?.permission_request?.length ? <p><b>Diminta:</b> {skill.installation.permission_request.join(', ')}</p> : null}
          {skill.requested_permissions.length > 0 && <p><b>Manifest meminta:</b> {skill.requested_permissions.join(', ')}</p>}
        </div>
        {skill.validation_report?.source_inventory && <details className="mt-3 rounded-xl border border-slate-200 bg-white p-3">
          <summary className="cursor-pointer text-[11px] font-semibold text-slate-700">Bukti dependency & provenance</summary>
          <div className="mt-2 grid grid-cols-2 gap-2 text-[10px] text-slate-600 sm:grid-cols-4">
            <p><b className="block text-slate-800">{skill.validation_report.source_inventory.dependency_count ?? 0}</b>Package records</p>
            <p><b className="block text-slate-800">{skill.validation_report.source_inventory.dependency_edge_count ?? 0}</b>Dependency edges</p>
            <p><b className="block text-slate-800">{skill.validation_report.source_inventory.exact_version_count ?? 0}</b>Exact versions</p>
            <p><b className="block text-slate-800">{skill.validation_report.source_inventory.unresolved_dependency_count ?? 0}</b>Unresolved</p>
          </div>
          <div className="mt-2 space-y-1 text-[10px] text-slate-600">
            <p>Registry metadata: {skill.validation_report.source_inventory.registry_resolution?.registry_metadata_resolved_count ?? 0}/{skill.validation_report.source_inventory.registry_resolution?.exact_version_count ?? 0} resolved · {skill.validation_report.source_inventory.registry_resolution?.unresolved_count ?? 0} unresolved</p>
            <p className={skill.validation_report.source_inventory.dependency_graph_complete ? 'font-semibold text-emerald-700' : 'font-semibold text-amber-700'}>Graph: {skill.validation_report.source_inventory.dependency_graph_complete ? 'lengkap menurut parser' : 'belum lengkap · publikasi tetap diblokir'} · {skill.validation_report.source_inventory.unresolved_dependency_edge_count ?? 0} edge belum terpetakan</p>
            {(skill.validation_report.source_inventory.dependency_graph_blocking_manifests ?? []).map(path => <p key={path} className="break-all text-amber-700">Butuh resolusi graph: {path}</p>)}
            {(skill.validation_report.source_inventory.dependency_edges ?? []).slice(0, 8).map((edge, index) => <p key={index} className="break-all rounded-lg bg-slate-50 px-2 py-1 font-mono">{edge.from}{edge.from_version ? '@' + edge.from_version : ''} → {edge.to}{edge.to_version ? '@' + edge.to_version : ''} <span className="text-slate-400">({edge.kind || 'dependency'}{edge.resolution_status ? ' · ' + edge.resolution_status : ''})</span></p>)}
            {(skill.validation_report.findings ?? []).map((finding, index) => <p key={'finding-' + index} className="text-amber-700">• {finding}</p>)}
          </div>
          <p className="mt-2 text-[9px] leading-relaxed text-slate-400">Graph merupakan bukti hasil parsing statis. Kelengkapan transitive closure, resolusi sumber, kompatibilitas lisensi, dan keamanan eksekusi tetap memerlukan review.</p>
        </details>}
        <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
          <span className="inline-flex items-center gap-1 text-[10px] text-slate-500"><LockKeyhole className="h-3 w-3"/>{skill.installation?.execution_enabled ? 'Eksekusi diizinkan oleh server' : skill.installation?.permission_status === 'approved' ? 'Permission disetujui · gate eksekusi masih tertutup' : 'Eksekusi dinonaktifkan oleh server'}</span>
          <div className="flex flex-wrap gap-2">{skill.validation_status === 'pending' && <button disabled={busy === skill.id} onClick={() => void ingest(skill.id)} className="rounded-xl border border-slate-200 px-3 py-2 text-[11px] font-semibold text-slate-700 disabled:opacity-50">Ambil sumber & verifikasi</button>}<button disabled={busy === skill.id} onClick={() => void validate(skill.id)} className="inline-flex items-center gap-1.5 rounded-xl bg-red-600 px-3 py-2 text-[11px] font-semibold text-white hover:bg-red-700 disabled:opacity-50"><ShieldCheck className="h-3.5 w-3.5"/>{busy === skill.id ? 'Memproses…' : 'Validasi metadata'}</button>{skill.publication_status === 'published' && !skill.installation && <button disabled={busy === skill.id} onClick={() => void install(skill.id)} className="rounded-xl border border-slate-200 px-3 py-2 text-[11px] font-semibold text-slate-700 disabled:opacity-50">Install</button>}{skill.installation && skill.installation.permission_status !== 'pending_review' && skill.installation.permission_status !== 'approved' && <button disabled={busy === skill.id || skill.requested_permissions.length === 0} onClick={() => void requestPermissions(skill)} className="rounded-xl border border-slate-200 px-3 py-2 text-[11px] font-semibold text-slate-700 disabled:opacity-50">Ajukan permission</button>}{skill.installation && skill.installation.permission_status !== 'revoked' && <button disabled={busy === skill.id} onClick={() => void revokePermissions(skill)} className="rounded-xl border border-rose-200 px-3 py-2 text-[11px] font-semibold text-rose-700 disabled:opacity-50">Cabut permission</button>}</div>
        </div>
      </article>)}</div>}
    <p className="text-[10px] text-slate-400">Validasi ini hanya metadata. Pemindaian file, dependency/SBOM, hak cipta, sandbox compatibility, dan persetujuan keamanan belum dilakukan oleh endpoint ini.</p>
  </div>;
}
