'use client';

import React, { useEffect, useState } from 'react';
import { ShieldCheck, PackagePlus, RefreshCw, LockKeyhole, AlertCircle, Plus, X } from 'lucide-react';
import { customerSkillApi, type CustomerSkillPackage } from '@/lib/api/client';

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

  const refresh = async () => {
    setLoading(true); setError(null);
    try { setItems((await customerSkillApi.list()).items); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Skill Registry tidak dapat dimuat.'); }
    finally { setLoading(false); }
  };
  useEffect(() => { void refresh(); }, []);

  const validate = async (id: string) => {
    setBusy(id); setError(null);
    try { await customerSkillApi.validate(id); await refresh(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Validasi metadata gagal.'); }
    finally { setBusy(null); }
  };

  const ingest = async (id: string) => { setBusy(id); setError(null); try { const result = await customerSkillApi.ingest(id); setError(null); window.alert('Integritas sumber diverifikasi: ' + result.file_count + ' file, ' + result.total_bytes + ' bytes. Status eksekusi tetap nonaktif.'); await refresh(); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Source ingestion gagal. Pastikan repository, commit, path dan hash cocok dengan sumber pinned.'); } finally { setBusy(null); } };

  const install = async (id: string) => { setBusy(id); setError(null); try { await customerSkillApi.install(id); await refresh(); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Instalasi ditolak oleh gate registry.'); } finally { setBusy(null); } };

  const requestPermissions = async (skill: CustomerSkillPackage) => { setBusy(skill.id); setError(null); try { await customerSkillApi.requestPermissions(skill.id, skill.requested_permissions); await refresh(); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Permintaan permission gagal.'); } finally { setBusy(null); } };

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
        <button onClick={() => setShowImport(value => !value)} className="inline-flex items-center gap-1.5 rounded-xl bg-red-600 px-3 py-2 text-xs font-semibold text-white hover:bg-red-700"><Plus className="h-3.5 w-3.5"/>Registrasi</button>
      </div>
    </div>
    <div className="rounded-2xl border border-blue-100 bg-blue-50/60 p-3 text-xs leading-relaxed text-blue-900">
      Import hanya menyimpan metadata dan provenance, bukan mengunduh atau menjalankan kode. Eksekusi tetap nonaktif sampai validasi isi, pemeriksaan lisensi, publikasi, dan persetujuan permission selesai.
    </div>
    {error && <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700"><AlertCircle className="mr-1 inline h-4 w-4"/>{error}</div>}
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
        <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
          <span className="inline-flex items-center gap-1 text-[10px] text-slate-500"><LockKeyhole className="h-3 w-3"/>{skill.installation?.execution_enabled ? 'Eksekusi diizinkan oleh server' : skill.installation?.permission_status === 'approved' ? 'Permission disetujui · gate eksekusi masih tertutup' : 'Eksekusi dinonaktifkan oleh server'}</span>
          <div className="flex flex-wrap gap-2">{skill.validation_status === 'pending' && <button disabled={busy === skill.id} onClick={() => void ingest(skill.id)} className="rounded-xl border border-slate-200 px-3 py-2 text-[11px] font-semibold text-slate-700 disabled:opacity-50">Ambil sumber & verifikasi</button>}<button disabled={busy === skill.id} onClick={() => void validate(skill.id)} className="inline-flex items-center gap-1.5 rounded-xl bg-red-600 px-3 py-2 text-[11px] font-semibold text-white hover:bg-red-700 disabled:opacity-50"><ShieldCheck className="h-3.5 w-3.5"/>{busy === skill.id ? 'Memproses…' : 'Validasi metadata'}</button>{skill.publication_status === 'published' && !skill.installation && <button disabled={busy === skill.id} onClick={() => void install(skill.id)} className="rounded-xl border border-slate-200 px-3 py-2 text-[11px] font-semibold text-slate-700 disabled:opacity-50">Install</button>}{skill.installation && skill.installation.permission_status !== 'pending_review' && skill.installation.permission_status !== 'approved' && <button disabled={busy === skill.id || skill.requested_permissions.length === 0} onClick={() => void requestPermissions(skill)} className="rounded-xl border border-slate-200 px-3 py-2 text-[11px] font-semibold text-slate-700 disabled:opacity-50">Ajukan permission</button>}</div>
        </div>
      </article>)}</div>}
    <p className="text-[10px] text-slate-400">Validasi ini hanya metadata. Pemindaian file, dependency/SBOM, hak cipta, sandbox compatibility, dan persetujuan keamanan belum dilakukan oleh endpoint ini.</p>
  </div>;
}
