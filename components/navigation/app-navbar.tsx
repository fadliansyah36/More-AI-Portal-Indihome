'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  User,
  Building2,
  Sparkles,
  MessageSquare,
  Bot,
  Wifi,
  Gauge,
  Sliders,
  Receipt,
  Ticket,
  Shield,
  Layers,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  QrCode,
  Users,
  Key,
  Radio,
  BarChart3,
  CheckCircle2,
  Lock,
  Grid,
  Menu,
  X,
  FileText,
  Search,
  Smartphone,
} from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { MoreAiIndiHomeLockup } from '@/components/branding/logos';
import { PWAInstallButton } from '@/components/pwa/pwa-install-button';

export const isPartnerTab = (tab: NavigationTab): boolean => {
  return [
    'partner',
    'partner_login',
    'partner_promo',
    'partner_locations',
    'partner_qr',
    'partner_packages',
    'partner_analytics',
    'partner_live_sessions',
    'partner_gateway_config',
    'partner_staff',
    'partner_api_settings',
    'partner_access_promo',
  ].includes(tab);
};

interface AppNavbarProps {
  currentTab: NavigationTab;
  onNavigate: (tab: NavigationTab) => void;
  isDarkMode?: boolean;
  onToggleDarkMode?: () => void;
  onOpenGallery?: () => void;
  onOpenDrawer?: () => void;
}

