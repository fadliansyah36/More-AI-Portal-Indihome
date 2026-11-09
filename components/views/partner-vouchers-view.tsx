'use client';

import React, { useState } from 'react';
import { ArrowLeft, Ticket, Coffee, Gift, Tag, Check, QrCode } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';

interface PartnerVouchersViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

export const PartnerVouchersView: React.FC<PartnerVouchersViewProps> = ({
  onBack,
  onNavigateTab,
}) => {
  const { showToast } = useToast();
  const [selectedVoucher, setSelectedVoucher] = useState<{ id: string; title: string; code: string } | null>(null);

  const [vouchers, setVouchers] = useState([
    {
      id: 'v-1',
      title: 'Diskon Rp 50.000 Kafe Mitra',
      venue: 'CoffeeHouse Semarang & Resto Nusantara',
      desc: 'Berlaku untuk seluruh menu makanan & minuman dengan minimum transaksi Rp 100.000.',
      expiry: '31 Des 2026',
      code: 'MOREAI-KAFE50K',
      claimed: false,
    },
    {
      id: 'v-2',
      title: 'Diskon 20% Minuman Spesial Kopi',
      venue: 'Seluruh Gerai Kopi Mitra MoreAI',
      desc: 'Nikmati diskon 20% kopi artisan saat bekerja dengan AI Workspace di venue.',
      expiry: '15 Jan 2027',
      code: 'KOPI-AI20',
      claimed: true,
    },
    {
      id: 'v-3',
      title: 'Voucher Extra 25.000 Poin AI',
      venue: 'Ekosistem MoreAI',
      desc: 'Kredit AI tambahan untuk eksekusi deep research agent & visual marketing.',
      expiry: '28 Feb 2027',
      code: 'BONUS-AI25K',
      claimed: false,
    },
  ]);

  const handleClaim = (v: typeof vouchers[0]) => {
    setVouchers((prev) =>
      prev.map((item) => (item.id === v.id ? { ...item, claimed: true } : item))
    );
    setSelectedVoucher({ id: v.id, title: v.title, code: v.code });
    showToast(`Voucher "${v.title}" berhasil diklaim! Tunjukkan kode ke kasir.`, 'success');
  };

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <button onClick={onBack} className="p-1 rounded-lg text-slate-400 hover:text-slate-700">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="text-center">
          <span className="text-[10px] font-bold text-red-600 uppercase tracking-wider block">
            Sheet 5 Screen 12
          </span>
          <h1 className="text-sm sm:text-base font-bold text-slate-900 leading-tight">
            Voucher &amp; Diskon Mitra
          </h1>
        </div>
        <div className="w-5" />
      </div>

      {/* Top Banner */}
      <div className="p-5 rounded-3xl bg-gradient-to-r from-red-600 via-rose-600 to-amber-600 text-white shadow-xs space-y-1">
        <div className="flex items-center gap-1.5 text-xs text-amber-200 font-bold uppercase">
          <Gift className="w-4 h-4" />
          <span>Keuntungan Pengguna Wi-Fi</span>
        </div>
        <h2 className="text-base font-black">Spesial Mitra Tempat Nongkrong</h2>
        <p className="text-xs text-white/90">
          Klaim voucher potongan makan, minum, dan kredit token tambahan di ribuan kafe mitra.
        </p>
      </div>

      {/* Voucher Cards */}
      <div className="space-y-3">
        {vouchers.map((v) => (
          <div
            key={v.id}
            className="p-4 rounded-3xl bg-white border border-slate-100 shadow-xs space-y-3 text-xs"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-2xl bg-red-50 text-red-600 flex items-center justify-center shrink-0 mt-0.5">
                  <Coffee className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-xs sm:text-sm">{v.title}</h3>
                  <p className="text-[11px] font-medium text-red-600 mt-0.5">{v.venue}</p>
                  <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">{v.desc}</p>
                </div>
              </div>
            </div>

            <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
              <span className="text-[10px] text-slate-400">
                Berlaku hingga: <strong>{v.expiry}</strong>
              </span>

              {v.claimed ? (
                <button
                  onClick={() => setSelectedVoucher({ id: v.id, title: v.title, code: v.code })}
                  className="px-3 py-1.5 rounded-xl bg-slate-900 text-white font-bold text-xs flex items-center gap-1.5 shadow-2xs"
                >
                  <QrCode className="w-3.5 h-3.5" />
                  <span>Tampilkan Kode</span>
                </button>
              ) : (
                <button
                  onClick={() => handleClaim(v)}
                  className="px-3.5 py-1.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-xs shadow-xs active:scale-95 transition"
                >
                  Klaim Voucher
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Voucher Code QR Modal */}
      {selectedVoucher && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-fadeIn">
          <div className="w-full max-w-sm rounded-3xl bg-white p-6 shadow-2xl border border-slate-100 text-center space-y-3">
            <h3 className="text-sm font-bold text-slate-900">{selectedVoucher.title}</h3>
            <p className="text-xs text-slate-500">Tunjukkan barcode atau kode ini kepada kasir:</p>

            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200">
              <span className="font-mono text-lg font-black tracking-widest text-slate-900 block mb-2">
                {selectedVoucher.code}
              </span>
              <div className="w-32 h-32 bg-white rounded-xl mx-auto border border-slate-200 flex items-center justify-center p-2 shadow-2xs">
                {/* Visual Barcode / QR pattern */}
                <div className="grid grid-cols-4 gap-1 w-full h-full p-2 bg-slate-900 rounded-lg">
                  <div className="bg-white rounded-xs" />
                  <div className="bg-red-600 rounded-xs" />
                  <div className="bg-white rounded-xs" />
                  <div className="bg-white rounded-xs" />
                  <div className="bg-white rounded-xs" />
                  <div className="bg-white rounded-xs" />
                  <div className="bg-red-600 rounded-xs" />
                  <div className="bg-white rounded-xs" />
                </div>
              </div>
            </div>

            <button
              onClick={() => setSelectedVoucher(null)}
              className="w-full py-2.5 rounded-xl bg-slate-900 text-white font-bold text-xs"
            >
              Tutup Voucher
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
