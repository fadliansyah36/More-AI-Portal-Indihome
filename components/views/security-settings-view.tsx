'use client';

import React, { useState } from 'react';
import { ArrowLeft, Shield, Lock, Smartphone, Key, LogOut, CheckCircle2, AlertTriangle } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';
import { createSupabaseBrowserClient } from '@/lib/supabase/client';

interface SecuritySettingsViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

export const SecuritySettingsView: React.FC<SecuritySettingsViewProps> = ({
  onBack,
  onNavigateTab,
}) => {
  const { showToast } = useToast();
  const [twoFactorAuth, setTwoFactorAuth] = useState(true);
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');

  const [activeSessions, setActiveSessions] = useState([
    {
      id: 'dev-1',
      device: 'iPhone 15 Pro Max',
      browser: 'Safari Mobile PWA',
      location: 'Jakarta, Indonesia',
      status: 'Sesi Ini (Aktif)',
      isCurrent: true,
    },
    {
      id: 'dev-2',
      device: 'MacBook Pro 16"',
      browser: 'Chrome 130 macOS',
      location: 'Semarang, Indonesia',
      status: 'Aktif 2 jam lalu',
      isCurrent: false,
    },
  ]);

  const toggle2FA = () => {
    const nextState = !twoFactorAuth;
    setTwoFactorAuth(nextState);
    showToast(
      nextState
        ? 'Autentikasi Dua Faktor (2FA) berhasil diaktifkan!'
        : '2FA dinonaktifkan.',
      'info'
    );
  };

  const handleUpdatePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPassword || newPassword.length < 8) {
      showToast('Kata sandi baru minimal 8 karakter.', 'error');
      return;
    }
    try {
      const supabase = createSupabaseBrowserClient();
      const { data: userData, error: userError } = await supabase.auth.getUser();
      if (userError || !userData.user?.email) throw new Error('Sesi pengguna tidak valid. Silakan login kembali.');
      const { error: reauthError } = await supabase.auth.signInWithPassword({
        email: userData.user.email,
        password: oldPassword,
      });
      if (reauthError) throw new Error('Kata sandi saat ini tidak benar.');
      const { error: updateError } = await supabase.auth.updateUser({ password: newPassword });
      if (updateError) throw updateError;
      showToast('Kata sandi akun berhasil diperbarui.', 'success');
      setOldPassword('');
      setNewPassword('');
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Kata sandi gagal diperbarui.', 'error');
    }
  };

  const handleRevokeOtherSessions = async () => {
    try {
      const { error } = await createSupabaseBrowserClient().auth.signOut({ scope: 'global' });
      if (error) throw error;
      setActiveSessions([]);
      showToast('Semua sesi telah dicabut. Silakan login kembali.', 'success');
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Sesi perangkat gagal dicabut.', 'error');
    }
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
            Sheet 5 Screen 14
          </span>
          <h1 className="text-sm sm:text-base font-bold text-slate-900 leading-tight">
            Keamanan &amp; Sesi Akun
          </h1>
        </div>
        <div className="w-5" />
      </div>

      {/* 2FA Toggle Card */}
      <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-slate-900">Autentikasi 2 Langkah (2FA)</h3>
              <p className="text-[10px] text-slate-500 mt-0.5">Kode OTP WhatsApp / SMS saat login</p>
            </div>
          </div>

          <button
            onClick={toggle2FA}
            className={`w-12 h-6 rounded-full p-1 transition duration-200 ease-in-out ${
              twoFactorAuth ? 'bg-emerald-600' : 'bg-slate-300'
            }`}
          >
            <div
              className={`w-4 h-4 rounded-full bg-white transition duration-200 ease-in-out ${
                twoFactorAuth ? 'translate-x-6' : 'translate-x-0'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Change Password Form */}
      <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-xs space-y-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-red-50 text-red-600 flex items-center justify-center">
            <Lock className="w-4 h-4" />
          </div>
          <h3 className="text-xs font-bold text-slate-900">Ubah Kata Sandi</h3>
        </div>

        <form onSubmit={handleUpdatePassword} className="space-y-2 text-xs">
          <div>
            <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">
              Kata Sandi Saat Ini
            </label>
            <input
              type="password"
              value={oldPassword}
              onChange={(e) => setOldPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 focus:bg-white focus:outline-none"
            />
          </div>

          <div>
            <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">
              Kata Sandi Baru
            </label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Minimal 8 karakter"
              className="w-full p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 focus:bg-white focus:outline-none"
            />
          </div>

          <button
            type="submit"
            className="w-full py-2.5 rounded-xl bg-slate-900 text-white font-bold text-xs hover:bg-slate-800 transition mt-2 shadow-xs"
          >
            Perbarui Kata Sandi
          </button>
        </form>
      </div>

      {/* Active Sessions */}
      <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            Sesi Perangkat Aktif
          </h3>
          <span className="text-[10px] text-slate-400 font-semibold">2 Perangkat</span>
        </div>

        <div className="space-y-2">
          {activeSessions.map((sess) => (
            <div
              key={sess.id}
              className="p-3 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-between text-xs"
            >
              <div className="flex items-center gap-2.5">
                <Smartphone className="w-4 h-4 text-slate-600" />
                <div>
                  <span className="font-bold text-slate-900 block">{sess.device}</span>
                  <span className="text-[10px] text-slate-400">{sess.browser} • {sess.location}</span>
                </div>
              </div>
              <span
                className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${
                  sess.isCurrent ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-200 text-slate-600'
                }`}
              >
                {sess.status}
              </span>
            </div>
          ))}
        </div>

        <button
          onClick={handleRevokeOtherSessions}
          className="w-full py-2.5 rounded-xl border border-red-200 text-red-600 hover:bg-red-50 font-bold text-xs transition"
        >
          Keluar dari Sesi Lainnya
        </button>
      </div>
    </div>
  );
};
