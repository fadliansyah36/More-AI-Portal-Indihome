'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { ArrowLeft, Megaphone, Plus, RefreshCw, X, CalendarDays } from 'lucide-react';
import { useToast } from '@/components/ui/toast-context';
import { partnerApi, PartnerCampaign } from '@/lib/api/client';

interface PartnerPromoViewProps {
  onBack: () => void;
}

export const PartnerPromoView: React.FC<PartnerPromoViewProps> = ({ onBack }) => {
  const { showToast } = useToast();
  const [campaigns, setCampaigns] = useState<PartnerCampaign[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [locationId, setLocationId] = useState('');
  const [startsAt, setStartsAt] = useState('');
  const [endsAt, setEndsAt] = useState('');
  const [budget, setBudget] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setCampaigns(await partnerApi.campaigns() as PartnerCampaign[]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Kampanye tidak dapat dimuat.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const create = async () => {
    if (name.trim().length < 2) {
      showToast('Nama kampanye minimal 2 karakter.', 'error');
      return;
    }
    if (startsAt && endsAt && new Date(endsAt) <= new Date(startsAt)) {
      showToast('Waktu berakhir harus setelah waktu mulai.', 'error');
      return;
    }
    const parsedBudget = budget.trim() ? Number(budget) : null;
    if (parsedBudget !== null && (!Number.isFinite(parsedBudget) || parsedBudget < 0)) {
      showToast('Anggaran harus berupa angka nol atau lebih.', 'error');
      return;
    }
    setSaving(true);
    try {
      await partnerApi.createCampaign({
        name: name.trim(),
        location_id: locationId.trim() || null,
        starts_at: startsAt ? new Date(startsAt).toISOString() : null,
        ends_at: endsAt ? new Date(endsAt).toISOString() : null,
        budget: parsedBudget,
      });
      setName('');
      setLocationId('');
      setStartsAt('');
      setEndsAt('');
      setBudget('');
      setShowCreate(false);
      await load();
      showToast('Kampanye tersimpan sebagai draft.', 'success');
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Kampanye gagal dibuat.', 'error');
    } finally {
      setSaving(false);
    }
  };

  const changeStatus = async (campaign: PartnerCampaign, status: PartnerCampaign['status']) => {
    try {
      await partnerApi.updateCampaign(campaign.id, { status });
      await load();
      showToast('Status kampanye diperbarui.', 'success');
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Status kampanye gagal diperbarui.', 'error');
    }
  };

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <button onClick={onBack} className="p-1 rounded-lg text-slate-400 hover:text-slate-700" aria-label="Kembali"><ArrowLeft className="w-5 h-5" /></button>
        <div className="text-center"><h1 className="text-base font-bold text-slate-900 leading-tight">Promo &amp; Kampanye Partner</h1><span className="text-[10px] text-slate-500 font-medium">Data kampanye dari tenant aktif</span></div>
        <button onClick={() => void load()} disabled={loading} className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 disabled:opacity-50" aria-label="Segarkan"><RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /></button>
      </div>

      <div className="rounded-3xl bg-gradient-to-r from-red-600 to-rose-600 p-4 text-white shadow-xs">
        <div className="flex items-center gap-2"><Megaphone className="h-5 w-5" /><h3 className="text-sm font-bold">Kelola kampanye lokasi</h3></div>
        <p className="mt-1 text-xs text-red-100">Kampanye disimpan di tenant partner dan dibatasi berdasarkan role serta cakupan lokasi.</p>
        <button onClick={() => setShowCreate(true)} className="mt-3 inline-flex items-center gap-2 rounded-xl bg-white px-3 py-2 text-xs font-bold text-red-700 hover:bg-red-50"><Plus className="h-4 w-4" /> Buat kampanye</button>
      </div>

      {error && <div role="alert" className="rounded-2xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">{error}</div>}
      {loading && <p className="py-8 text-center text-xs text-slate-500">Memuat kampanye…</p>}
      {!loading && !error && campaigns.length === 0 && <div className="rounded-3xl border border-slate-100 bg-white p-6 text-center"><Megaphone className="mx-auto h-8 w-8 text-slate-300" /><p className="mt-2 text-sm font-semibold text-slate-700">Belum ada kampanye</p><p className="mt-1 text-xs text-slate-500">Buat kampanye untuk mulai mengelola promosi tenant.</p></div>}

      <div className="space-y-3">
        {campaigns.map((campaign) => (
          <article key={campaign.id} className="space-y-3 rounded-3xl border border-slate-100 bg-white p-4 shadow-xs">
            <div className="flex items-start justify-between gap-3"><div className="min-w-0"><h4 className="text-sm font-bold text-slate-900">{campaign.name}</h4><p className="mt-1 break-all font-mono text-[10px] text-slate-400">{campaign.id}</p></div><span className="shrink-0 rounded-full bg-slate-100 px-2.5 py-1 text-[10px] font-bold text-slate-700">{campaign.status}</span></div>
            <div className="grid grid-cols-2 gap-2 border-t border-slate-100 pt-3 text-xs">
              <div><span className="block text-[10px] text-slate-400">Mulai</span><strong className="text-slate-700">{campaign.starts_at ? new Date(campaign.starts_at).toLocaleString('id-ID') : 'Belum ditentukan'}</strong></div>
              <div><span className="block text-[10px] text-slate-400">Berakhir</span><strong className="text-slate-700">{campaign.ends_at ? new Date(campaign.ends_at).toLocaleString('id-ID') : 'Belum ditentukan'}</strong></div>
            </div>
            {campaign.budget !== null && <p className="text-xs text-slate-600">Anggaran tercatat: {Number(campaign.budget).toLocaleString('id-ID')}</p>}
            <div className="flex flex-wrap gap-2 border-t border-slate-100 pt-2">
              {campaign.status !== 'active' && <button onClick={() => void changeStatus(campaign, 'active')} className="rounded-lg bg-emerald-50 px-3 py-1.5 text-[11px] font-semibold text-emerald-700">Aktifkan</button>}
              {campaign.status === 'active' && <button onClick={() => void changeStatus(campaign, 'paused')} className="rounded-lg bg-amber-50 px-3 py-1.5 text-[11px] font-semibold text-amber-700">Jeda kampanye</button>}
              {campaign.status === 'paused' && <button onClick={() => void changeStatus(campaign, 'active')} className="rounded-lg bg-emerald-50 px-3 py-1.5 text-[11px] font-semibold text-emerald-700">Lanjutkan</button>}
            </div>
          </article>
        ))}
      </div>

      {showCreate && <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"><div className="w-full max-w-sm space-y-3 rounded-3xl border border-slate-100 bg-white p-5 shadow-2xl">
        <div className="flex items-center justify-between"><h3 className="text-sm font-bold text-slate-900">Buat kampanye</h3><button onClick={() => setShowCreate(false)} aria-label="Tutup"><X className="h-4 w-4 text-slate-400" /></button></div>
        <label className="block space-y-1 text-xs"><span className="font-semibold text-slate-700">Nama kampanye</span><input value={name} onChange={(e) => setName(e.target.value)} maxLength={180} className="w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5" placeholder="Nama promosi" /></label>
        <label className="block space-y-1 text-xs"><span className="font-semibold text-slate-700">Location ID (opsional)</span><input value={locationId} onChange={(e) => setLocationId(e.target.value)} className="w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5 font-mono text-[11px]" placeholder="UUID lokasi tenant" /></label>
        <label className="block space-y-1 text-xs"><span className="font-semibold text-slate-700">Mulai (opsional)</span><input type="datetime-local" value={startsAt} onChange={(e) => setStartsAt(e.target.value)} className="w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5" /></label>
        <label className="block space-y-1 text-xs"><span className="font-semibold text-slate-700">Berakhir (opsional)</span><input type="datetime-local" value={endsAt} onChange={(e) => setEndsAt(e.target.value)} className="w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5" /></label>
        <label className="block space-y-1 text-xs"><span className="font-semibold text-slate-700">Anggaran (opsional)</span><input type="number" min="0" value={budget} onChange={(e) => setBudget(e.target.value)} className="w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5" /></label>
        <p className="text-[10px] text-slate-500">Kampanye baru dibuat sebagai draft. FastAPI memeriksa tenant dan permission saat penyimpanan.</p>
        <div className="flex gap-2"><button onClick={() => setShowCreate(false)} className="flex-1 rounded-xl bg-slate-100 py-2.5 text-xs font-semibold text-slate-600">Batal</button><button onClick={() => void create()} disabled={saving} className="flex-1 rounded-xl bg-red-600 py-2.5 text-xs font-bold text-white disabled:opacity-50">{saving ? 'Menyimpan…' : 'Simpan draft'}</button></div>
      </div></div>}
    </div>
  );
};
