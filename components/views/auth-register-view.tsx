'use client';

import React, { useState } from 'react';
import { MoreAiLogo, GlobalPartnerLogo } from '@/components/branding/logos';
import { ArrowLeft, User, Mail, Lock, Eye, EyeOff } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';
import { createSupabaseBrowserClient } from '@/lib/supabase/client';

interface AuthRegisterViewProps {
  onNavigate: (tab: NavigationTab) => void;
  onRegisterSuccess: () => void;
}

export const AuthRegisterView: React.FC<AuthRegisterViewProps> = ({
  onNavigate,
  onRegisterSuccess,
}) => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [agreed, setAgreed] = useState(true);
  const { showToast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!agreed || isSubmitting) return;
    const normalizedName = fullName.trim().replace(/\s+/g, ' ');
    const normalizedEmail = email.trim().toLowerCase();
    if (normalizedName.length < 2 || normalizedName.length > 80) {
      showToast('Nama lengkap harus terdiri dari 2–80 karakter.', 'error');
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail)) {
      showToast('Format email tidak valid.', 'error');
      return;
    }
    if (password.length < 12 || password.length > 128 || !/[a-z]/.test(password) || !/[A-Z]/.test(password) || !/[0-9]/.test(password) || !/[^A-Za-z0-9]/.test(password)) {
      showToast('Password minimal 12 karakter dan harus memuat huruf besar, huruf kecil, angka, serta simbol.', 'error');
      return;
    }
    setIsSubmitting(true);
    try {
      const supabase = createSupabaseBrowserClient();
      const { data, error } = await supabase.auth.signUp({
        email: normalizedEmail,
        password,
        options: { data: { full_name: normalizedName } },
      });
      if (error) {
        const message = error.message.toLowerCase();
        if (message.includes('already registered') || message.includes('already exists')) {
          throw new Error('Email sudah terdaftar. Silakan masuk atau gunakan fitur lupa password.');
        }
        if (message.includes('password')) throw new Error('Password belum memenuhi kebijakan keamanan.');
        if (message.includes('rate limit') || message.includes('too many')) {
          throw new Error('Terlalu banyak percobaan. Silakan tunggu beberapa saat sebelum mencoba kembali.');
        }
        throw new Error('Pendaftaran gagal. Periksa email dan password, lalu coba kembali.');
      }
      if (!data.user) throw new Error('Akun belum berhasil dibuat. Silakan coba kembali.');
      if (!data.session) {
        showToast('Akun berhasil dibuat, tetapi login otomatis belum aktif. Admin perlu menonaktifkan Confirm Email di Supabase Auth.', 'error');
        return;
      }
      onRegisterSuccess();
      onNavigate('welcome_success');
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Pendaftaran gagal. Periksa kembali data Anda.', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-[680px] flex flex-col justify-between py-6 px-4 bg-white rounded-3xl animate-fadeIn">
      {/* Top Bar */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <button
          onClick={() => onNavigate('login')}
          className="p-1 rounded-lg text-slate-400 hover:text-slate-700"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <MoreAiLogo />
        <div className="w-5" />
      </div>

      {/* Main Registration Form (Sheet 5 Screen 2) */}
      <div className="my-auto py-2">
        <div className="text-center mb-4">
          <h2 className="text-lg font-black text-slate-900 tracking-tight">Daftar Akun Baru</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Buat akun untuk mengakses seluruh layanan MoreAI &amp; Global Partner ISP/Network
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="text-[11px] font-semibold text-slate-700 block mb-1">
              Nama Lengkap *
            </label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Contoh: Andi Pratama"
                required
                className="w-full text-xs pl-10 pr-4 py-2.5 rounded-2xl bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500 transition"
              />
            </div>
          </div>

          <div>
            <label className="text-[11px] font-semibold text-slate-700 block mb-1">
              Email *
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="nama@email.com"
                required
                className="w-full text-xs pl-10 pr-4 py-2.5 rounded-2xl bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500 transition"
              />
            </div>
          </div>

          <div>
            <label className="text-[11px] font-semibold text-slate-700 block mb-1">
              Buat Password *
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Minimal 12 karakter, huruf/angka/simbol..."
                required
                className="w-full text-xs pl-10 pr-10 py-2.5 rounded-2xl bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500 transition"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 p-1"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <label className="flex items-start gap-2 pt-1 cursor-pointer text-[11px] text-slate-600">
            <input
              type="checkbox"
              checked={agreed}
              onChange={(e) => setAgreed(e.target.checked)}
              className="w-4 h-4 rounded text-red-600 focus:ring-red-500 mt-0.5"
            />
            <span>
              Saya setuju dengan <strong>Syarat &amp; Ketentuan</strong> dan <strong>Kebijakan Privasi</strong> MoreAI &amp; Global Partner ISP/Network.
            </span>
          </label>

          <button
            type="submit"
            disabled={!agreed || isSubmitting}
            className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 disabled:opacity-40 text-white text-xs font-bold transition shadow-xs mt-2"
          >
            {isSubmitting ? 'Memproses...' : 'Daftar Sekarang'}
          </button>
        </form>
      </div>

      {/* Switch to Login */}
      <div className="text-center text-xs text-slate-500 pt-2 border-t border-slate-100">
        Sudah punya akun?{' '}
        <button
          onClick={() => onNavigate('login')}
          className="font-bold text-red-600 hover:text-red-700 hover:underline"
        >
          Masuk di Sini
        </button>
      </div>
    </div>
  );
};
