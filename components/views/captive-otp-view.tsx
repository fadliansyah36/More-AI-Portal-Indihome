'use client';

import React, { useState, useEffect } from 'react';
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
  const [timer, setTimer] = useState(45);
  const [phone, setPhone] = useState('+62 812-3456-7890');

  useEffect(() => {
    if (timer > 0) {
      const interval = setInterval(() => setTimer((t) => t - 1), 1000);
      return () => clearInterval(interval);
    }
  }, [timer]);

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

  const handleAutoFill = () => {
    setOtp(['8', '4', '2', '1', '9', '6']);
    showToast('Kode OTP berhasil dimasukkan otomatis untuk simulasi.', 'info');
  };

  const handleVerify = () => {
    const code = otp.join('');
    if (code.length < 6) {
      showToast('Masukkan 6 digit kode verifikasi lengkap.', 'error');
      return;
    }
    showToast('Verifikasi berhasil! Menghubungkan perangkat ke Wi-Fi...', 'success');
    setTimeout(() => {
      onNavigateTab('captive_success');
    }, 600);
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
            Kode verifikasi telah dikirimkan via WhatsApp / SMS ke nomor:
          </p>
          <span className="text-xs font-mono font-bold text-slate-800 bg-slate-100 px-3 py-1 rounded-full inline-block mt-2">
            {phone}
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
              className="w-10 sm:w-12 h-12 sm:h-14 text-center font-mono font-black text-lg sm:text-xl rounded-2xl border border-slate-200 focus:border-red-500 focus:ring-2 focus:ring-red-500/20 bg-slate-50 focus:bg-white transition"
            />
          ))}
        </div>

        {/* Resend Timer & Quick Fill */}
        <div className="pt-2 flex items-center justify-between text-xs text-slate-500 px-2">
          <span>
            {timer > 0 ? (
              <>Kirim ulang dalam <strong className="text-slate-800 font-mono">00:{timer < 10 ? `0${timer}` : timer}</strong></>
            ) : (
              <button
                onClick={() => {
                  setTimer(45);
                  showToast('Kode OTP baru telah dikirimkan kembali.', 'info');
                }}
                className="text-red-600 font-bold hover:underline"
              >
                Kirim Ulang Kode Sekarang
              </button>
            )}
          </span>

          <button
            onClick={handleAutoFill}
            className="text-[11px] font-semibold text-red-600 hover:text-red-700 bg-red-50 px-2.5 py-1 rounded-lg"
          >
            Auto-Isi Demo
          </button>
        </div>

        <button
          onClick={handleVerify}
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
