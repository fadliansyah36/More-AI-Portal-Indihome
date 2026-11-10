'use client';

import React, { useState } from 'react';
import { MoreAiLogo, GlobalPartnerLogo } from '@/components/branding/logos';
import { ArrowLeft, User, Mail, Phone, Lock, Eye, EyeOff } from 'lucide-react';
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
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [agreed, setAgreed] = useState(true);
  const { showToast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!agreed) return;
    try {
      const supabase = createSupabaseBrowserClient();
      const { data, error } = await supabase.auth.signUp({
        email: email.trim(),
        password,
        options: {
          data: { full_name: fullName.trim(), phone: phone.trim() },
          emailRedirectTo: window.location.origin,
        },
      });
      if (error) throw error;
      if (data.session) {
        onRegisterSuccess();
        onNavigate('welcome_success');
      } else {
        showToast('Pendaftaran diterima. Silakan verifikasi email untuk mengaktifkan akun.', 'success');
        onNavigate('login');
      }
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Pendaftaran gagal. Periksa kembali data Anda.', 'error');
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
              Nomor HP (WhatsApp) *
            </label>
            <div className="relative">
              <Phone className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="0812 3456 7890"
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
                placeholder="Minimal 8 karakter..."
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
            disabled={!agreed}
            className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 disabled:opacity-40 text-white text-xs font-bold transition shadow-xs mt-2"
          >
            Daftar Sekarang
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
