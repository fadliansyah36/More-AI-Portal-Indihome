'use client';

import React, { useEffect, useMemo, useState } from 'react';
import {
  Gift,
  Zap,
  Sparkles,
  Wifi,
  ChevronRight,
  Plus,
  Receipt,
  Ticket,
} from 'lucide-react';
import { useToast } from '@/components/ui/toast-context';
import { NavigationTab } from '@/types/moreai';
import { customerApi, CustomerEntitlement, CustomerLedgerEntry, CustomerQuota, CustomerUsageRecord, CustomerWallet } from '@/lib/api/client';

interface BenefitCreditViewProps {
  onNavigateTab?: (tab: NavigationTab) => void;
}

export const BenefitCreditView: React.FC<BenefitCreditViewProps> = ({ onNavigateTab }) => {
  const { showToast } = useToast();
  const [activeSubTab, setActiveSubTab] = useState<'semua' | 'wifi' | 'ai'>('semua');
  const [wallets, setWallets] = useState<CustomerWallet[]>([]);
  const [entitlements, setEntitlements] = useState<CustomerEntitlement[]>([]);
  const [quotas, setQuotas] = useState<CustomerQuota[]>([]);
  const [usage, setUsage] = useState<CustomerUsageRecord[]>([]);
  const [ledger, setLedger] = useState<CustomerLedgerEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    Promise.all([
      customerApi.wallets(),
      customerApi.entitlements(),
      customerApi.quotas(),
      customerApi.usage(50),
      customerApi.ledger(50),
    ]).then(([walletResult, entitlementResult, quotaResult, usageResult, ledgerResult]) => {
      if (!active) return;
      setWallets(walletResult.wallets || []);
      setEntitlements(entitlementResult || []);
      setQuotas(quotaResult || []);
      setUsage(usageResult || []);
      setLedger(ledgerResult || []);
      setError(null);
    }).catch((err: unknown) => {
      if (!active) return;
      setError(err instanceof Error ? err.message : 'Data benefit dan kredit tidak dapat dimuat.');
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, []);

  const balance = useMemo(
    () => wallets.reduce((total, wallet) => total + Number(wallet.balance || 0), 0),
    [wallets],
  );
  const activeEntitlements = entitlements.filter((item) => item.status === 'active');
  const monthlyQuota = quotas.find((item) => /month|monthly|llm|token|credit/i.test(item.metric_key)) || quotas[0];
  const history = usage.map((item) => ({
    id: item.id,
    title: item.model_key || item.provider_key || 'Penggunaan AI',
    type: (item as CustomerUsageRecord).id ? 'ai' as const : 'ai' as const,
    date: new Date(item.created_at).toLocaleString('id-ID'),
    amount: item.actual_cost !== null ? String(item.actual_cost) : String(item.estimated_cost),
    positive: false,
  })).concat(ledger.map((item) => ({
    id: item.id,
    title: item.description || item.entry_type,
    type: 'ai' as const,
    date: new Date(item.created_at).toLocaleString('id-ID'),
    amount: Number(item.amount).toLocaleString('id-ID'),
    positive: Number(item.amount) > 0,
  }))).sort((a, b) => b.date.localeCompare(a.date));
  const filteredHistory = activeSubTab === 'wifi' ? [] : history;
  const handleTopUp = () => showToast('Top Up belum tersedia melalui backend pembayaran. Tidak ada saldo yang diubah.', 'info');

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Title */}
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">Benefit & AI Credit Center</h1>
        <p className="text-xs text-slate-500">
          Kelola kuota, saldo kredit, dan hak istimewa pengguna jaringan Global Partner ISP/Network
        </p>
      </div>

      {/* Featured Big Red Benefit Card (Exact layout from Sheet 1, 2, 5, 6) */}
      <div className="p-5 rounded-3xl bg-gradient-to-br from-red-600 via-rose-600 to-red-700 text-white shadow-md relative overflow-hidden">
        <div className="relative z-10 space-y-3">
          <div className="flex items-center justify-between">
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/20 backdrop-blur-xs text-[10px] font-bold">
              <Gift className="w-3.5 h-3.5 text-amber-300" />
              <span>BENEFIT &amp; AI CREDIT</span>
            </div>
            <span className="text-[10px] font-bold text-emerald-300 bg-emerald-950/40 px-2.5 py-0.5 rounded-full border border-emerald-400/30">
              {loading ? 'Memuat status' : activeEntitlements.length ? 'Benefit Aktif' : 'Belum Ada Benefit'}
            </span>
          </div>

          <div>
            <span className="text-xs text-red-100 font-medium block">AI Credit &amp; Entitlement</span>
            <div className="flex items-baseline gap-2 mt-0.5">
              <span className="text-2xl sm:text-3xl font-black tracking-tight">{monthlyQuota ? Number(monthlyQuota.limit_value).toLocaleString('id-ID') : '—'}</span>
              <span className="text-xs font-bold text-red-200">{monthlyQuota?.metric_key || 'Kuota belum tersedia'}</span>
            </div>
            <span className="text-[11px] text-white/80 block mt-0.5">
              Saldo wallet aktif: <strong>{loading ? 'Memuat…' : `${balance.toLocaleString('id-ID')} ${wallets[0]?.currency || 'CREDIT'}`}</strong>
            </span>
          </div>

          <div className="pt-2 flex gap-2">
            <button
              onClick={() => showToast(activeEntitlements.length ? 'Status benefit dibaca dari entitlement akun.' : 'Belum ada entitlement benefit aktif pada akun ini.', 'info')}
              className="flex-1 py-2.5 rounded-xl bg-white text-red-600 font-bold text-xs hover:bg-red-50 transition shadow-xs text-center"
            >
              {loading ? 'Memuat Status…' : activeEntitlements.length ? 'Status Benefit Aktif' : 'Belum Ada Benefit'}
            </button>
            <button
              onClick={handleTopUp}
              className="px-4 py-2.5 rounded-xl bg-red-900/40 hover:bg-red-900/60 text-white font-bold text-xs border border-white/20 transition flex items-center gap-1"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Top Up</span>
            </button>
          </div>
        </div>

        {/* Ambient background decoration */}
        <div className="absolute -right-6 -bottom-6 w-32 h-32 rounded-full bg-white/10 blur-xl pointer-events-none" />
      </div>

      {/* Detail Benefit List (From Sheet 5) */}
      <div className="bg-white rounded-3xl p-4 border border-slate-100 shadow-xs space-y-3">
        <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
          Detail Benefit Eksklusif Global Partner ISP
        </h2>

        <div className="space-y-2">
          {activeEntitlements.length ? activeEntitlements.map((item) => (
            <div key={item.id} className="p-3 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-between">
              <div>
                <h4 className="text-xs font-bold text-slate-900">{String(item.metadata?.label || item.entitlement_key)}</h4>
                <p className="text-[10px] text-slate-500">{item.source_type} · berlaku mulai {new Date(item.starts_at).toLocaleDateString('id-ID')}</p>
              </div>
              <span className="text-[10px] text-emerald-600 font-bold bg-emerald-50 px-2 py-0.5 rounded-full">Aktif</span>
            </div>
          )) : (
            <p className="text-xs text-slate-500 p-3 rounded-2xl bg-slate-50 border border-slate-100">
              {loading ? 'Memuat entitlement dari akun…' : 'Belum ada benefit aktif yang tercatat untuk akun ini.'}
            </p>
          )}
        </div>

        {/* Quick Navigation Cards (Sheet 5 #12 & #13) */}
        {onNavigateTab && (
          <div className="grid grid-cols-2 gap-2 pt-1 border-t border-slate-100">
            <button
              onClick={() => onNavigateTab('token_ledger')}
              className="p-3 rounded-2xl bg-slate-50 hover:bg-slate-100 border border-slate-100 text-left transition group"
            >
              <div className="flex items-center justify-between mb-1">
                <Receipt className="w-4 h-4 text-red-600" />
                <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:translate-x-0.5 transition-transform" />
              </div>
              <span className="text-xs font-bold text-slate-900 block">Ledger Token</span>
              <span className="text-[10px] text-slate-500">Audit hash transaksi</span>
            </button>

            <button
              onClick={() => onNavigateTab('partner_vouchers')}
              className="p-3 rounded-2xl bg-slate-50 hover:bg-slate-100 border border-slate-100 text-left transition group"
            >
              <div className="flex items-center justify-between mb-1">
                <Ticket className="w-4 h-4 text-amber-600" />
                <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:translate-x-0.5 transition-transform" />
              </div>
              <span className="text-xs font-bold text-slate-900 block">Dompet Kupon</span>
              <span className="text-[10px] text-slate-500">Voucher kafe mitra</span>
            </button>
          </div>
        )}
      </div>

      {/* Riwayat Penggunaan (Sheet 1, 5, 6) */}
      <div className="bg-white rounded-3xl p-4 border border-slate-100 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            Riwayat Penggunaan
          </h2>
          {onNavigateTab ? (
            <button
              onClick={() => onNavigateTab('token_ledger')}
              className="text-[11px] font-bold text-red-600 hover:text-red-700 flex items-center gap-0.5"
            >
              <span>Lihat Ledger</span>
              <ChevronRight className="w-3 h-3" />
            </button>
          ) : (
            <span className="text-[10px] text-slate-400">Terakhir disinkronkan</span>
          )}
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-1 p-1 bg-slate-100 rounded-xl">
          {(['semua', 'wifi', 'ai'] as const).map((sub) => (
            <button
              key={sub}
              onClick={() => setActiveSubTab(sub)}
              className={`flex-1 py-1 text-[11px] font-semibold rounded-lg capitalize transition ${
                activeSubTab === sub
                  ? 'bg-white text-slate-900 shadow-2xs'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              {sub === 'wifi' ? 'Wi-Fi' : sub === 'ai' ? 'AI Access' : 'Semua'}
            </button>
          ))}
        </div>

        {/* History items */}
        <div className="space-y-2">
          {error && <p className="text-xs text-rose-600">{error}</p>}
          {!loading && filteredHistory.length === 0 && <p className="text-xs text-slate-500 p-3">{activeSubTab === 'wifi' ? 'Riwayat sesi Wi-Fi belum tersedia pada endpoint ini.' : 'Belum ada riwayat kredit atau penggunaan AI.'}</p>}
          {filteredHistory.map((h) => (
            <div
              key={h.id}
              className="p-3 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-between"
            >
              <div className="flex items-center gap-2.5">
                <div
                  className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs ${
                    h.positive
                      ? 'bg-emerald-50 text-emerald-600'
                      : 'bg-rose-50 text-rose-600'
                  }`}
                >
                  {<Sparkles className="w-3.5 h-3.5" />}
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-900">{h.title}</h4>
                  <span className="text-[10px] text-slate-400">{h.date}</span>
                </div>
              </div>

              <span
                className={`text-xs font-bold ${
                  h.positive ? 'text-emerald-600' : 'text-red-600'
                }`}
              >
                {h.amount}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
