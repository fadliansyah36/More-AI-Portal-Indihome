'use client';

import React, { useEffect, useState } from 'react';
import {
  User,
  Gift,
  Bell,
  Globe,
  Shield,
  Moon,
  HelpCircle,
  Info,
  LogOut,
  ChevronRight,
  HardDrive,
  Sparkles,
  Lock,
  Check,
} from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';
import { profileApi, customerApi, notificationApi } from '@/lib/api/client';

interface ProfileSettingsViewProps {
  onNavigateTab: (tab: NavigationTab) => void;
  onLogout?: () => void;
  isDarkMode?: boolean;
  onToggleDarkMode?: () => void;
}

export const ProfileSettingsView: React.FC<ProfileSettingsViewProps> = ({
  onNavigateTab,
  onLogout,
  isDarkMode = false,
  onToggleDarkMode,
}) => {
  const { showToast } = useToast();
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [profileName, setProfileName] = useState('');
  const [profileEmail, setProfileEmail] = useState('');
  const [profileLoading, setProfileLoading] = useState(true);
  const [savingPreference, setSavingPreference] = useState(false);
  const [creditBalance, setCreditBalance] = useState<number | null>(null);

  useEffect(() => {
    let active = true;

    // Profile identity and notification preferences are independent resources.
    // A notification endpoint failure must never turn a successfully loaded
    // customer profile into a generic "Failed to fetch" state.
    profileApi.get()
      .then((identity) => {
        if (!active) return;
        const registeredName = identity.profile?.display_name?.trim()
          || identity.user?.display_name?.trim()
          || '';
        setProfileName(registeredName || 'Nama belum diatur');
        setProfileEmail(identity.user?.email || '');
      })
      .catch((error) => {
        if (active) showToast(error instanceof Error ? error.message : 'Profil gagal dimuat.', 'error');
      })
      .finally(() => { if (active) setProfileLoading(false); });

    notificationApi.preferences()
      .then((preferences) => {
        if (active) setNotificationsEnabled(preferences.in_app_enabled);
      })
      .catch(() => {
        // Keep the existing preference state; profile identity remains usable.
      });

    return () => { active = false; };
  }, [showToast]);

  useEffect(() => {
    let active = true;
    customerApi.wallets().then(({ wallets }) => {
      if (!active) return;
      const balance = wallets.reduce((sum, wallet) => sum + Number(wallet.balance || 0), 0);
      setCreditBalance(Number.isFinite(balance) ? balance : null);
    }).catch(() => { if (active) setCreditBalance(null); });
    return () => { active = false; };
  }, []);

  const toggleNotifications = async () => {
    const next = !notificationsEnabled;
    setSavingPreference(true);
    try {
      const saved = await notificationApi.updatePreferences({ in_app_enabled: next });
      setNotificationsEnabled(saved.in_app_enabled);
      showToast('Preferensi notifikasi tersimpan.', 'success');
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Preferensi gagal disimpan.', 'error');
    } finally { setSavingPreference(false); }
  };
  const [language, setLanguage] = useState<'id' | 'en'>('id');
  const [showFaqModal, setShowFaqModal] = useState(false);
  const [showAboutModal, setShowAboutModal] = useState(false);

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Profile Header (From Sheet 1, 2, 5, 6) */}
      <div className="p-5 rounded-3xl bg-white border border-slate-100 shadow-xs text-center space-y-2">
        <div className="relative w-20 h-20 mx-auto">
          <div className="w-20 h-20 rounded-full bg-gradient-to-tr from-red-600 via-rose-500 to-amber-500 p-0.5 shadow-md">
            <div className="w-full h-full rounded-full bg-white flex items-center justify-center overflow-hidden">
              <span className="text-2xl font-black text-red-600">{profileName ? profileName.trim().split(/\\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase() : "M"}</span>
            </div>
          </div>
          <span className="absolute bottom-0 right-0 w-5 h-5 rounded-full bg-emerald-500 border-2 border-white flex items-center justify-center text-white text-[9px] font-bold">
            ✓
          </span>
        </div>

        <div>
          <h2 className="text-base font-bold text-slate-900 leading-tight">{profileLoading ? "Memuat profil…" : profileName}</h2>
          <p className="text-xs text-slate-500 font-medium">{profileEmail || "Email tidak tersedia"}</p>
        </div>

        {/* Small Benefit Pill */}
        <div
          onClick={() => onNavigateTab('benefits')}
          className="cursor-pointer inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-red-50 hover:bg-red-100 border border-red-200 text-red-700 text-xs font-semibold transition"
        >
          <Gift className="w-3.5 h-3.5 text-red-600" />
          <span>AI Credit: {creditBalance === null ? 'Tidak tersedia' : creditBalance.toLocaleString('id-ID') + ' Poin'}</span>
          <ChevronRight className="w-3 h-3" />
        </div>
      </div>

      {/* Settings Navigation Menu */}
      <div className="bg-white rounded-3xl p-3 border border-slate-100 shadow-xs space-y-1">
        <button
          onClick={() => showToast(profileName ? 'Profil akun: ' + profileName + (profileEmail ? ' · ' + profileEmail : '') : 'Informasi profil belum tersedia.', 'info')}
          className="w-full p-3 rounded-2xl hover:bg-slate-50 flex items-center justify-between text-left transition group"
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center group-hover:bg-red-50 group-hover:text-red-600 transition">
              <User className="w-4 h-4" />
            </div>
            <span className="text-xs font-semibold text-slate-800">Informasi Akun</span>
          </div>
          <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-slate-700 transition" />
        </button>

        <button
          onClick={() => onNavigateTab('benefits')}
          className="w-full p-3 rounded-2xl hover:bg-slate-50 flex items-center justify-between text-left transition group"
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center group-hover:bg-red-50 group-hover:text-red-600 transition">
              <Gift className="w-4 h-4" />
            </div>
            <span className="text-xs font-semibold text-slate-800">Benefit & AI Credit</span>
          </div>
          <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-slate-700 transition" />
        </button>

        <div className="w-full p-3 rounded-2xl flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center">
              <Moon className="w-4 h-4" />
            </div>
            <span className="text-xs font-semibold text-slate-800">Mode Gelap</span>
          </div>
          <button
            onClick={onToggleDarkMode}
            className={`w-11 h-6 rounded-full transition-colors relative p-0.5 ${
              isDarkMode ? 'bg-red-600' : 'bg-slate-200'
            }`}
          >
            <div
              className={`w-5 h-5 rounded-full bg-white shadow-xs transition-transform ${
                isDarkMode ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>

        <div className="w-full p-3 rounded-2xl flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center">
              <Bell className="w-4 h-4" />
            </div>
            <span className="text-xs font-semibold text-slate-800">Notifikasi</span>
          </div>
          <button
            onClick={() => void toggleNotifications()} disabled={savingPreference}
            className={`w-11 h-6 rounded-full transition-colors relative p-0.5 ${
              notificationsEnabled ? 'bg-red-600' : 'bg-slate-200'
            }`}
          >
            <div
              className={`w-5 h-5 rounded-full bg-white shadow-xs transition-transform ${
                notificationsEnabled ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>

        <button
          onClick={() => setLanguage(language === 'id' ? 'en' : 'id')}
          className="w-full p-3 rounded-2xl hover:bg-slate-50 flex items-center justify-between text-left transition group"
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center group-hover:bg-red-50 group-hover:text-red-600 transition">
              <Globe className="w-4 h-4" />
            </div>
            <span className="text-xs font-semibold text-slate-800">Bahasa</span>
          </div>
          <span className="text-[11px] font-bold text-red-600 uppercase">
            {language === 'id' ? 'Bahasa Indonesia' : 'English'}
          </span>
        </button>

        <button
          onClick={() => onNavigateTab('security_settings')}
          className="w-full p-3 rounded-2xl hover:bg-slate-50 flex items-center justify-between text-left transition group"
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center group-hover:bg-red-50 group-hover:text-red-600 transition">
              <Shield className="w-4 h-4" />
            </div>
            <span className="text-xs font-semibold text-slate-800">Keamanan & Privasi</span>
          </div>
          <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-slate-700 transition" />
        </button>

        <button
          onClick={() => setShowFaqModal(true)}
          className="w-full p-3 rounded-2xl hover:bg-slate-50 flex items-center justify-between text-left transition group"
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center group-hover:bg-red-50 group-hover:text-red-600 transition">
              <HelpCircle className="w-4 h-4" />
            </div>
            <span className="text-xs font-semibold text-slate-800">Bantuan & FAQ</span>
          </div>
          <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-slate-700 transition" />
        </button>

        <button
          onClick={() => setShowAboutModal(true)}
          className="w-full p-3 rounded-2xl hover:bg-slate-50 flex items-center justify-between text-left transition group"
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center group-hover:bg-red-50 group-hover:text-red-600 transition">
              <Info className="w-4 h-4" />
            </div>
            <span className="text-xs font-semibold text-slate-800">Tentang MoreAI</span>
          </div>
          <span className="text-[10px] text-slate-400">v1.0.0 PWA</span>
        </button>

        <button
          onClick={() => {
            showToast('Anda telah keluar dari sesi MoreAI.', 'info');
            if (onLogout) onLogout();
          }}
          className="w-full p-3 rounded-2xl hover:bg-red-50 flex items-center gap-3 text-left transition text-red-600"
        >
          <div className="w-8 h-8 rounded-xl bg-red-50 text-red-600 flex items-center justify-center">
            <LogOut className="w-4 h-4" />
          </div>
          <span className="text-xs font-bold">Keluar Akun</span>
        </button>
      </div>

      {/* FAQ Modal */}
      {showFaqModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-fadeIn">
          <div className="w-full max-w-sm rounded-3xl bg-white p-5 shadow-2xl border border-slate-100 text-slate-800 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900">Bantuan & FAQ</h3>
              <button onClick={() => setShowFaqModal(false)} className="text-slate-400 hover:text-slate-600 text-xs font-bold">
                ✕
              </button>
            </div>
            <div className="space-y-2 text-xs text-slate-600">
              <p className="font-bold text-slate-900">1. Bagaimana cara mendapatkan AI Credit Free?</p>
              <p>Cukup hubungkan perangkat Anda ke jaringan Wi-Fi Global Partner ISP yang terdaftar. Saldo kuota akan otomatis terisi setiap bulan.</p>
              <p className="font-bold text-slate-900 pt-1">2. Apakah aplikasi ini bisa digunakan saat offline?</p>
              <p>Ya, MoreAI berbasis PWA yang mendukung caching offline untuk riwayat tugas dan catatan yang telah dibuka.</p>
              <p className="font-bold text-slate-900 pt-1">3. Siapa yang dapat mendaftar sebagai Partner?</p>
              <p>Pemilik kedai kopi, restoran, coworking space, dan institusi publik yang ingin menyediakan akses internet &amp; AI terpadu bagi pengunjung.</p>
            </div>
            <button
              onClick={() => setShowFaqModal(false)}
              className="w-full py-2.5 rounded-xl bg-slate-900 text-white text-xs font-semibold hover:bg-slate-800 transition mt-2"
            >
              Tutup
            </button>
          </div>
        </div>
      )}

      {/* About Modal */}
      {showAboutModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-fadeIn">
          <div className="w-full max-w-sm rounded-3xl bg-white p-5 shadow-2xl border border-slate-100 text-slate-800 space-y-3 text-center">
            <div className="w-12 h-12 rounded-2xl bg-red-600 text-white flex items-center justify-center mx-auto text-xl font-black">
              M
            </div>
            <h3 className="text-base font-bold text-slate-900">MoreAI &bull; Global Partner ISP/Network</h3>
            <p className="text-xs text-slate-500">
              Platform AI Workspace &amp; Akses Wi-Fi Terintegrasi bersama Ekosistem Global Partner ISP/Network.
            </p>
            <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100 text-[11px] text-slate-600 space-y-1">
              <div>Versi: 1.0.0 (Progressive Web App)</div>
              <div>Mitra Jaringan: Global Partner ISP &amp; Network Alliance</div>
              <div>Engine: OpenManus Agent Architecture &amp; Gemini AI</div>
            </div>
            <button
              onClick={() => setShowAboutModal(false)}
              className="w-full py-2.5 rounded-xl bg-red-600 text-white text-xs font-semibold hover:bg-red-700 transition"
            >
              Tutup
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
