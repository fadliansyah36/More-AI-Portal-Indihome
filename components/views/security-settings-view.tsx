'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { ArrowLeft, Shield, Lock, LogOut } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';
import { createSupabaseBrowserClient } from '@/lib/supabase/client';

interface SecuritySettingsViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

type MfaFactor = {
  id: string;
  friendly_name: string | null;
  factor_type: string;
  status: string;
};

type TotpEnrollment = {
  id: string;
  qr_code: string;
  secret: string;
  uri: string;
};

export const SecuritySettingsView: React.FC<SecuritySettingsViewProps> = ({
  onBack,
}) => {
  const { showToast } = useToast();
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [factors, setFactors] = useState<MfaFactor[]>([]);
  const [enrollment, setEnrollment] = useState<TotpEnrollment | null>(null);
  const [verifyCode, setVerifyCode] = useState('');
  const [loadingFactors, setLoadingFactors] = useState(true);
  const [mfaBusy, setMfaBusy] = useState(false);
  const [removingFactor, setRemovingFactor] = useState<string | null>(null);

  const loadFactors = useCallback(async () => {
    setLoadingFactors(true);
    try {
      const { data, error } = await createSupabaseBrowserClient().auth.mfa.listFactors();
      if (error) throw error;
      setFactors([...data.totp, ...data.phone].map((factor) => ({
        id: factor.id,
        friendly_name: factor.friendly_name ?? null,
        factor_type: factor.factor_type,
        status: factor.status,
      })));
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Status MFA tidak dapat dimuat.', 'error');
    } finally {
      setLoadingFactors(false);
    }
  }, [showToast]);

  useEffect(() => {
    void loadFactors();
  }, [loadFactors]);

  const verifiedTotp = factors.filter((factor) => factor.factor_type === 'totp' && factor.status === 'verified');

  const handleEnrollTotp = async () => {
    setMfaBusy(true);
    try {
      const { data, error } = await createSupabaseBrowserClient().auth.mfa.enroll({
        factorType: 'totp',
        friendlyName: 'MoreAI Authenticator',
      });
      if (error) throw error;
      setEnrollment({
        id: data.id,
        qr_code: data.totp.qr_code,
        secret: data.totp.secret,
        uri: data.totp.uri,
      });
      setVerifyCode('');
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Pendaftaran authenticator gagal dimulai.', 'error');
    } finally {
      setMfaBusy(false);
    }
  };

  const handleVerifyTotp = async () => {
    if (!enrollment || !/^\d{6,8}$/.test(verifyCode.trim())) {
      showToast('Masukkan kode authenticator 6–8 digit.', 'error');
      return;
    }
    setMfaBusy(true);
    try {
      const supabase = createSupabaseBrowserClient();
      const challenge = await supabase.auth.mfa.challenge({ factorId: enrollment.id });
      if (challenge.error) throw challenge.error;
      const verified = await supabase.auth.mfa.verify({
        factorId: enrollment.id,
        challengeId: challenge.data.id,
        code: verifyCode.trim(),
      });
      if (verified.error) throw verified.error;
      setEnrollment(null);
      setVerifyCode('');
      await loadFactors();
      showToast('Authenticator TOTP berhasil diverifikasi dan diaktifkan.', 'success');
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Verifikasi kode authenticator gagal.', 'error');
    } finally {
      setMfaBusy(false);
    }
  };

  const handleCancelEnrollment = async () => {
    if (!enrollment) return;
    setMfaBusy(true);
    try {
      const { error } = await createSupabaseBrowserClient().auth.mfa.unenroll({ factorId: enrollment.id });
      if (error) throw error;
      setEnrollment(null);
      setVerifyCode('');
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Pendaftaran authenticator gagal dibatalkan.', 'error');
    } finally {
      setMfaBusy(false);
    }
  };

  const handleRemoveFactor = async (factorId: string) => {
    setRemovingFactor(factorId);
    try {
      const { error } = await createSupabaseBrowserClient().auth.mfa.unenroll({ factorId });
      if (error) throw error;
      await createSupabaseBrowserClient().auth.refreshSession();
      await loadFactors();
      showToast('Faktor autentikasi berhasil dihapus.', 'success');
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Faktor autentikasi gagal dihapus.', 'error');
    } finally {
      setRemovingFactor(null);
    }
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

  const handleRevokeAllSessions = async () => {
    try {
      const { error } = await createSupabaseBrowserClient().auth.signOut({ scope: 'global' });
      if (error) throw error;
      showToast('Permintaan pencabutan seluruh sesi berhasil. Silakan login kembali.', 'success');
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Sesi perangkat gagal dicabut.', 'error');
    }
  };

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <button onClick={onBack} className="p-1 rounded-lg text-slate-400 hover:text-slate-700">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="text-center">
          <span className="text-[10px] font-bold text-red-600 uppercase tracking-wider block">Sheet 5 Screen 14</span>
          <h1 className="text-sm sm:text-base font-bold text-slate-900 leading-tight">Keamanan &amp; Sesi Akun</h1>
        </div>
        <div className="w-5" />
      </div>

      <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-xs space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-slate-900">Autentikasi 2 Langkah (2FA)</h3>
              <p className="text-[10px] text-slate-500 mt-0.5">
                {loadingFactors ? 'Memuat status authenticator…' : verifiedTotp.length > 0 ? 'Authenticator TOTP aktif' : 'Belum ada authenticator TOTP terverifikasi'}
              </p>
            </div>
          </div>
          <span className={`text-[10px] font-bold px-2 py-1 rounded-full ${verifiedTotp.length ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>
            {loadingFactors ? 'Memuat' : verifiedTotp.length ? 'Aktif' : 'Nonaktif'}
          </span>
        </div>

        <div className="space-y-2">
          {factors.map((factor) => (
            <div key={factor.id} className="flex items-center justify-between gap-3 rounded-xl border border-slate-100 bg-slate-50 p-3">
              <div className="min-w-0">
                <p className="text-xs font-semibold text-slate-800">{factor.friendly_name || (factor.factor_type === 'totp' ? 'Authenticator App' : 'Phone factor')}</p>
                <p className="text-[10px] text-slate-500">{factor.factor_type.toUpperCase()} · {factor.status}</p>
              </div>
              <button
                type="button"
                onClick={() => void handleRemoveFactor(factor.id)}
                disabled={removingFactor === factor.id || factor.status !== 'verified'}
                className="text-[10px] font-bold text-red-600 disabled:text-slate-400 disabled:cursor-not-allowed"
              >
                {removingFactor === factor.id ? 'Menghapus…' : 'Hapus'}
              </button>
            </div>
          ))}
        </div>

        {!enrollment ? (
          <button
            type="button"
            onClick={() => void handleEnrollTotp()}
            disabled={mfaBusy || loadingFactors}
            className="w-full py-2.5 rounded-xl bg-slate-900 text-white font-bold text-xs hover:bg-slate-800 transition disabled:opacity-50"
          >
            {mfaBusy ? 'Memproses…' : verifiedTotp.length ? 'Tambah Authenticator' : 'Aktifkan Authenticator'}
          </button>
        ) : (
          <div className="space-y-3 rounded-2xl border border-slate-200 p-3">
            <p className="text-xs font-bold text-slate-900">Hubungkan aplikasi authenticator</p>
            <p className="text-[10px] text-slate-500">Pindai QR berikut menggunakan aplikasi authenticator. Jika tidak dapat memindai, masukkan secret secara manual.</p>
            <div className="flex justify-center rounded-xl bg-white p-2">
              <img
                src={`data:image/svg+xml;charset=utf-8,${encodeURIComponent(enrollment.qr_code)}`}
                alt="QR code authenticator TOTP"
                className="h-44 w-44"
              />
            </div>
            <div className="rounded-lg bg-slate-50 p-2">
              <p className="text-[9px] font-bold uppercase text-slate-500">Secret manual</p>
              <p className="break-all font-mono text-xs text-slate-800">{enrollment.secret}</p>
            </div>
            <label className="block text-[10px] font-bold text-slate-600">
              Kode verifikasi
              <input
                inputMode="numeric"
                autoComplete="one-time-code"
                value={verifyCode}
                onChange={(event) => setVerifyCode(event.target.value.replace(/\D/g, '').slice(0, 8))}
                placeholder="Masukkan kode dari authenticator"
                className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5 text-xs text-slate-900"
              />
            </label>
            <div className="flex gap-2">
              <button type="button" onClick={() => void handleCancelEnrollment()} disabled={mfaBusy} className="flex-1 rounded-xl border border-slate-200 py-2 text-xs font-bold text-slate-600 disabled:opacity-50">Batal</button>
              <button type="button" onClick={() => void handleVerifyTotp()} disabled={mfaBusy || verifyCode.trim().length < 6} className="flex-1 rounded-xl bg-emerald-600 py-2 text-xs font-bold text-white disabled:opacity-50">{mfaBusy ? 'Memverifikasi…' : 'Verifikasi & Aktifkan'}</button>
            </div>
          </div>
        )}
        <p className="text-[10px] text-slate-500">Pengelolaan faktor memakai Supabase Auth MFA. Penghapusan faktor terverifikasi memerlukan sesi dengan tingkat assurance yang sesuai.</p>
      </div>

      <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-xs space-y-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-red-50 text-red-600 flex items-center justify-center"><Lock className="w-4 h-4" /></div>
          <h3 className="text-xs font-bold text-slate-900">Ubah Kata Sandi</h3>
        </div>
        <form onSubmit={handleUpdatePassword} className="space-y-2 text-xs">
          <div>
            <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Kata Sandi Saat Ini</label>
            <input type="password" value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} placeholder="••••••••••••" className="w-full p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 focus:bg-white focus:outline-none" />
          </div>
          <div>
            <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Kata Sandi Baru</label>
            <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} placeholder="Minimal 8 karakter" className="w-full p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 focus:bg-white focus:outline-none" />
          </div>
          <button type="submit" className="w-full py-2.5 rounded-xl bg-slate-900 text-white font-bold text-xs hover:bg-slate-800 transition mt-2 shadow-xs">Perbarui Kata Sandi</button>
        </form>
      </div>

      <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Sesi Perangkat Aktif</h3>
          <span className="text-[10px] text-slate-400 font-semibold">Inventaris belum tersedia</span>
        </div>
        <p className="text-[11px] text-slate-500">Supabase Auth tidak menyediakan daftar sesi perangkat lengkap melalui kontrak client yang digunakan aplikasi. Anda tetap dapat mencabut seluruh sesi akun.</p>
        <button onClick={() => void handleRevokeAllSessions()} className="w-full py-2.5 rounded-xl border border-red-200 text-red-600 hover:bg-red-50 font-bold text-xs transition">
          <span className="inline-flex items-center justify-center gap-2"><LogOut className="h-3.5 w-3.5" />Keluar dari Semua Sesi</span>
        </button>
      </div>
    </div>
  );
};
