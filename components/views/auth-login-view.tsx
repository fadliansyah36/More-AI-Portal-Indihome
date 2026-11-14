'use client';

import React, { useState } from 'react';
import { MoreAiLogo, GlobalPartnerLogo } from '@/components/branding/logos';
import { Eye, EyeOff, Lock, Mail, ArrowRight, ShieldCheck } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';
import { createSupabaseBrowserClient } from '@/lib/supabase/client';

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
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;
    const normalizedEmail = email.trim().toLowerCase();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail) || !password) {
      showToast('Masukkan email dan password yang valid.', 'error');
      return;
    }
    setIsSubmitting(true);
    try {
      const supabase = createSupabaseBrowserClient();
      const { data, error } = await supabase.auth.signInWithPassword({ email: normalizedEmail, password });
      if (error) {
        const message = error.message.toLowerCase();
        const code = 'code' in error && typeof error.code === 'string' ? error.code.toLowerCase() : '';
        if (code === 'email_not_confirmed' || message.includes('email not confirmed')) {
          showToast('Email akun belum dikonfirmasi. Periksa inbox/spam atau minta tautan konfirmasi baru sebelum masuk.', 'error');
          return;
        }
        if (code === 'user_banned' || message.includes('user is banned')) {
          showToast('Akun ini sedang dinonaktifkan. Hubungi dukungan MoreAI untuk pemeriksaan akses.', 'error');
          return;
        }
        if (code.includes('rate_limit') || message.includes('rate limit') || message.includes('too many')) {
          showToast('Terlalu banyak percobaan login. Tunggu beberapa saat lalu coba kembali.', 'error');
          return;
        }
        if (code === 'invalid_credentials' || message.includes('invalid login credentials')) {
          showToast('Supabase Auth tidak menemukan pasangan email dan password yang valid. Pastikan email yang digunakan sama dengan email saat pendaftaran, lalu gunakan Lupa password jika perlu membuat ulang password.', 'error');
          return;
        }
        if (message.includes('network') || message.includes('fetch') || message.includes('timeout')) {
          showToast('Tidak dapat menghubungi Supabase Auth. Periksa koneksi dan konfigurasi URL Auth, lalu coba kembali.', 'error');
          return;
        }
        showToast('Login ditolak oleh Supabase Auth: ' + error.message, 'error');
        return;
      }
      if (!data.session) {
        showToast('Login belum berhasil. Silakan coba kembali.', 'error');
        return;
      }
      onLoginSuccess();
      onNavigate('home');
    } catch (cause) {
      showToast(cause instanceof Error ? cause.message : 'Layanan login sedang tidak tersedia. Silakan coba kembali.', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOAuth = async (provider: 'google' | 'apple') => {
    try {
      const supabase = createSupabaseBrowserClient();
      const { error } = await supabase.auth.signInWithOAuth({
        provider,
        options: { redirectTo: window.location.origin },
      });
      if (error) throw error;
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Login sosial belum tersedia.', 'error');
    }
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
              Email
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="nama@email.com"
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
                autoComplete="current-password"
                required
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
              onClick={async () => {
                const identifier = email.trim().toLowerCase();
                if (!identifier.includes('@')) {
                  showToast('Masukkan alamat email untuk mengirim tautan pemulihan password.', 'info');
                  return;
                }
                try {
                  const { error } = await createSupabaseBrowserClient().auth.resetPasswordForEmail(identifier, {
                    redirectTo: window.location.origin + '/?view=login',
                  });
                  if (error) throw error;
                  showToast('Jika email terdaftar, tautan pemulihan akan dikirim oleh Supabase Auth.', 'success');
                } catch (error) {
                  showToast(error instanceof Error ? error.message : 'Permintaan pemulihan gagal.', 'error');
                }
              }}
              className="text-slate-500 hover:text-red-600 transition"
            >
              Lupa password?
            </button>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 active:scale-95 text-white text-xs sm:text-sm font-bold transition shadow-xs mt-2 disabled:opacity-50"
          >
            {isSubmitting ? 'Memproses...' : 'Masuk dengan akun'}
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
            onClick={() => void handleOAuth('google')}
            className="w-12 h-12 rounded-2xl border border-slate-200 bg-white hover:bg-slate-50 flex items-center justify-center shadow-2xs active:scale-95 transition"
            title="Masuk dengan Google"
          >
            <span className="font-bold text-base text-red-500">G</span>
          </button>

          {/* Apple */}
          <button
            onClick={() => void handleOAuth('apple')}
            className="w-12 h-12 rounded-2xl border border-slate-200 bg-white hover:bg-slate-50 flex items-center justify-center shadow-2xs active:scale-95 transition"
            title="Masuk dengan Apple"
          >
            <span className="font-black text-base text-slate-900"></span>
          </button>

          {/* Global Partner ISP SSO */}
          <button
            onClick={() => showToast('Single Sign-On Global Partner ISP belum dikonfigurasi pada Supabase Auth.', 'info')}
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
