'use client';

import React, { useState } from 'react';
import { ArrowLeft, KeyRound, Smartphone, CheckCircle2, RotateCcw } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';

interface CaptiveOtpViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

export const CaptiveOtpView: React.FC<CaptiveOtpViewProps> = ({
  onBack,
  onNavigateTab,
}) => {
  const { showToast } = useToast();
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [phone] = useState('');

  const handleDigitChange = (index: number, val: string) => {
    if (val.length > 1) val = val.slice(-1);
    const newOtp = [...otp];
    newOtp[index] = val;
    setOtp(newOtp);

    // Auto focus next
    if (val && index < 5) {
      const nextInput = document.getElementById(`otp-input-${index + 1}`);
      nextInput?.focus();
    }
  };

  const handleVerify = () => {
    showToast('Verifikasi OTP belum terhubung ke layanan gateway. Tidak ada sesi Wi-Fi yang dibuat.', 'error');
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
            Sheet 3 Screen 4
          </span>
          <h1 className="text-sm sm:text-base font-bold text-slate-900 leading-tight">
            Verifikasi Kode OTP
          </h1>
        </div>
        <div className="w-5" />
      </div>

      {/* Hero Badge */}
      <div className="p-5 rounded-3xl bg-white border border-slate-100 shadow-xs text-center space-y-3">
        <div className="w-12 h-12 rounded-2xl bg-red-50 text-red-600 flex items-center justify-center mx-auto shadow-2xs">
          <KeyRound className="w-6 h-6" />
        </div>
        <div>
          <h2 className="text-base font-bold text-slate-900">Masukkan 6 Digit OTP</h2>
          <p className="text-xs text-slate-500 mt-1 max-w-xs mx-auto">
            Pengiriman OTP belum terhubung ke layanan gateway. Nomor tujuan belum tersedia dari backend:
          </p>
          <span className="text-xs font-mono font-bold text-slate-800 bg-slate-100 px-3 py-1 rounded-full inline-block mt-2">
            {phone || 'Nomor belum tersedia'}
          </span>
        </div>

        {/* 6 Digit Input Boxes */}
        <div className="flex justify-center gap-2 pt-2">
          {otp.map((digit, idx) => (
            <input
              key={idx}
              id={`otp-input-${idx}`}
              type="text"
              inputMode="numeric"
              maxLength={1}
              value={digit}
              onChange={(e) => handleDigitChange(idx, e.target.value)}
              disabled
              className="w-10 sm:w-12 h-12 sm:h-14 text-center font-mono font-black text-lg sm:text-xl rounded-2xl border border-slate-200 focus:border-red-500 focus:ring-2 focus:ring-red-500/20 bg-slate-50 focus:bg-white transition"
            />
          ))}
        </div>

        <div className="pt-2 text-left text-[11px] text-amber-800 bg-amber-50 border border-amber-200 rounded-xl p-3">
          Verifikasi OTP dinonaktifkan sampai endpoint pengiriman dan validasi OTP dari gateway terintegrasi. Kode demo tidak digunakan.
        </div>

        <button
          onClick={handleVerify}
          disabled
          className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 active:scale-95 text-white font-bold text-xs transition shadow-xs mt-3"
        >
          Verifikasi &amp; Hubungkan Wi-Fi
        </button>
      </div>

      {/* Help Note */}
      <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-100 text-center text-xs text-slate-500">
        Belum menerima kode? Periksa sinyal seluler Anda atau hubungi kasir/staf venue untuk kode voucher alternatif.
      </div>
    </div>
  );
};
