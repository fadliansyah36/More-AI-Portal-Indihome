'use client';

import React, { useState } from 'react';
import { MoreAiLogo, GlobalPartnerLogo } from '@/components/branding/logos';
import { Eye, EyeOff, Lock, Mail, ArrowRight, ShieldCheck } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';

interface AuthLoginViewProps {
  onNavigate: (tab: NavigationTab) => void;
  onLoginSuccess: () => void;
}

export const AuthLoginView: React.FC<AuthLoginViewProps> = ({
  onNavigate,
  onLoginSuccess,
}) => {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<'masuk' | 'daftar'>('masuk');
  const [emailOrPhone, setEmailOrPhone] = useState('andipratama@email.com');
  const [password, setPassword] = useState('Password2026!');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onLoginSuccess();
    onNavigate('home');
  };

  return (
    <div className="min-h-[680px] flex flex-col justify-between py-6 px-4 bg-white rounded-3xl animate-fadeIn">
      {/* Brand Header */}
      <div className="pt-4 flex flex-col items-center">
        <MoreAiLogo className="justify-center" />
        <span className="text-[11px] font-medium text-slate-400 mt-2">
          Masuk ke Akun AI Workspace Anda
        </span>
      </div>

      {/* Main Form Container (Exact layout from Sheet 6 Screen 3) */}
      <div className="my-auto py-2">
        {/* Masuk vs Daftar Tabs */}
        <div className="flex border-b border-slate-200 mb-5">
          <button
            onClick={() => setActiveTab('masuk')}
            className={`flex-1 pb-3 text-xs sm:text-sm font-bold transition relative ${
              activeTab === 'masuk' ? 'text-red-600' : 'text-slate-400 hover:text-slate-600'
            }`}
          >
            Masuk
            {activeTab === 'masuk' && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-red-600 rounded-full" />
            )}
          </button>
          <button
            onClick={() => onNavigate('register')}
            className={`flex-1 pb-3 text-xs sm:text-sm font-bold transition relative ${
              activeTab === 'daftar' ? 'text-red-600' : 'text-slate-400 hover:text-slate-600'
            }`}
          >
            Daftar
            {activeTab === 'daftar' && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-red-600 rounded-full" />
            )}
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3.5">
          <div>
            <label className="text-[11px] font-semibold text-slate-700 block mb-1">
              Email atau nomor HP
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={emailOrPhone}
                onChange={(e) => setEmailOrPhone(e.target.value)}
                placeholder="email@domain.com atau 0812..."
                className="w-full text-xs sm:text-sm pl-10 pr-4 py-2.5 rounded-2xl bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500 transition"
              />
            </div>
          </div>

          <div>
            <label className="text-[11px] font-semibold text-slate-700 block mb-1">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Masukkan kata sandi..."
                className="w-full text-xs sm:text-sm pl-10 pr-10 py-2.5 rounded-2xl bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500 transition"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Ingat Saya & Lupa Password */}
          <div className="flex items-center justify-between text-xs pt-1">
            <label className="flex items-center gap-2 cursor-pointer text-slate-600 font-medium">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="w-4 h-4 rounded text-red-600 focus:ring-red-500"
              />
              <span>Ingat saya</span>
            </label>

            <button
              type="button"
              onClick={() => showToast('Tautan pemulihan kata sandi telah dikirim ke email terdaftar.', 'info')}
              className="text-slate-500 hover:text-red-600 transition"
            >
              Lupa password?
            </button>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 active:scale-95 text-white text-xs sm:text-sm font-bold transition shadow-xs mt-2"
          >
            Masuk dengan akun
          </button>
        </form>

        {/* Separator 'atau' */}
        <div className="relative my-4 text-center">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-slate-200" />
          </div>
          <span className="relative bg-white px-3 text-[11px] text-slate-400 font-semibold uppercase tracking-wider">
            atau
          </span>
        </div>

        {/* 3 Social SSO Buttons (Google, Apple, Global Partner ISP SSO) */}
        <div className="flex items-center justify-center gap-3">
          {/* Google */}
          <button
            onClick={() => onLoginSuccess()}
            className="w-12 h-12 rounded-2xl border border-slate-200 bg-white hover:bg-slate-50 flex items-center justify-center shadow-2xs active:scale-95 transition"
            title="Masuk dengan Google"
          >
            <span className="font-bold text-base text-red-500">G</span>
          </button>

          {/* Apple */}
          <button
            onClick={() => onLoginSuccess()}
            className="w-12 h-12 rounded-2xl border border-slate-200 bg-white hover:bg-slate-50 flex items-center justify-center shadow-2xs active:scale-95 transition"
            title="Masuk dengan Apple"
          >
            <span className="font-black text-base text-slate-900"></span>
          </button>

          {/* Global Partner ISP SSO */}
          <button
            onClick={() => onLoginSuccess()}
            className="w-12 h-12 rounded-2xl border border-blue-200 bg-blue-50/60 hover:bg-blue-100/70 flex items-center justify-center shadow-2xs active:scale-95 transition"
            title="Masuk dengan Global Partner ISP ID"
          >
            <span className="font-black text-xs text-blue-600">ISP</span>
          </button>
        </div>
      </div>

      {/* Footer Switcher */}
      <div className="text-center text-xs text-slate-500 pt-2 border-t border-slate-100">
        Belum punya akun?{' '}
        <button
          onClick={() => onNavigate('register')}
          className="font-bold text-red-600 hover:text-red-700 hover:underline"
        >
          Daftar Sekarang
        </button>
      </div>
    </div>
  );
};
