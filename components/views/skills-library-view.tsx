'use client';

import React, { useEffect, useState } from 'react';
import { ShieldCheck, PackagePlus, RefreshCw, LockKeyhole, AlertCircle } from 'lucide-react';
import { customerApi, type CustomerSkillPackage } from '@/lib/api/client';

export function SkillsLibraryView() {
  const [items, setItems] = useState<CustomerSkillPackage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const refresh = async () => {
    setLoading(true); setError(null);
    try { setItems((await customerApi.skills()).items); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Skill Registry tidak dapat dimuat.'); }
    finally { setLoading(false); }
  };
  useEffect(() => { void refresh(); }, []);

  const validate = async (id: string) => {
    setBusy(id); setError(null);
    try { await customerApi.validateSkill(id); await refresh(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Validasi metadata gagal.'); }
    finally { setBusy(null); }
  };

  return <div className="space-y-4 pb-20 animate-fadeIn">
    <div className="flex items-start justify-between gap-3">
      <div><h1 className="text-xl font-bold tracking-tight text-slate-900">AI Skills Library</h1>
        <p className="mt-1 text-xs text-slate-500">Registry terpusat untuk provenance, versi, lisensi, validasi, dan izin eksekusi Agent OpenManus.</p></div>
      <button onClick={() => void refresh()} className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"><RefreshCw className="h-3.5 w-3.5"/>Muat ulang</button>
    </div>
    <div className="rounded-2xl border border-blue-100 bg-blue-50/60 p-3 text-xs leading-relaxed text-blue-900">
      Skill yang diimpor tidak otomatis dijalankan. Eksekusi tetap nonaktif sampai validasi, pemeriksaan lisensi, publikasi, dan persetujuan permission selesai.
    </div>
    {error && <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700"><AlertCircle className="mr-1 inline h-4 w-4"/>{error}</div>}
    {loading ? <div className="rounded-2xl border border-slate-100 bg-white p-8 text-center text-xs text-slate-500">Memuat Skill Registry…</div>
      : items.length === 0 ? <div className="rounded-2xl border border-slate-100 bg-white p-8 text-center"><PackagePlus className="mx-auto mb-2 h-7 w-7 text-slate-400"/><p className="text-sm font-semibold text-slate-800">Belum ada skill terdaftar</p><p className="mt-1 text-xs text-slate-500">Import skill dilakukan melalui proses kurasi sumber dan metadata provenance yang telah ditinjau.</p></div>
      : <div className="grid gap-3 lg:grid-cols-2">{items.map(skill => <article key={skill.id} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-2xs">
        <div className="flex items-start justify-between gap-2"><div><h2 className="text-sm font-bold text-slate-900">{skill.name}</h2><p className="mt-0.5 text-[11px] text-slate-500">{skill.slug} · v{skill.version}</p></div>
          <span className="rounded-full border border-amber-200 bg-amber-50 px-2 py-1 text-[10px] font-semibold text-amber-800">{skill.validation_status.replace('_',' ')}</span></div>
        <p className="mt-2 text-xs leading-relaxed text-slate-600">{skill.description || 'Tidak ada deskripsi.'}</p>
        <div className="mt-3 space-y-1 rounded-xl bg-slate-50 p-3 text-[10px] text-slate-600">
          <p><b>Sumber:</b> {skill.source_repository} · {skill.source_ref}</p><p><b>Commit:</b> <span className="font-mono">{skill.source_commit.slice(0,12)}</span></p>
          <p><b>Lisensi:</b> {skill.license_id} · {skill.license_status}</p><p><b>SHA-256:</b> <span className="font-mono">{skill.content_sha256.slice(0,16)}…</span></p>
        </div>
        <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
          <span className="inline-flex items-center gap-1 text-[10px] text-slate-500"><LockKeyhole className="h-3 w-3"/>Eksekusi: nonaktif</span>
          <button disabled={busy === skill.id} onClick={() => void validate(skill.id)} className="inline-flex items-center gap-1.5 rounded-xl bg-red-600 px-3 py-2 text-[11px] font-semibold text-white hover:bg-red-700 disabled:opacity-50"><ShieldCheck className="h-3.5 w-3.5"/>{busy === skill.id ? 'Memproses…' : 'Validasi metadata'}</button>
        </div>
      </article>)}</div>}
    <p className="text-[10px] text-slate-400">Validasi di layar ini hanya memeriksa metadata. Pemindaian file, dependency/SBOM, hak cipta, dan persetujuan keamanan harus dilakukan sebelum publikasi.</p>
  </div>;
}
