'use client';

import React, { useState } from 'react';
import { ArrowLeft, Building2, Lock, Mail, ShieldCheck, ArrowRight } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';
import { MoreAiLogo, IndiHomeLogo } from '@/components/branding/logos';

interface PartnerLoginViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

export const PartnerLoginView: React.FC<PartnerLoginViewProps> = ({
  onBack,
  onNavigateTab,
}) => {
  const { showToast } = useToast();
  const [email, setEmail] = useState('farhan@coffeehouse.id');
  const [password, setPassword] = useState('Partner2026!');
  const [partnerMode, setPartnerMode] = useState<'login' | 'register'>('login');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    showToast('Login mitra B2B berhasil! Membuka Dashboard Partner...', 'success');
    onNavigateTab('partner');
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
            Sheet 4 Screen 1
          </span>
          <h1 className="text-sm sm:text-base font-bold text-slate-900 leading-tight">
            Portal Mitra Venue (B2B)
          </h1>
        </div>
        <div className="w-5" />
      </div>

      {/* Hero Badge */}
      <div className="p-6 rounded-3xl bg-white border border-slate-100 shadow-xs text-center space-y-3">
        <div className="w-14 h-14 rounded-2xl bg-red-600 text-white flex items-center justify-center mx-auto shadow-md">
          <Building2 className="w-7 h-7" />
        </div>
        <div>
          <h2 className="text-base font-black text-slate-900">MoreAI Partner Wi-Fi &amp; AI</h2>
          <p className="text-xs text-slate-500 mt-1 max-w-xs mx-auto">
            Solusi konektivitas Wi-Fi venue, kuota sponsor AI untuk pelanggan, dan analisis kunjungan.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex p-1 bg-slate-100 rounded-2xl text-xs font-bold text-slate-600">
          <button
            onClick={() => setPartnerMode('login')}
            className={`flex-1 py-2 rounded-xl transition ${
              partnerMode === 'login' ? 'bg-white text-red-600 shadow-xs' : 'hover:text-slate-900'
            }`}
          >
            Masuk Mitra
          </button>
          <button
            onClick={() => setPartnerMode('register')}
            className={`flex-1 py-2 rounded-xl transition ${
              partnerMode === 'register' ? 'bg-white text-red-600 shadow-xs' : 'hover:text-slate-900'
            }`}
          >
            Daftar Venue Baru
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-3 text-left pt-2">
          <div>
            <label className="text-[11px] font-bold text-slate-700 block mb-1">
              Email Bisnis / ID Mitra IndiHome
            </label>
            <div className="flex items-center gap-2 p-3 rounded-2xl bg-slate-50 border border-slate-200 focus-within:border-red-500 focus-within:bg-white transition">
              <Mail className="w-4 h-4 text-slate-400" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="nama@bisnis.com"
                className="w-full bg-transparent text-xs text-slate-900 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="text-[11px] font-bold text-slate-700 block mb-1">
              Kata Sandi Portal
            </label>
            <div className="flex items-center gap-2 p-3 rounded-2xl bg-slate-50 border border-slate-200 focus-within:border-red-500 focus-within:bg-white transition">
              <Lock className="w-4 h-4 text-slate-400" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full bg-transparent text-xs text-slate-900 focus:outline-none"
              />
            </div>
          </div>

          <button
            type="submit"
            className="w-full py-3.5 rounded-2xl bg-red-600 hover:bg-red-700 active:scale-95 text-white font-bold text-xs transition shadow-xs mt-3 flex items-center justify-center gap-2"
          >
            <span>{partnerMode === 'login' ? 'Masuk ke Dashboard Partner' : 'Daftarkan Venue'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>
      </div>

      {/* Info Card */}
      <div className="p-4 rounded-3xl bg-slate-50 border border-slate-100 flex items-start gap-3 text-xs text-slate-600">
        <ShieldCheck className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
        <div>
          <strong className="text-slate-900 block mb-0.5">Integrasi Jaringan Resmi</strong>
          Mendukung gateway MikroTik Hotspot, UniFi OS, dan Router Fiber IndiHome secara native.
        </div>
      </div>
    </div>
  );
};
