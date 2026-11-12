'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { ArrowLeft, Users, UserPlus, Shield, RefreshCw, X } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';
import { partnerApi, PartnerMember } from '@/lib/api/client';

interface PartnerStaffViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

const roleLabels: Record<string, string> = {
  partner_owner: 'Owner',
  partner_admin: 'Administrator',
  location_manager: 'Manajer Lokasi',
  partner_staff: 'Staf',
  partner_analyst: 'Analis',
};

export const PartnerStaffView: React.FC<PartnerStaffViewProps> = ({
  onBack,
}) => {
  const { showToast } = useToast();
  const [staffList, setStaffList] = useState<PartnerMember[]>([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [userId, setUserId] = useState('');
  const [role, setRole] = useState<'partner_admin' | 'location_manager' | 'partner_staff' | 'partner_analyst'>('partner_staff');
  const [locationId, setLocationId] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const rows = await partnerApi.members();
      setStaffList(rows as PartnerMember[]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Daftar staf tidak dapat dimuat.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    void Promise.resolve().then(() => { if (active) void load(); });
    return () => { active = false; };
  }, [load]);

  const invite = async () => {
    const normalizedUserId = userId.trim();
    if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(normalizedUserId)) {
      showToast('Masukkan User ID UUID yang valid.', 'error');
      return;
    }
    setSaving(true);
    try {
      await partnerApi.inviteMember({
        user_id: normalizedUserId,
        role_key: role,
        location_id: locationId.trim() || null,
      });
      setUserId('');
      setLocationId('');
      setShowAddModal(false);
      await load();
      showToast('Undangan keanggotaan mitra berhasil dibuat.', 'success');
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Undangan staf gagal dibuat.', 'error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <button onClick={onBack} className="p-1 rounded-lg text-slate-400 hover:text-slate-700" aria-label="Kembali">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="text-center">
          <span className="text-[10px] font-bold text-red-600 uppercase tracking-wider block">Partner Governance</span>
          <h1 className="text-sm sm:text-base font-bold text-slate-900 leading-tight">Manajemen Staf &amp; Operator</h1>
        </div>
        <div className="flex items-center gap-1">
          <button onClick={() => { setLoading(true); setError(null); void load(); }} disabled={loading} className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 disabled:opacity-50" aria-label="Segarkan">
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button onClick={() => setShowAddModal(true)} className="text-xs font-bold text-red-600 flex items-center gap-1 hover:text-red-700" aria-label="Undang staf">
            <UserPlus className="w-4 h-4" />
            <span className="hidden sm:inline">Undang Staf</span>
          </button>
        </div>
      </div>

      <div className="rounded-3xl border border-slate-100 bg-white p-4 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-red-50 text-red-600"><Users className="h-5 w-5" /></div>
          <div><p className="text-xs font-bold text-slate-900">Keanggotaan tenant aktif</p><p className="text-[11px] text-slate-500">Daftar berasal dari FastAPI dengan pembatasan tenant dan role di server.</p></div>
        </div>
      </div>

      {error && <div role="alert" className="rounded-2xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">{error}</div>}
      {loading && <p className="py-8 text-center text-xs text-slate-500">Memuat anggota tenant…</p>}
      {!loading && !error && staffList.length === 0 && <div className="rounded-3xl border border-slate-100 bg-white p-6 text-center"><Users className="mx-auto h-8 w-8 text-slate-300" /><p className="mt-2 text-sm font-semibold text-slate-700">Belum ada anggota</p><p className="mt-1 text-xs text-slate-500">Keanggotaan yang diotorisasi untuk tenant aktif akan muncul di sini.</p></div>}

      <div className="space-y-3">
        {staffList.map((staff) => (
          <div key={staff.id} className="flex items-center justify-between gap-3 rounded-3xl border border-slate-100 bg-white p-4 text-xs shadow-xs">
            <div className="flex min-w-0 items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-slate-800 text-sm font-bold text-white"><Shield className="h-4 w-4" /></div>
              <div className="min-w-0">
                <h3 className="truncate font-bold text-slate-900">{staff.user_id}</h3>
                <p className="mt-0.5 text-[11px] text-slate-500">{roleLabels[staff.role_key] || staff.role_key}</p>
                <p className="mt-0.5 text-[10px] text-slate-400">Lokasi: {staff.location_id || 'Seluruh tenant'}</p>
              </div>
            </div>
            <span className={`shrink-0 rounded-full px-2 py-1 text-[9px] font-bold ${staff.status === 'active' ? 'border border-emerald-200 bg-emerald-50 text-emerald-600' : 'bg-slate-100 text-slate-600'}`}>{staff.status}</span>
          </div>
        ))}
      </div>

      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 animate-fadeIn">
          <div className="w-full max-w-sm space-y-3 rounded-3xl border border-slate-100 bg-white p-5 shadow-2xl">
            <div className="flex items-center justify-between"><h3 className="text-sm font-bold text-slate-900">Undang anggota tenant</h3><button onClick={() => setShowAddModal(false)} aria-label="Tutup"><X className="h-4 w-4 text-slate-400" /></button></div>
            <label className="block space-y-1 text-xs"><span className="font-semibold text-slate-700">Supabase User ID (UUID)</span><input value={userId} onChange={(e) => setUserId(e.target.value)} placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" className="w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5 font-mono text-[11px]" /></label>
            <label className="block space-y-1 text-xs"><span className="font-semibold text-slate-700">Peran</span><select value={role} onChange={(e) => setRole(e.target.value as typeof role)} className="w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5"><option value="partner_admin">Administrator</option><option value="location_manager">Manajer Lokasi</option><option value="partner_staff">Staf</option><option value="partner_analyst">Analis</option></select></label>
            <label className="block space-y-1 text-xs"><span className="font-semibold text-slate-700">Location ID (opsional)</span><input value={locationId} onChange={(e) => setLocationId(e.target.value)} placeholder="UUID lokasi" className="w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5 font-mono text-[11px]" /></label>
            <p className="text-[10px] text-slate-500">FastAPI hanya menerima undangan dari Partner Owner/Admin dan memvalidasi kepemilikan lokasi di server. Undangan tidak otomatis menjadi membership aktif.</p>
            <div className="flex gap-2"><button onClick={() => setShowAddModal(false)} className="flex-1 rounded-xl bg-slate-100 py-2.5 text-xs font-semibold text-slate-600">Batal</button><button onClick={() => void invite()} disabled={saving} className="flex-1 rounded-xl bg-red-600 py-2.5 text-xs font-bold text-white disabled:opacity-50">{saving ? 'Mengirim…' : 'Kirim undangan'}</button></div>
          </div>
        </div>
      )}
    </div>
  );
};
