'use client';

import React, { useEffect, useState } from 'react';
import { ArrowLeft, Crown } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { customerApi, type CustomerEntitlement } from '@/lib/api/client';

interface AccountUpgradeViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

export const AccountUpgradeView: React.FC<AccountUpgradeViewProps> = ({ onBack }) => {
  const [entitlements, setEntitlements] = useState<CustomerEntitlement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    customerApi.entitlements().then((rows) => { if (active) setEntitlements(rows); })
      .catch((cause) => { if (active) setError(cause instanceof Error ? cause.message : 'Entitlement akun tidak dapat dimuat.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);
  const activeEntitlements = entitlements.filter((item) => item.status === 'active');

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <button onClick={onBack} className="p-1 rounded-lg text-slate-400 hover:text-slate-700">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="text-center">
          <span className="text-[10px] font-bold text-red-600 uppercase tracking-wider block">
            Sheet 3 Screen 11
          </span>
          <h1 className="text-sm sm:text-base font-bold text-slate-900 leading-tight">
            Upgrade ke Akun Penuh
          </h1>
        </div>
        <div className="w-5" />
      </div>

      {/* Hero Card */}
      <div className="p-5 rounded-3xl bg-gradient-to-br from-red-600 via-rose-600 to-red-700 text-white shadow-md space-y-3 text-center">
        <div className="w-12 h-12 rounded-2xl bg-white/20 backdrop-blur-xs text-amber-300 flex items-center justify-center mx-auto shadow-2xs">
          <Crown className="w-6 h-6" />
        </div>
        <div>
          <h2 className="text-lg font-black tracking-tight">Lebih Banyak Ruang &amp; Kuota AI</h2>
          <p className="text-xs text-red-100 mt-1 max-w-xs mx-auto">
            Simpan riwayat tugas permanen, akses AI tanpa batas kuota venue, dan aktifkan semua autonomous agent.
          </p>
        </div>
      </div>

      <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-xs space-y-3">
        <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Entitlement Akun Saat Ini</h3>
        {loading ? <p className="text-xs text-slate-500">Memuat status paket dari backend…</p> : error ? (
          <p role="alert" className="text-xs text-red-600">{error}</p>
        ) : activeEntitlements.length ? activeEntitlements.map((item) => (
          <div key={item.id} className="rounded-2xl bg-slate-50 border border-slate-100 p-3">
            <p className="text-xs font-semibold text-slate-900">{item.entitlement_key}</p>
            <p className="mt-1 text-[10px] text-slate-500">Sumber: {item.source_type}{item.expires_at ? ' · Berlaku sampai ' + new Date(item.expires_at).toLocaleString('id-ID') : ''}</p>
          </div>
        )) : <p className="text-xs text-slate-500">Belum ada entitlement aktif yang tercatat pada akun ini.</p>}
      </div>
      <div className="rounded-3xl border border-amber-200 bg-amber-50 p-4 space-y-2">
        <h3 className="text-xs font-bold text-amber-900">Upgrade dan pembayaran belum tersedia</h3>
        <p className="text-xs leading-relaxed text-amber-800">Harga paket, checkout, dan aktivasi subscription belum terhubung ke backend pembayaran. Tidak ada upgrade yang akan diklaim berhasil sebelum transaksi dan entitlement dikonfirmasi oleh server.</p>
        <button type="button" disabled className="w-full py-3.5 rounded-2xl bg-slate-300 text-slate-600 font-bold text-xs cursor-not-allowed">Upgrade belum dapat dilakukan</button>
      </div>
    </div>
  );
};