export const AppNavbar: React.FC<AppNavbarProps> = ({
  currentTab,
  onNavigate,
  isDarkMode = false,
  onToggleDarkMode,
  onOpenGallery,
  onOpenDrawer,
}) => {
  // Mode state: derived directly from currentTab
  const activeIsPartner = isPartnerTab(currentTab);
  const [overrideMode, setOverrideMode] = useState<'customer' | 'partner' | null>(null);
  const navMode = overrideMode ?? (activeIsPartner ? 'partner' : 'customer');

  const [openDropdown, setOpenDropdown] = useState<string | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpenDropdown(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleModeSwitch = (mode: 'customer' | 'partner') => {
    setOverrideMode(mode);
    setOpenDropdown(null);
    setMobileMenuOpen(false);
    if (mode === 'customer' && isPartnerTab(currentTab)) {
      onNavigate('home');
    } else if (mode === 'partner' && !isPartnerTab(currentTab)) {
      onNavigate('partner');
    }
  };

  // Customer Navigation Groups
  const customerQuickLinks: { id: NavigationTab; label: string; icon: any }[] = [
    { id: 'home', label: 'Beranda', icon: Sparkles },
    { id: 'chat', label: 'Chat AI', icon: MessageSquare },
    { id: 'agents', label: 'Agen AI', icon: Bot },
    { id: 'create', label: 'Buat Konten', icon: FileText },
    { id: 'wifi', label: 'Wi-Fi IndiHome', icon: Wifi },
    { id: 'speedtest', label: 'Speedtest 104M', icon: Gauge },
    { id: 'benefits', label: 'AI Credit (100K)', icon: Sparkles },
    { id: 'profile', label: 'Profil Saya', icon: User },
  ];

  const customerCategories = [
    {
      title: 'Fitur AI & Workspace',
      items: [
        { id: 'home', label: 'Beranda Pelanggan', desc: 'Dashboard utama & ringkasan', icon: Sparkles },
        { id: 'chat', label: 'Chat AI Assistant', desc: 'Tanya jawab model lokal & cepat', icon: MessageSquare },
        { id: 'agents', label: 'AI Agent Studio', desc: 'Research, marketing, writing, code', icon: Bot },
        { id: 'create', label: 'Buat Konten & Media', desc: 'Generator teks, gambar, video', icon: FileText },
        { id: 'analyse', label: 'Analisis File & Riset', desc: 'Upload dokumen PDF, tabel, data', icon: Layers },
        { id: 'code', label: 'Code Playground', desc: 'Asisten coding Python, JS, dll', icon: Key },
        { id: 'files', label: 'Manajemen Dokumen', desc: 'Penyimpanan berkas cloud', icon: FileText },
        { id: 'tasks', label: 'Daftar Tugas & Proyek', desc: 'Kelola workflow otomatis', icon: CheckCircle2 },
      ],
    },
    {
      title: 'Koneksi Wi-Fi IndiHome',
      items: [
        { id: 'wifi', label: 'Wi-Fi Management', desc: 'SSID, password, & sinyal optik', icon: Wifi },
        { id: 'speedtest', label: 'Uji Kecepatan Internet', desc: 'Speedtest 104.2 Mbps & latensi 9ms', icon: Gauge },
        { id: 'device_access_control', label: 'Kontrol Akses Perangkat', desc: 'QoS limit bandwidth & safe browsing', icon: Sliders },
        { id: 'wifi_session', label: 'Sesi Hotspot Tamu', desc: 'Monitor waktu aktif & kuota GB', icon: Radio },
        { id: 'devices_connected', label: 'Daftar Perangkat Aktif', desc: '5 gadget terhubung di router', icon: Smartphone },
      ],
    },
    {
      title: 'Benefit, Poin & Akun',
      items: [
        { id: 'benefits', label: 'AI Credit & Kuota Free', desc: '100.000 Poin dari IndiHome', icon: Sparkles },
        { id: 'token_ledger', label: 'Buku Besar Token', desc: 'Riwayat transaksi & audit hash', icon: Receipt },
        { id: 'partner_vouchers', label: 'Dompet Kupon Mitra', desc: 'Diskon Rp 25K-50K di kafe mitra', icon: Ticket },
        { id: 'edutech', label: 'Pusat Edukasi MoreAI', desc: 'Modul belajar & kurikulum AI', icon: Layers },
        { id: 'security_settings', label: 'Pusat Keamanan & 2FA', desc: 'Ubah sandi, enkripsi & 2-faktor', icon: Shield },
        { id: 'profile', label: 'Pengaturan Profil', desc: 'Detail akun & bahasa', icon: User },
      ],
    },
    {
      title: 'Akses Tamu & Captive Flow',
      items: [
        { id: 'captive', label: 'Captive Portal Landing', desc: 'Halaman sambutan Wi-Fi kafe', icon: Wifi },
        { id: 'captive_terms', label: 'Syarat & Ketentuan', desc: 'Legalitas akses & regulasi data', icon: FileText },
        { id: 'captive_otp', label: 'Verifikasi OTP Nomor HP', desc: 'Otentikasi SMS / WhatsApp 6-digit', icon: Key },
        { id: 'captive_success', label: 'Sukses Terhubung Wi-Fi', desc: 'Bonus 100K poin & status aktif', icon: CheckCircle2 },
        { id: 'account_upgrade', label: 'Upgrade Akun Tamu', desc: 'Simpan histori permanen', icon: User },
        { id: 'login', label: 'Masuk Akun', desc: 'Login Google / email', icon: Lock },
      ],
    },
  ];

  // Partner Navigation Groups
  const partnerQuickLinks: { id: NavigationTab; label: string; icon: any }[] = [
    { id: 'partner', label: 'Dashboard Mitra', icon: Building2 },
    { id: 'partner_live_sessions', label: 'Live Tamu', icon: Radio },
    { id: 'partner_locations', label: 'Cabang Venue', icon: Building2 },
    { id: 'partner_qr', label: 'QR Meja Kafe', icon: QrCode },
    { id: 'partner_packages', label: 'Paket Wi-Fi', icon: Wifi },
    { id: 'partner_gateway_config', label: 'Gateway Router', icon: Sliders },
    { id: 'partner_staff', label: 'Staf & Kasir', icon: Users },
    { id: 'partner_analytics', label: 'Analitik Venue', icon: BarChart3 },
    { id: 'partner_api_settings', label: 'API & Webhook', icon: Key },
    { id: 'partner_login', label: 'Login Mitra', icon: Lock },
  ];

  const partnerCategories = [
    {
      title: 'Operasional Venue Kafe/Resto',
      items: [
        { id: 'partner', label: 'Dashboard Utama Mitra', desc: 'Statistik tamu, pendapatan, & status AP', icon: Building2 },
        { id: 'partner_live_sessions', label: 'Live Monitor Pengunjung', desc: 'Pantau user aktif, MAC & bandwidth real-time', icon: Radio },
        { id: 'partner_locations', label: 'Manajemen Cabang & Meja', desc: 'Multi-outlet kafe & co-working', icon: Building2 },
        { id: 'partner_staff', label: 'Manajemen Staf & Kasir', desc: 'Role supervisor, kasir, dan teknisi', icon: Users },
      ],
    },
    {
      title: 'Jaringan Hotspot & Akses Tamu',
      items: [
        { id: 'partner_gateway_config', label: 'Konfigurasi Gateway Router', desc: 'MikroTik RouterOS, UniFi, & ONT Fiber', icon: Sliders },
        { id: 'partner_qr', label: 'QR Generator Meja Kafe', desc: 'Cetak barcode meja & banner promosi', icon: QrCode },
        { id: 'partner_packages', label: 'Paket Kuota & Durasi Tamu', desc: 'Atur batas waktu 1-4 jam & gratis/berbayar', icon: Wifi },
        { id: 'partner_promo', label: 'Program Insentif Mitra', desc: 'Skema komisi revenue share & poin venue', icon: Ticket },
        { id: 'partner_access_promo', label: 'Banner Promosi Venue', desc: 'Desain banner marketing kafe', icon: Layers },
      ],
    },
    {
      title: 'Finansial, Analitik & Integrasi',
      items: [
        { id: 'partner_analytics', label: 'Analitik Jam Sibuk & Tamu', desc: 'Grafik pengunjung harian & demografi', icon: BarChart3 },
        { id: 'partner_api_settings', label: 'Pengaturan API & Webhooks', desc: 'Integrasi POS kasir & callback event login', icon: Key },
        { id: 'partner_login', label: 'Portal Login & Registrasi Mitra', desc: 'Pintu masuk pemilik usaha B2B', icon: Lock },
      ],
    },
  ];

  return (
    <header className="sticky top-0 z-40 w-full bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 shadow-xs select-none transition-colors">
      {/* Row 1: Brand on Left, Desktop Segmented Control in Center, Utility Actions on Right */}
      <div className="w-full px-3 sm:px-6 lg:px-8 py-2 sm:py-2.5 flex items-center justify-between gap-2 sm:gap-3">
        {/* Brand Lockup (Clicking brand opens Customer Home) */}
        <div
          className="flex items-center gap-1.5 cursor-pointer shrink-0"
          onClick={() => handleModeSwitch('customer')}
          title="Ke Beranda Customer"
        >
          <MoreAiIndiHomeLockup size="sm" dark={isDarkMode} />
        </div>

        {/* PROMINENT SEGMENTED NAVBAR (Desktop Only: hidden on mobile, shown on md+) */}
        <div className="hidden md:flex items-center bg-slate-100 dark:bg-slate-800 p-1 rounded-2xl border border-slate-200/80 dark:border-slate-700 shadow-2xs shrink-0">
          {/* Customer Tab */}
          <button
            onClick={() => handleModeSwitch('customer')}
            className={`flex items-center gap-1.5 px-4 py-1.5 rounded-xl text-xs font-bold transition-all ${
              navMode === 'customer'
                ? 'bg-red-600 text-white shadow-xs'
                : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <User className="w-3.5 h-3.5" />
            <span>UI Customer</span>
            <span
              className={`text-[9px] px-1.5 py-0.2 rounded-full uppercase tracking-wider font-extrabold ${
                navMode === 'customer'
                  ? 'bg-white/25 text-white'
                  : 'bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300'
              }`}
            >
              Workspace
            </span>
          </button>

          {/* Mitra Partner Tab */}
          <button
            onClick={() => handleModeSwitch('partner')}
            className={`flex items-center gap-1.5 px-4 py-1.5 rounded-xl text-xs font-bold transition-all ${
              navMode === 'partner'
                ? 'bg-slate-900 dark:bg-white text-white dark:text-slate-900 shadow-xs'
                : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Building2 className="w-3.5 h-3.5 text-amber-500" />
            <span>UI Mitra Partner</span>
            <span
              className={`text-[9px] px-1.5 py-0.2 rounded-full uppercase tracking-wider font-extrabold ${
                navMode === 'partner'
                  ? 'bg-amber-500/20 text-amber-300 dark:text-amber-700'
                  : 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300'
              }`}
            >
              B2B Venue
            </span>
          </button>
        </div>

        {/* Right utility items: Gallery Modal Button, PWA, and Menu */}
        <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
          {/* Direct Screen Gallery Button */}
          {onOpenGallery && (
            <button
              onClick={onOpenGallery}
              className="flex items-center gap-1 px-2 sm:px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-semibold transition shadow-2xs"
              title="Katalog Lengkap Sheet 1-6"
            >
              <Grid className="w-3.5 h-3.5 text-red-600 shrink-0" />
              <span className="hidden sm:inline">Pilih Halaman UI</span>
              <span className="sm:hidden text-[11px] font-semibold">Halaman</span>
            </button>
          )}

          <PWAInstallButton compact />

          {/* All-screen Drawer Menu Trigger */}
          {onOpenDrawer && (
            <button
              onClick={onOpenDrawer}
              className="p-1.5 sm:p-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-red-50 hover:text-red-600 transition shrink-0"
              title="Menu Navigasi Seluruh Fitur"
            >
              <Menu className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Row 2 (Mobile Only): Dedicated Full-Width Segmented Tab for Customer vs Mitra Partner */}
      <div className="block md:hidden px-3 pt-0.5 pb-2 bg-white dark:bg-slate-900 border-b border-slate-100 dark:border-slate-800">
        <div className="grid grid-cols-2 p-1 bg-slate-100 dark:bg-slate-800/90 rounded-xl gap-1 w-full border border-slate-200/70 dark:border-slate-700/70 shadow-2xs">
          <button
            onClick={() => handleModeSwitch('customer')}
            className={`flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg text-xs font-bold transition-all ${
              navMode === 'customer'
                ? 'bg-red-600 text-white shadow-xs font-extrabold'
                : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <User className="w-3.5 h-3.5 shrink-0" />
            <span>UI Customer</span>
          </button>
          <button
            onClick={() => handleModeSwitch('partner')}
            className={`flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg text-xs font-bold transition-all ${
              navMode === 'partner'
                ? 'bg-slate-900 dark:bg-white text-white dark:text-slate-900 shadow-xs font-extrabold'
                : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Building2 className="w-3.5 h-3.5 text-amber-500 shrink-0" />
            <span>UI Mitra Partner</span>
          </button>
        </div>
      </div>

      {/* Row 3 Sub-Navbar: Category Dropdowns & Quick Horizontal Scroll Bar with min-w-0 */}
      <div
        ref={dropdownRef}
        className={`border-t px-3 sm:px-6 lg:px-8 py-1.5 sm:py-2 transition-colors w-full overflow-hidden ${
          navMode === 'customer'
            ? 'bg-red-50/40 dark:bg-red-950/20 border-red-100 dark:border-red-900/30'
            : 'bg-amber-50/40 dark:bg-amber-950/20 border-amber-100 dark:border-amber-900/30'
        }`}
      >
        <div className="w-full flex items-center justify-between gap-2 sm:gap-3">
          {/* Mode Indicator & Active Context Badge */}
          <div className="flex items-center gap-1.5 shrink-0">
            <span
              className={`text-[10px] sm:text-[11px] font-extrabold flex items-center gap-1 sm:gap-1.5 px-2 sm:px-2.5 py-1 rounded-lg shrink-0 ${
                navMode === 'customer'
                  ? 'bg-red-600 text-white shadow-2xs'
                  : 'bg-slate-900 text-amber-400 dark:bg-amber-400 dark:text-slate-900 shadow-2xs'
              }`}
            >
              {navMode === 'customer' ? (
                <>
                  <User className="w-3 h-3 shrink-0" />
                  <span className="hidden sm:inline">Customer Workspace</span>
                  <span className="sm:hidden">Workspace</span>
                </>
              ) : (
                <>
                  <Building2 className="w-3 h-3 shrink-0" />
                  <span className="hidden sm:inline">Mitra Partner B2B</span>
                  <span className="sm:hidden">Mitra B2B</span>
                </>
              )}
            </span>

            {/* Desktop Category Dropdown Trigger */}
            <div className="relative hidden md:block">
              <button
                onClick={() => setOpenDropdown(openDropdown === 'categories' ? null : 'categories')}
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 transition shadow-2xs"
              >
                <span>Kategori Menu</span>
                <ChevronDown className={`w-3.5 h-3.5 transition-transform ${openDropdown === 'categories' ? 'rotate-180' : ''}`} />
              </button>

              {/* Categorized Dropdown Popup */}
              {openDropdown === 'categories' && (
                <div className="absolute left-0 top-full mt-2 w-[520px] bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 p-4 z-50 grid grid-cols-2 gap-4 animate-in fade-in duration-150">
                  {(navMode === 'customer' ? customerCategories : partnerCategories).map((cat, idx) => (
                    <div key={idx} className="space-y-1.5">
                      <h4 className="text-[10px] font-black uppercase tracking-wider text-slate-400 dark:text-slate-500 border-b border-slate-100 dark:border-slate-800 pb-1">
                        {cat.title}
                      </h4>
                      <div className="space-y-0.5">
                        {cat.items.map((item) => (
                          <button
                            key={item.id}
                            onClick={() => {
                              onNavigate(item.id as NavigationTab);
                              setOpenDropdown(null);
                            }}
                            className={`w-full text-left p-1.5 rounded-lg flex items-center justify-between transition group ${
                              currentTab === item.id
                                ? 'bg-red-50 dark:bg-red-950/40 text-red-600 font-bold'
                                : 'hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200'
                            }`}
                          >
                            <div className="flex items-center gap-2 min-w-0">
                              <item.icon className="w-3.5 h-3.5 shrink-0 text-slate-400 group-hover:text-red-600" />
                              <div className="min-w-0">
                                <span className="text-xs truncate block">{item.label}</span>
                                <span className="text-[9px] text-slate-400 truncate block">{item.desc}</span>
                              </div>
                            </div>
                            <ChevronRight className="w-3 h-3 text-slate-300 opacity-0 group-hover:opacity-100 shrink-0" />
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Horizontal Quick Links Scrollbar (Desktop & Mobile) with min-w-0 flex-1 */}
          <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-0.5 min-w-0 flex-1 justify-start md:justify-end">
            {(navMode === 'customer' ? customerQuickLinks : partnerQuickLinks).map((link) => {
              const Icon = link.icon;
              const isActive = currentTab === link.id;
              return (
                <button
                  key={link.id}
                  onClick={() => onNavigate(link.id)}
                  className={`flex items-center gap-1.5 px-2.5 sm:px-3 py-1 rounded-xl text-xs font-semibold whitespace-nowrap transition-all shrink-0 ${
                    isActive
                      ? navMode === 'customer'
                        ? 'bg-red-600 text-white shadow-2xs font-bold scale-[1.02]'
                        : 'bg-slate-900 text-white dark:bg-white dark:text-slate-900 shadow-2xs font-bold scale-[1.02]'
                      : 'bg-white/80 dark:bg-slate-800/80 text-slate-700 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-800 border border-slate-200/60 dark:border-slate-700/60 shadow-2xs'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-white dark:text-slate-900' : 'text-slate-400'}`} />
                  <span>{link.label}</span>
                </button>
              );
            })}

            {/* Mobile All Pages sheet trigger */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden flex items-center gap-1 px-2.5 py-1 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-bold text-slate-700 dark:text-slate-200 shrink-0 shadow-2xs"
            >
              <span>Semua</span>
              <ChevronDown className={`w-3 h-3 ${mobileMenuOpen ? 'rotate-180' : ''}`} />
            </button>
          </div>
        </div>


        {/* Mobile Accordion Dropdown for All Sub-Pages in Current Mode */}
        {mobileMenuOpen && (
          <div className="md:hidden mt-2 pt-2 border-t border-slate-200 dark:border-slate-800 space-y-3 animate-in fade-in duration-150">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                Direktori {navMode === 'customer' ? 'Customer' : 'Mitra Partner'}
              </span>
              <button
                onClick={() => setMobileMenuOpen(false)}
                className="text-xs text-red-600 font-semibold"
              >
                Tutup
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {(navMode === 'customer' ? customerCategories : partnerCategories).map((cat, idx) => (
                <div key={idx} className="bg-white dark:bg-slate-800/80 p-2.5 rounded-xl border border-slate-200/80 dark:border-slate-700 space-y-1">
                  <h5 className="text-[10px] font-black uppercase tracking-wider text-slate-400 dark:text-slate-500">
                    {cat.title}
                  </h5>
                  <div className="grid grid-cols-2 gap-1">
                    {cat.items.map((item) => (
                      <button
                        key={item.id}
                        onClick={() => {
                          onNavigate(item.id as NavigationTab);
                          setMobileMenuOpen(false);
                        }}
                        className={`text-left p-1.5 rounded-lg text-xs truncate flex items-center gap-1.5 transition ${
                          currentTab === item.id
                            ? 'bg-red-600 text-white font-bold'
                            : 'text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700'
                        }`}
                      >
                        <item.icon className="w-3 h-3 shrink-0" />
                        <span className="truncate">{item.label}</span>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </header>
  );
};
