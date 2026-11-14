'use client';

import React, { useEffect, useState } from 'react';
import { Brain, Plus, Pencil, Trash2, Save, X, ShieldCheck, ShieldOff } from 'lucide-react';
import { customerApi, CustomerPersonalMemoryItem, CustomerPersonalMemoryState } from '@/lib/api/client';
import { useToast } from '@/components/ui/toast-context';

const retentionOptions = [30, 90, 180, 365] as const;
type RetentionDays = typeof retentionOptions[number];

export const PersonalMemorySettings: React.FC = () => {
  const { showToast } = useToast();
  const [state, setState] = useState<CustomerPersonalMemoryState | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [retentionDays, setRetentionDays] = useState<RetentionDays>(90);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');
  const [editRetention, setEditRetention] = useState<RetentionDays>(90);

  useEffect(() => {
    let active = true;
    customerApi.personalMemory()
      .then((next) => { if (active) setState(next); })
      .catch((error) => { if (active) showToast(error instanceof Error ? error.message : 'Pengaturan Memory tidak dapat dimuat.', 'error'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [showToast]);

  const toggleConsent = async () => {
    if (!state || saving) return;
    setSaving(true);
    try {
      const updated = await customerApi.setPersonalMemoryConsent(!state.enabled);
      setState((current) => current ? { ...current, ...updated } : current);
      showToast(updated.enabled ? 'Personal Memory diaktifkan dengan persetujuan Anda.' : 'Personal Memory dinonaktifkan. Data tersimpan tidak akan digunakan.', 'success');
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Persetujuan Memory gagal diperbarui.', 'error');
    } finally { setSaving(false); }
  };

  const addMemory = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!title.trim() || !content.trim() || saving) return;
    setSaving(true);
    try {
      const created = await customerApi.createPersonalMemory({ title: title.trim(), content: content.trim(), retention_days: retentionDays });
      setState((current) => current ? { ...current, items: [created, ...current.items] } : current);
      setTitle(''); setContent('');
      showToast('Memory pribadi berhasil disimpan.', 'success');
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Memory gagal disimpan.', 'error');
    } finally { setSaving(false); }
  };

  const beginEdit = (item: CustomerPersonalMemoryItem) => {
    const remaining = Math.max(1, Math.ceil((new Date(item.expires_at).getTime() - Date.now()) / 86400000));
    const nearest = retentionOptions.find((value) => value >= remaining) || 365;
    setEditingId(item.id); setEditTitle(item.title); setEditContent(item.content); setEditRetention(nearest);
  };

  const saveEdit = async (memoryId: string) => {
    if (!editTitle.trim() || !editContent.trim() || saving) return;
    setSaving(true);
    try {
      const updated = await customerApi.updatePersonalMemory(memoryId, {
        title: editTitle.trim(), content: editContent.trim(), retention_days: editRetention,
      });
      setState((current) => current ? { ...current, items: current.items.map((item) => item.id === memoryId ? updated : item) } : current);
      setEditingId(null);
      showToast('Memory berhasil diperbarui.', 'success');
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Memory gagal diperbarui.', 'error');
    } finally { setSaving(false); }
  };

  const removeMemory = async (memoryId: string) => {
    if (saving || !window.confirm('Hapus Memory ini secara permanen?')) return;
    setSaving(true);
    try {
      await customerApi.deletePersonalMemory(memoryId);
      setState((current) => current ? { ...current, items: current.items.filter((item) => item.id !== memoryId) } : current);
      showToast('Memory berhasil dihapus.', 'success');
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Memory gagal dihapus.', 'error');
    } finally { setSaving(false); }
  };

  const clearAllMemory = async () => {
    if (saving || !state || !window.confirm('Hapus seluruh Personal Memory secara permanen dan nonaktifkan penggunaannya?')) return;
    setSaving(true);
    try {
      await customerApi.clearPersonalMemory();
      setState((current) => current ? { ...current, enabled: false, disabled_at: new Date().toISOString(), items: [] } : current);
      setEditingId(null);
      showToast('Seluruh Personal Memory berhasil dihapus.', 'success');
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Penghapusan seluruh Memory gagal.', 'error');
    } finally { setSaving(false); }
  };

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-4 sm:p-5 shadow-xs space-y-4">
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-2xl bg-red-50 text-red-600 flex items-center justify-center shrink-0">
          <Brain className="w-5 h-5" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-bold text-slate-900">Personal Memory</h3>
          <p className="text-[11px] leading-relaxed text-slate-500 mt-1">
            Catatan yang Anda buat sendiri dan dapat ditinjau, dikoreksi, atau dihapus. Riwayat percakapan disimpan terpisah.
          </p>
        </div>
        {state && (
          <span className={`text-[10px] font-bold px-2 py-1 rounded-full ${state.enabled ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>
            {state.enabled ? 'Aktif' : 'Nonaktif'}
          </span>
        )}
      </div>

      {loading ? (
        <p className="text-xs text-slate-500">Memuat pengaturan Memory…</p>
      ) : !state ? (
        <p className="text-xs text-rose-600">Pengaturan Memory tidak tersedia. Coba muat ulang halaman.</p>
      ) : (
        <>
          <div className="rounded-2xl border border-slate-100 bg-slate-50 p-3 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 min-w-0">
              {state.enabled ? <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" /> : <ShieldOff className="w-4 h-4 text-slate-400 shrink-0" />}
              <div>
                <p className="text-xs font-semibold text-slate-800">Izinkan penggunaan Personal Memory</p>
                <p className="text-[10px] text-slate-500">Nonaktif berarti catatan tidak dimuat ke konteks pada eksekusi berikutnya.</p>
              </div>
            </div>
            <button type="button" onClick={() => void toggleConsent()} disabled={saving}
              aria-pressed={state.enabled} aria-label="Ubah persetujuan Personal Memory"
              className={`w-11 h-6 rounded-full p-0.5 transition-colors shrink-0 disabled:opacity-50 ${state.enabled ? 'bg-red-600' : 'bg-slate-300'}`}>
              <span className={`block w-5 h-5 rounded-full bg-white shadow-xs transition-transform ${state.enabled ? 'translate-x-5' : 'translate-x-0'}`} />
            </button>
          </div>

          <>
            {state.enabled && (
              <form onSubmit={(event) => void addMemory(event)} className="space-y-2.5">
                <p className="text-xs font-bold text-slate-800">Tambah catatan pribadi</p>
                <input value={title} onChange={(event) => setTitle(event.target.value)} maxLength={120} required
                  placeholder="Judul Memory" className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-xs text-slate-800 outline-none focus:border-red-500 focus:ring-2 focus:ring-red-500/10" />
                <textarea value={content} onChange={(event) => setContent(event.target.value)} maxLength={4000} required rows={3}
                  placeholder="Tulis informasi yang ingin Anda simpan…" className="w-full resize-y rounded-xl border border-slate-200 px-3 py-2.5 text-xs text-slate-800 outline-none focus:border-red-500 focus:ring-2 focus:ring-red-500/10" />
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <label className="text-[11px] text-slate-600 flex items-center gap-2">
                    Retensi
                    <select value={retentionDays} onChange={(event) => setRetentionDays(Number(event.target.value) as RetentionDays)} className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs">
                      {retentionOptions.map((days) => <option key={days} value={days}>{days} hari</option>)}
                    </select>
                  </label>
                  <button type="submit" disabled={saving || !title.trim() || !content.trim()} className="inline-flex items-center gap-1.5 rounded-xl bg-red-600 px-3 py-2 text-[11px] font-bold text-white disabled:opacity-50">
                    <Plus className="w-3.5 h-3.5" /> {saving ? 'Menyimpan…' : 'Simpan Memory'}
                  </button>
                </div>
              </form>
            )}
            {!state.enabled && <p className="text-[11px] text-slate-500">Memory dinonaktifkan untuk konteks AI. Catatan tetap dapat ditinjau, dikoreksi, atau dihapus.</p>}
            <div className="border-t border-slate-100 pt-3 space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-bold text-slate-800">Memory tersimpan</p>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-slate-500">{state.items.length} catatan</span>
                    {state.items.length > 0 && (
                      <button type="button" onClick={() => void clearAllMemory()} disabled={saving}
                        className="text-[10px] font-semibold text-rose-600 hover:text-rose-700 disabled:opacity-50">
                        Hapus semua
                      </button>
                    )}
                  </div>
                </div>
                {state.items.length === 0 ? (
                  <p className="text-[11px] text-slate-500 rounded-xl bg-slate-50 p-3">Belum ada catatan pribadi.</p>
                ) : state.items.map((item) => (
                  <div key={item.id} className="rounded-xl border border-slate-100 p-3 space-y-2">
                    {editingId === item.id ? (
                      <>
                        <input value={editTitle} onChange={(event) => setEditTitle(event.target.value)} maxLength={120} className="w-full rounded-lg border border-slate-200 px-2.5 py-2 text-xs text-slate-800" />
                        <textarea value={editContent} onChange={(event) => setEditContent(event.target.value)} maxLength={4000} rows={3} className="w-full rounded-lg border border-slate-200 px-2.5 py-2 text-xs text-slate-800" />
                        <div className="flex items-center justify-between gap-2">
                          <select value={editRetention} onChange={(event) => setEditRetention(Number(event.target.value) as RetentionDays)} className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs">
                            {retentionOptions.map((days) => <option key={days} value={days}>{days} hari</option>)}
                          </select>
                          <div className="flex gap-2">
                            <button type="button" onClick={() => setEditingId(null)} className="rounded-lg border border-slate-200 p-2 text-slate-600" aria-label="Batal edit"><X className="w-3.5 h-3.5" /></button>
                            <button type="button" onClick={() => void saveEdit(item.id)} disabled={saving || !editTitle.trim() || !editContent.trim()} className="rounded-lg bg-red-600 p-2 text-white disabled:opacity-50" aria-label="Simpan edit"><Save className="w-3.5 h-3.5" /></button>
                          </div>
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="flex items-start justify-between gap-2">
                          <p className="text-xs font-semibold text-slate-900 break-words">{item.title}</p>
                          <div className="flex gap-1 shrink-0">
                            <button type="button" onClick={() => beginEdit(item)} disabled={saving} className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100" aria-label="Edit Memory"><Pencil className="w-3.5 h-3.5" /></button>
                            <button type="button" onClick={() => void removeMemory(item.id)} disabled={saving} className="rounded-lg p-1.5 text-rose-600 hover:bg-rose-50" aria-label="Hapus Memory"><Trash2 className="w-3.5 h-3.5" /></button>
                          </div>
                        </div>
                        <p className="text-[11px] leading-relaxed text-slate-600 whitespace-pre-wrap break-words">{item.content}</p>
                        <p className="text-[10px] text-slate-400">Berakhir {new Date(item.expires_at).toLocaleDateString('id-ID')}</p>
                      </>
                    )}
                  </div>
                ))}
            </div>
          <p className="text-[10px] leading-relaxed text-slate-400">
            Catatan dibuat secara manual. MoreAI tidak otomatis menyimpan isi chat atau file sebagai Personal Memory. Perubahan consent/penghapusan berlaku untuk eksekusi berikutnya; run aktif mungkin telah memuat konteks sebelumnya.
          </p>
        </>
      )}
    </section>
  );
};
