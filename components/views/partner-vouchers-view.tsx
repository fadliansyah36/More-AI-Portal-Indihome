'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { ArrowLeft, Ticket, Gift, QrCode, RefreshCw, Copy, Ban, Plus, X } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';
import { partnerApi } from '@/lib/api/client';

type AccessCode = {
  id: string;
  location_id: string | null;
  network_id: string | null;
  campaign_id: string | null;
  reward_id: string | null;
  status: 'active' | 'revoked' | 'exhausted' | 'expired' | string;
  expires_at: string;
  max_redemptions: number;
  redemption_count: number;
  created_at: string;
  revoked_at: string | null;
};

interface PartnerVouchersViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

export const PartnerVouchersView: React.FC<PartnerVouchersViewProps> = ({
  onBack,
}) => {
  const { showToast } = useToast();
  const [codes, setCodes] = useState<AccessCode[]>([]);
  const [selectedCode, setSelectedCode] = useState<string | null>(null);
  const [newCode, setNewCode] = useState<string | null>(null);
  const [expiresAt, setExpiresAt] = useState(() => new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 16));
  const [maxRedemptions, setMaxRedemptions] = useState('1');
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const rows = await partnerApi.accessCodes();
      setCodes(rows as AccessCode[]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Data kode akses tidak dapat dimuat.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const createCode = async () => {
    const expiry = new Date(expiresAt);
    const count = Number(maxRedemptions);
    if (!Number.isFinite(expiry.getTime()) || expiry.getTime() <= Date.now()) {
      showToast('Masa berlaku harus berada di waktu mendatang.', 'error');
      return;
    }
    if (!Number.isInteger(count) || count < 1 || count > 100000) {
      showToast('Batas penukaran harus berupa angka 1–100.000.', 'error');
      return;
    }
    setSaving(true);
    try {
      const result = await partnerApi.createAccessCode({
        expires_at: expiry.toISOString(),
        max_redemptions: count,
      });
      setNewCode(result.access_code);
      setShowCreate(false);
      await load();
      showToast('Kode akses berhasil dibuat. Salin sekarang; kode hanya ditampilkan satu kali.', 'success');
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Kode akses gagal dibuat.', 'error');
    } finally {
      setSaving(false);
    }
  };

  const revokeCode = async (code: AccessCode) => {
    if (code.status !== 'active') return;
    try {
      await partnerApi.revokeAccessCode(code.id);
      await load();
      showToast('Kode akses telah dicabut.', 'success');
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Kode akses gagal dicabut.', 'error');
    }
  };

  const copyCode = async (code: string) => {
    try {
      await navigator.clipboard.writeText(code);
      showToast('Kode akses disalin.', 'success');
    } catch {
      showToast('Tidak dapat menyalin otomatis. Silakan salin kode secara manual.', 'error');
    }
  };

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <button onClick={onBack} className="p-1 rounded-lg text-slate-400 hover:text-slate-700" aria-label="Kembali">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="text-center">
          <span className="text-[10px] font-bold text-red-600 uppercase tracking-wider block">Partner Operations</span>
          <h1 className="text-sm sm:text-base font-bold text-slate-900 leading-tight">Voucher &amp; Kode Akses</h1>
        </div>
        <button onClick={() => void load()} disabled={loading} className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 disabled:opacity-50" aria-label="Segarkan">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="p-5 rounded-3xl bg-gradient-to-r from-red-600 via-rose-600 to-amber-600 text-white shadow-xs space-y-2">
        <div className="flex items-center gap-1.5 text-xs text-amber-100 font-bold uppercase">
          <Gift className="w-4 h-4" /><span>Partner Network Access</span>
        </div>
        <h2 className="text-base font-black">Kelola kode akses jaringan</h2>
        <p className="text-xs text-white/90">Kode dibuat dan diverifikasi oleh backend. Kode asli hanya ditampilkan saat penerbitan; database menyimpan hash-nya.</p>
        <button onClick={() => setShowCreate(true)} className="inline-flex items-center gap-2 rounded-xl bg-white px-3.5 py-2 text-xs font-bold text-red-700 hover:bg-red-50">
          <Plus className="w-4 h-4" /> Buat kode akses
        </button>
      </div>

      {error && <div role="alert" className="rounded-2xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">{error}</div>}
      {loading && <p className="py-8 text-center text-xs text-slate-500">Memuat kode akses dari FastAPI…</p>}
      {!loading && !error && codes.length === 0 && (
        <div className="rounded-3xl border border-slate-100 bg-white p-6 text-center">
          <Ticket className="mx-auto h-8 w-8 text-slate-300" />
          <p className="mt-2 text-sm font-semibold text-slate-700">Belum ada kode akses</p>
          <p className="mt-1 text-xs text-slate-500">Kode yang diterbitkan untuk tenant aktif akan tampil di sini.</p>
        </div>
      )}

      <div className="space-y-3">
        {codes.map((code) => (
          <article key={code.id} className="space-y-3 rounded-3xl border border-slate-100 bg-white p-4 text-xs shadow-xs">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <h3 className="font-bold text-slate-900">Kode akses jaringan</h3>
                <p className="mt-1 break-all font-mono text-[10px] text-slate-400">{code.id}</p>
              </div>
              <span className={`shrink-0 rounded-full px-2.5 py-1 text-[10px] font-bold ${code.status === 'active' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>{code.status}</span>
            </div>
            <div className="grid grid-cols-2 gap-2 border-t border-slate-100 pt-3">
              <div><span className="block text-[10px] text-slate-400">Penukaran</span><strong className="text-slate-800">{code.redemption_count} / {code.max_redemptions}</strong></div>
              <div><span className="block text-[10px] text-slate-400">Berlaku sampai</span><strong className="text-slate-800">{new Date(code.expires_at).toLocaleString('id-ID')}</strong></div>
            </div>
            <div className="flex items-center justify-between border-t border-slate-100 pt-2">
              <button onClick={() => setSelectedCode(code.id)} className="text-[11px] font-semibold text-slate-600 hover:text-slate-900">Detail</button>
              {code.status === 'active' && <button onClick={() => void revokeCode(code)} className="inline-flex items-center gap-1 rounded-lg border border-red-100 px-2.5 py-1.5 text-[11px] font-semibold text-red-600 hover:bg-red-50"><Ban className="h-3.5 w-3.5" /> Cabut kode</button>}
            </div>
            {selectedCode === code.id && <div className="rounded-xl bg-slate-50 p-3 text-[10px] text-slate-600">Lokasi: {code.location_id || 'Semua lokasi tenant'}<br/>Jaringan: {code.network_id || 'Tidak dibatasi'}<br/>Campaign: {code.campaign_id || 'Tidak terhubung'}<br/>Reward: {code.reward_id || 'Tidak terhubung'}</div>}
          </article>
        ))}
      </div>

      {newCode && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="w-full max-w-sm space-y-4 rounded-3xl border border-slate-100 bg-white p-6 text-center shadow-2xl">
            <QrCode className="mx-auto h-8 w-8 text-red-600" />
            <h3 className="text-sm font-bold text-slate-900">Kode akses berhasil diterbitkan</h3>
            <p className="text-xs text-slate-500">Simpan kode ini sekarang. Demi keamanan, backend tidak menyediakan plaintext lagi setelah pembuatan.</p>
            <div className="break-all rounded-2xl border border-slate-200 bg-slate-50 p-4 font-mono text-sm font-bold text-slate-900">{newCode}</div>
            <button onClick={() => void copyCode(newCode)} className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-red-600 py-2.5 text-xs font-bold text-white"><Copy className="h-4 w-4" /> Salin kode</button>
            <button onClick={() => setNewCode(null)} className="w-full rounded-xl bg-slate-100 py-2.5 text-xs font-semibold text-slate-700">Tutup</button>
          </div>
        </div>
      )}

      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="w-full max-w-sm space-y-4 rounded-3xl border border-slate-100 bg-white p-5 shadow-2xl">
            <div className="flex items-center justify-between"><h3 className="text-sm font-bold text-slate-900">Buat kode akses</h3><button onClick={() => setShowCreate(false)} aria-label="Tutup"><X className="h-4 w-4 text-slate-400" /></button></div>
            <label className="block space-y-1 text-xs"><span className="font-semibold text-slate-700">Berlaku sampai</span><input type="datetime-local" value={expiresAt} onChange={(e) => setExpiresAt(e.target.value)} className="w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5" /></label>
            <label className="block space-y-1 text-xs"><span className="font-semibold text-slate-700">Maksimum penukaran</span><input type="number" min="1" max="100000" value={maxRedemptions} onChange={(e) => setMaxRedemptions(e.target.value)} className="w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5" /></label>
            <p className="text-[10px] text-slate-500">Penerbitan kode membutuhkan role Partner Owner atau Partner Admin.</p>
            <div className="flex gap-2"><button onClick={() => setShowCreate(false)} className="flex-1 rounded-xl bg-slate-100 py-2.5 text-xs font-semibold text-slate-600">Batal</button><button onClick={() => void createCode()} disabled={saving} className="flex-1 rounded-xl bg-red-600 py-2.5 text-xs font-bold text-white disabled:opacity-50">{saving ? 'Menerbitkan…' : 'Terbitkan kode'}</button></div>
          </div>
        </div>
      )}
    </div>
  );
};
