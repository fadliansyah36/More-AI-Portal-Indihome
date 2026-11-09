'use client';

import React, { useState } from 'react';
import {
  Gift,
  Zap,
  CheckCircle2,
  Clock,
  Sparkles,
  Wifi,
  ChevronRight,
  ShieldCheck,
  CreditCard,
  Plus,
  Receipt,
  Ticket,
} from 'lucide-react';
import { useToast } from '@/components/ui/toast-context';
import { NavigationTab } from '@/types/moreai';

interface BenefitCreditViewProps {
  onNavigateTab?: (tab: NavigationTab) => void;
}

export const BenefitCreditView: React.FC<BenefitCreditViewProps> = ({ onNavigateTab }) => {
  const { showToast } = useToast();
  const [activeSubTab, setActiveSubTab] = useState<'semua' | 'wifi' | 'ai'>('semua');
  const [isActivated, setIsActivated] = useState(true);
  const [balance, setBalance] = useState(8500);

  const usageHistory = [
    {
      id: 'h-1',
      title: 'Akses Wi-Fi IndiHome',
      type: 'wifi',
      date: '12 Jul 2027 · 2 jam',
      amount: 'Gratis via Partner',
      positive: true,
    },
    {
      id: 'h-2',
      title: 'Research Agent Run',
      type: 'ai',
      date: '12 Apr, 14:20',
      amount: '-500 Poin',
      positive: false,
    },
    {
      id: 'h-3',
      title: 'Creative Image Generation',
      type: 'ai',
      date: '12 Apr, 10:15',
      amount: '-300 Poin',
      positive: false,
    },
    {
      id: 'h-4',
      title: 'Chat AI MoreAI Assistant',
      type: 'ai',
      date: '11 Apr, 16:40',
      amount: '-50 Poin',
      positive: false,
    },
    {
      id: 'h-5',
      title: 'Bonus Login Jaringan IndiHome',
      type: 'wifi',
      date: '10 Apr, 09:00',
      amount: '+1.000 Poin',
      positive: true,
    },
  ];

  const filteredHistory = usageHistory.filter((h) => {
    if (activeSubTab === 'wifi') return h.type === 'wifi';
    if (activeSubTab === 'ai') return h.type === 'ai';
    return true;
  });

  const handleTopUp = () => {
    setBalance((prev) => prev + 5000);
    showToast('Top Up Simulasi: Berhasil menambahkan 5.000 Poin AI Credit ke wallet Anda!', 'success');
  };

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Title */}
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">Benefit & AI Credit Center</h1>
        <p className="text-xs text-slate-500">
          Kelola kuota, saldo kredit, dan hak istimewa pengguna jaringan IndiHome
        </p>
      </div>

      {/* Featured Big Red Benefit Card (Exact layout from Sheet 1, 2, 5, 6) */}
      <div className="p-5 rounded-3xl bg-gradient-to-br from-red-600 via-rose-600 to-red-700 text-white shadow-md relative overflow-hidden">
        <div className="relative z-10 space-y-3">
          <div className="flex items-center justify-between">
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/20 backdrop-blur-xs text-[10px] font-bold">
              <Gift className="w-3.5 h-3.5 text-amber-300" />
              <span>PARTNER FREE · Telkom IndiHome</span>
            </div>
            <span className="text-[10px] font-bold text-emerald-300 bg-emerald-950/40 px-2.5 py-0.5 rounded-full border border-emerald-400/30">
              {isActivated ? 'Aktif hingga 31 Des 2026' : 'Belum Diaktifkan'}
            </span>
          </div>

          <div>
            <span className="text-xs text-red-100 font-medium block">AI Credit Free IndiHome</span>
            <div className="flex items-baseline gap-2 mt-0.5">
              <span className="text-2xl sm:text-3xl font-black tracking-tight">100.000</span>
              <span className="text-xs font-bold text-red-200">Poin / Bulan</span>
            </div>
            <span className="text-[11px] text-white/80 block mt-0.5">
              Saldo Aktif Saat Ini: <strong>{balance.toLocaleString('id-ID')} Poin</strong> (≈ 2.5M Token)
            </span>
          </div>

          <div className="pt-2 flex gap-2">
            <button
              onClick={() => {
                const nextState = !isActivated;
                setIsActivated(nextState);
                showToast(nextState ? 'Benefit AI Credit IndiHome berhasil diaktifkan!' : 'Benefit telah dinonaktifkan sementara', 'info');
              }}
              className="flex-1 py-2.5 rounded-xl bg-white text-red-600 font-bold text-xs hover:bg-red-50 transition shadow-xs text-center"
            >
              {isActivated ? 'Status: Terhubung & Aktif' : 'Aktifkan Sekarang'}
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
          Detail Benefit Eksklusif IndiHome
        </h2>

        <div className="space-y-2">
          <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-red-50 text-red-600 flex items-center justify-center shrink-0">
                <Sparkles className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-900">Akses MoreAI Premium</h4>
                <p className="text-[10px] text-slate-500">Model AI canggih tanpa antrian server</p>
              </div>
            </div>
            <span className="text-[10px] text-emerald-600 font-bold bg-emerald-50 px-2 py-0.5 rounded-full">
              Gratis
            </span>
          </div>

          <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                <Zap className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-900">Voucher AI Tools</h4>
                <p className="text-[10px] text-slate-500">Nilai Rp 50.000 untuk generator gambar & video</p>
              </div>
            </div>
            <span className="text-[10px] text-slate-600 font-semibold bg-slate-100 px-2 py-0.5 rounded-full">
              Terklaim
            </span>
          </div>

          <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center shrink-0">
                <Gift className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-900">Diskon Partner Kafe & Resto</h4>
                <p className="text-[10px] text-slate-500">Diskon Rp 25.000 di 100+ venue partner</p>
              </div>
            </div>
            <span className="text-[10px] text-slate-600 font-semibold bg-slate-100 px-2 py-0.5 rounded-full">
              Siap Digunakan
            </span>
          </div>
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
                  {h.type === 'wifi' ? <Wifi className="w-3.5 h-3.5" /> : <Sparkles className="w-3.5 h-3.5" />}
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
