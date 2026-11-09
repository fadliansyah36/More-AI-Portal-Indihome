'use client';

import React, { useState } from 'react';
import { ArrowLeft, History, ArrowDownRight, ArrowUpRight, Filter, Search, ShieldCheck } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';

interface TokenLedgerViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

export const TokenLedgerView: React.FC<TokenLedgerViewProps> = ({
  onBack,
  onNavigateTab,
}) => {
  const { showToast } = useToast();
  const [filterType, setFilterType] = useState<'semua' | 'debit' | 'kredit'>('semua');

  const transactions = [
    {
      id: 'tx-101',
      title: 'Aktivasi Partner Free IndiHome',
      type: 'kredit',
      amount: '+100.000 Poin',
      date: '01 Nov 2026, 08:00 WIB',
      category: 'Kuota Bulanan',
      refHash: '0x8f2a...c4b1',
    },
    {
      id: 'tx-102',
      title: 'Research Agent Run (Analisis Pasar)',
      type: 'debit',
      amount: '-500 Poin',
      date: '02 Nov 2026, 14:20 WIB',
      category: 'Eksekusi Agent',
      refHash: '0x3e1d...99fa',
    },
    {
      id: 'tx-103',
      title: 'Generator Gambar Konten Medsos',
      type: 'debit',
      amount: '-300 Poin',
      date: '03 Nov 2026, 10:15 WIB',
      category: 'Kreativitas AI',
      refHash: '0x1b4c...72d8',
    },
    {
      id: 'tx-104',
      title: 'Top Up Kredit Mandiri Promo',
      type: 'kredit',
      amount: '+5.000 Poin',
      date: '05 Nov 2026, 19:40 WIB',
      category: 'Top Up Wallet',
      refHash: '0x7c2f...aa14',
    },
    {
      id: 'tx-105',
      title: 'Ringkasan Laporan Finansial PDF',
      type: 'debit',
      amount: '-150 Poin',
      date: '07 Nov 2026, 11:30 WIB',
      category: 'Pengolahan Dokumen',
      refHash: '0x99dd...01ce',
    },
  ];

  const filtered = transactions.filter((tx) => {
    if (filterType === 'debit') return tx.type === 'debit';
    if (filterType === 'kredit') return tx.type === 'kredit';
    return true;
  });

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <button onClick={onBack} className="p-1 rounded-lg text-slate-400 hover:text-slate-700">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="text-center">
          <span className="text-[10px] font-bold text-red-600 uppercase tracking-wider block">
            Sheet 5 Screen 13
          </span>
          <h1 className="text-sm sm:text-base font-bold text-slate-900 leading-tight">
            Riwayat Transaksi &amp; Ledger Token
          </h1>
        </div>
        <div className="w-5" />
      </div>

      {/* Balance Summary Banner */}
      <div className="p-5 rounded-3xl bg-slate-900 text-white shadow-xs space-y-2">
        <span className="text-[10px] uppercase font-bold text-slate-400">Saldo Dompet AI</span>
        <div className="flex items-baseline justify-between">
          <div>
            <span className="text-3xl font-black tracking-tight text-white font-mono">104.050</span>
            <span className="text-xs font-bold text-red-400 ml-1.5">Poin AI</span>
          </div>
          <span className="text-xs text-emerald-400 font-semibold bg-emerald-950/60 px-2.5 py-1 rounded-full border border-emerald-500/30">
            ≈ 2.6M Token
          </span>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1 p-1 bg-white rounded-2xl border border-slate-200 shadow-2xs text-xs font-semibold">
        <button
          onClick={() => setFilterType('semua')}
          className={`flex-1 py-1.5 rounded-xl transition ${
            filterType === 'semua' ? 'bg-red-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-50'
          }`}
        >
          Semua
        </button>
        <button
          onClick={() => setFilterType('kredit')}
          className={`flex-1 py-1.5 rounded-xl transition ${
            filterType === 'kredit' ? 'bg-red-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-50'
          }`}
        >
          Pemasukan (+)
        </button>
        <button
          onClick={() => setFilterType('debit')}
          className={`flex-1 py-1.5 rounded-xl transition ${
            filterType === 'debit' ? 'bg-red-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-50'
          }`}
        >
          Pengeluaran (-)
        </button>
      </div>

      {/* Transactions List */}
      <div className="space-y-2.5">
        {filtered.map((tx) => (
          <div
            key={tx.id}
            className="p-3.5 rounded-2xl bg-white border border-slate-100 shadow-2xs flex items-center justify-between gap-3 text-xs"
          >
            <div className="flex items-center gap-3 min-w-0">
              <div
                className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                  tx.type === 'kredit'
                    ? 'bg-emerald-50 text-emerald-600'
                    : 'bg-red-50 text-red-600'
                }`}
              >
                {tx.type === 'kredit' ? (
                  <ArrowDownRight className="w-5 h-5" />
                ) : (
                  <ArrowUpRight className="w-5 h-5" />
                )}
              </div>
              <div className="min-w-0">
                <h3 className="font-bold text-slate-900 truncate">{tx.title}</h3>
                <div className="flex items-center gap-2 text-[10px] text-slate-400 mt-0.5">
                  <span>{tx.date}</span>
                  <span>•</span>
                  <span className="font-mono">{tx.refHash}</span>
                </div>
              </div>
            </div>

            <div className="text-right shrink-0">
              <span
                className={`font-mono font-bold text-xs ${
                  tx.type === 'kredit' ? 'text-emerald-600' : 'text-red-600'
                }`}
              >
                {tx.amount}
              </span>
              <span className="text-[9px] text-slate-400 block mt-0.5">{tx.category}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
