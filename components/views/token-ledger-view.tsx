'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { ArrowLeft, ArrowDownRight, ArrowUpRight } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { customerApi, CustomerLedgerEntry, CustomerWallet } from '@/lib/api/client';

interface TokenLedgerViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

export const TokenLedgerView: React.FC<TokenLedgerViewProps> = ({ onBack }) => {
  const [filterType, setFilterType] = useState<'semua' | 'debit' | 'kredit'>('semua');
  const [wallets, setWallets] = useState<CustomerWallet[]>([]);
  const [transactions, setTransactions] = useState<CustomerLedgerEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);

  useEffect(() => {
    let active = true;
    customerApi.wallets()
      .then(async (walletResult) => {
        if (!active) return;
        setWallets(walletResult.wallets);
        const primary = walletResult.wallets.find((wallet) => wallet.status === 'active') || walletResult.wallets[0];
        if (!primary) {
          setTransactions([]);
          setNextCursor(null);
          return;
        }
        const ledgerResult = await customerApi.ledgerPage(50, undefined, primary.id);
        if (!active) return;
        setTransactions(ledgerResult.items);
        setNextCursor(ledgerResult.nextCursor);
      })
      .catch((err) => {
        if (active) setError(err instanceof Error ? err.message : 'Data wallet tidak tersedia.');
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const filtered = useMemo(() => transactions.filter((tx) => {
    const amount = Number(tx.amount);
    const entryType = tx.entry_type.toLowerCase();
    const debit = /debit|spend|usage|reserve|charge/i.test(entryType);
    const credit = /credit|refund|top.?up|grant|release/i.test(entryType) || (!debit && amount > 0);
    if (filterType === 'debit') return debit;
    if (filterType === 'kredit') return credit;
    return true;
  }), [transactions, filterType]);

  const primaryWallet = wallets.find((wallet) => wallet.status === 'active') || wallets[0];

  const loadMore = async () => {
    if (!nextCursor || loadingMore || !primaryWallet) return;
    setLoadingMore(true);
    try {
      const page = await customerApi.ledgerPage(50, nextCursor, primaryWallet.id);
      setTransactions((current) => [...current, ...page.items]);
      setNextCursor(page.nextCursor);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Riwayat transaksi berikutnya tidak dapat dimuat.');
    } finally {
      setLoadingMore(false);
    }
  };
  const formatAmount = (value: string | number, currency: string) =>
    new Intl.NumberFormat('id-ID', { maximumFractionDigits: 4 }).format(Number(value)) + ' ' + currency;
  const formatDate = (value: string) => new Date(value).toLocaleString('id-ID', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  });

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <button onClick={onBack} className="p-1 rounded-lg text-slate-400 hover:text-slate-700" aria-label="Kembali">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="text-center">
          <span className="text-[10px] font-bold text-red-600 uppercase tracking-wider block">Sheet 5 Screen 13</span>
          <h1 className="text-sm sm:text-base font-bold text-slate-900 leading-tight">Riwayat Transaksi &amp; Ledger Token</h1>
        </div>
        <div className="w-5" />
      </div>

      <div className="p-5 rounded-3xl bg-slate-900 text-white shadow-xs space-y-2">
        <span className="text-[10px] uppercase font-bold text-slate-400">Saldo Dompet AI</span>
        <div className="flex items-baseline justify-between">
          <div>
            <span className="text-3xl font-black tracking-tight text-white font-mono">
              {loading ? '—' : primaryWallet ? formatAmount(primaryWallet.balance, primaryWallet.currency) : 'Tidak tersedia'}
            </span>
            <span className="text-xs font-bold text-red-400 ml-1.5">{primaryWallet?.status ?? 'Wallet'}</span>
          </div>
          <span className="text-xs text-emerald-400 font-semibold bg-emerald-950/60 px-2.5 py-1 rounded-full border border-emerald-500/30">
            {wallets.length} dompet
          </span>
        </div>
      </div>

      <div className="flex items-center gap-1 p-1 bg-white rounded-2xl border border-slate-200 shadow-2xs text-xs font-semibold">
        {(['semua', 'kredit', 'debit'] as const).map((type) => (
          <button key={type} onClick={() => setFilterType(type)}
            className={'flex-1 py-1.5 rounded-xl transition ' + (filterType === type ? 'bg-red-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-50')}>
            {type === 'semua' ? 'Semua' : type === 'kredit' ? 'Pemasukan (+)' : 'Pengeluaran (-)'}
          </button>
        ))}
      </div>

      <div className="space-y-2.5">
        {error && <p className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">{error}</p>}
        {loading && <p className="p-3 text-xs text-slate-500">Memuat saldo dan ledger dari server…</p>}
        {!loading && !error && filtered.length === 0 && (
          <p className="rounded-xl border border-slate-100 bg-white p-4 text-xs text-slate-500">Belum ada transaksi pada dompet ini.</p>
        )}
        {filtered.map((tx) => {
          const amount = Number(tx.amount);
          const isDebit = /debit|spend|usage|reserve|charge/i.test(tx.entry_type);
          const isCredit = /credit|refund|top.?up|grant|release/i.test(tx.entry_type) || (!isDebit && amount > 0);
          const signedAmount = (isDebit && amount > 0 ? '−' : amount > 0 ? '+' : '') + formatAmount(Math.abs(amount), primaryWallet?.currency ?? '');
          return (
            <div key={tx.id} className="p-3.5 rounded-2xl bg-white border border-slate-100 shadow-2xs flex items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-3 min-w-0">
                <div className={'w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ' + (isCredit ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-600')}>
                  {isCredit ? <ArrowDownRight className="w-5 h-5" /> : <ArrowUpRight className="w-5 h-5" />}
                </div>
                <div className="min-w-0">
                  <h3 className="font-bold text-slate-900 truncate">{tx.description || tx.entry_type}</h3>
                  <div className="flex items-center gap-2 text-[10px] text-slate-400 mt-0.5">
                    <span>{formatDate(tx.created_at)}</span>
                    {tx.reference_id && <><span>•</span><span className="font-mono">{tx.reference_id.slice(0, 12)}</span></>}
                  </div>
                </div>
              </div>
              <div className="text-right shrink-0">
                <span className={'font-mono font-bold text-xs ' + (isCredit ? 'text-emerald-600' : 'text-red-600')}>{signedAmount}</span>
                <span className="text-[9px] text-slate-400 block mt-0.5">{tx.entry_type}</span>
              </div>
            </div>
          );
        })}
        {!loading && !error && nextCursor && (
          <button type="button" onClick={loadMore} disabled={loadingMore}
            className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-xs font-bold text-slate-700 hover:bg-slate-50 disabled:opacity-50">
            {loadingMore ? 'Memuat transaksi…' : 'Muat transaksi berikutnya'}
          </button>
        )}
      </div>
    </div>
  );
};
