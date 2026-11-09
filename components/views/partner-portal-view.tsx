'use client';

import React, { useState } from 'react';
import {
  Building2,
  MapPin,
  QrCode,
  Users,
  BarChart3,
  Package,
  FileCheck,
  CheckCircle2,
  ChevronRight,
  Download,
  Share2,
  Plus,
  ArrowRight,
  ArrowLeft,
  RotateCcw,
  Sparkles,
  TrendingUp,
  ShieldCheck,
  Megaphone,
} from 'lucide-react';
import { PARTNER_LOCATIONS } from '@/lib/data';
import { PartnerLocation, NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';

export interface PartnerPortalViewProps {
  initialMode?: 'dashboard' | 'onboarding' | 'qr' | 'locations' | 'analytics' | 'packages' | 'promo';
  onNavigateTab?: (tab: NavigationTab) => void;
}

export const PartnerPortalView: React.FC<PartnerPortalViewProps> = ({
  initialMode = 'dashboard',
  onNavigateTab,
}) => {
  const { showToast } = useToast();
  const [partnerMode, setPartnerMode] = useState<'dashboard' | 'onboarding' | 'qr' | 'locations' | 'analytics' | 'packages' | 'promo'>(initialMode);
  const [onboardingStep, setOnboardingStep] = useState<1 | 2 | 3 | 4>(1);
  const [locations, setLocations] = useState<PartnerLocation[]>(PARTNER_LOCATIONS);
  const [selectedPlan, setSelectedPlan] = useState<'Basic' | 'Business' | 'Enterprise'>('Business');

  // Form states for partner registration
  const [partnerName, setPartnerName] = useState('Farhan Fadliansyah');
  const [businessEmail, setBusinessEmail] = useState('farhan@coffeehouse.id');
  const [venueName, setVenueName] = useState('CoffeeHouse Semarang');
  const [venueType, setVenueType] = useState('Coffee Shop / Restoran');
  const [venueAddress, setVenueAddress] = useState('Jl. Pemuda No. 123, Semarang');

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Top Banner Header */}
      <div className="flex items-center justify-between">
        <div>
          <span className="text-[10px] font-bold text-red-600 uppercase tracking-wider">
            B2B Venue & Network System (Sheet 4)
          </span>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Partner Wi-Fi & AI Access
          </h1>
          <p className="text-xs text-slate-500">
            Kelola Wi-Fi venue, kuota sponsor AI pelanggan, dan distribusi QR code
          </p>
        </div>

        <div className="flex gap-1.5">
          <button
            onClick={() => setPartnerMode(partnerMode === 'dashboard' ? 'onboarding' : 'dashboard')}
            className="px-2.5 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition"
          >
            {partnerMode === 'onboarding' ? 'Ke Dashboard' : 'Alur Registrasi'}
          </button>
        </div>
      </div>

      {/* DASHBOARD MODE */}
      {partnerMode === 'dashboard' && (
        <div className="space-y-4">
          {/* Partner Header Card (Sheet 4) */}
          <div className="p-4 rounded-3xl bg-white border border-slate-100 shadow-xs flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-red-600 to-rose-500 text-white flex items-center justify-center font-bold text-lg shadow-xs">
                CH
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-bold text-slate-900">Halo, {partnerName} 👋</h2>
                </div>
                <p className="text-xs text-slate-500 font-medium">{venueName}</p>
                <div className="flex items-center gap-1.5 text-[10px] text-emerald-600 font-semibold mt-0.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span>Status Layanan: Aktif · Paket Business</span>
                </div>
              </div>
            </div>

            <button
              onClick={() => setPartnerMode('qr')}
              className="p-2.5 rounded-2xl bg-red-50 text-red-600 hover:bg-red-100 transition shadow-2xs"
              title="Buka QR Akses"
            >
              <QrCode className="w-5 h-5" />
            </button>
          </div>

          {/* Key Stat Counters (From Sheet 4: Pengguna Hari Ini 126, Total Akses AI 342) */}
          <div className="grid grid-cols-2 gap-2.5">
            <div className="p-4 rounded-3xl bg-white border border-slate-100 shadow-xs">
              <div className="flex items-center justify-between text-slate-400 mb-1">
                <span className="text-xs font-semibold">Pengguna Hari Ini</span>
                <Users className="w-4 h-4 text-blue-500" />
              </div>
              <span className="text-2xl font-black text-slate-900 tracking-tight">126</span>
              <span className="text-[10px] text-emerald-600 font-semibold block mt-0.5">
                +14% vs kemarin
              </span>
            </div>

            <div className="p-4 rounded-3xl bg-white border border-slate-100 shadow-xs">
              <div className="flex items-center justify-between text-slate-400 mb-1">
                <span className="text-xs font-semibold">Total Akses AI</span>
                <Sparkles className="w-4 h-4 text-red-500" />
              </div>
              <span className="text-2xl font-black text-slate-900 tracking-tight">342</span>
              <span className="text-[10px] text-emerald-600 font-semibold block mt-0.5">
                Kredit Sponsor Aktif
              </span>
            </div>
          </div>

          {/* Quick Action Navigation Grid (Exact from Sheet 4) */}
          <div className="grid grid-cols-4 gap-2">
            <button
              onClick={() => setPartnerMode('locations')}
              className="p-3 rounded-2xl bg-white border border-slate-100 hover:border-red-200 flex flex-col items-center text-center shadow-2xs transition group"
            >
              <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center mb-1 group-hover:scale-105 transition-transform">
                <Building2 className="w-4 h-4" />
              </div>
              <span className="text-[10px] font-bold text-slate-800">Kelola Lokasi</span>
            </button>

            <button
              onClick={() => setPartnerMode('qr')}
              className="p-3 rounded-2xl bg-white border border-slate-100 hover:border-red-200 flex flex-col items-center text-center shadow-2xs transition group"
            >
              <div className="w-8 h-8 rounded-xl bg-red-50 text-red-600 flex items-center justify-center mb-1 group-hover:scale-105 transition-transform">
                <QrCode className="w-4 h-4" />
              </div>
              <span className="text-[10px] font-bold text-slate-800">QR Akses</span>
            </button>

            <button
              onClick={() => setPartnerMode('analytics')}
              className="p-3 rounded-2xl bg-white border border-slate-100 hover:border-red-200 flex flex-col items-center text-center shadow-2xs transition group"
            >
              <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-1 group-hover:scale-105 transition-transform">
                <BarChart3 className="w-4 h-4" />
              </div>
              <span className="text-[10px] font-bold text-slate-800">Laporan</span>
            </button>

            <button
              onClick={() => setPartnerMode('packages')}
              className="p-3 rounded-2xl bg-white border border-slate-100 hover:border-red-200 flex flex-col items-center text-center shadow-2xs transition group"
            >
              <div className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center mb-1 group-hover:scale-105 transition-transform">
                <Package className="w-4 h-4" />
              </div>
              <span className="text-[10px] font-bold text-slate-800">Paket</span>
            </button>
          </div>

          {/* Locations Preview */}
          <div className="bg-white rounded-3xl p-4 border border-slate-100 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Titik Wi-Fi Partner Terdaftar
              </h3>
              <button
                onClick={() => setPartnerMode('locations')}
                className="text-xs text-red-600 font-semibold"
              >
                Lihat Semua
              </button>
            </div>

            <div className="space-y-2">
              {locations.map((loc) => (
                <div
                  key={loc.id}
                  className="p-3 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-between"
                >
                  <div>
                    <h4 className="text-xs font-bold text-slate-900">{loc.name}</h4>
                    <span className="text-[10px] text-slate-500">{loc.address}</span>
                  </div>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      loc.status === 'active'
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : 'bg-slate-200 text-slate-600'
                    }`}
                  >
                    {loc.status === 'active' ? `Aktif · ${loc.plan}` : 'Nonaktif'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* QR AKSES VIEW (Sheet 4) */}
      {partnerMode === 'qr' && (
        <div className="bg-white rounded-3xl p-6 border border-slate-100 shadow-xs text-center space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <button
              onClick={() => setPartnerMode('dashboard')}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-700"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h3 className="text-sm font-bold text-slate-900">QR Akses Wi-Fi & MoreAI</h3>
            <div className="w-5" />
          </div>

          {/* Realistic QR Code Graphic Mockup */}
          <div className="p-6 bg-slate-50 rounded-3xl border border-slate-200 inline-block shadow-inner mx-auto">
            <div className="w-48 h-48 bg-white p-3 rounded-2xl border border-slate-300 shadow-sm flex flex-col items-center justify-between">
              {/* Top simulated QR patterns */}
              <div className="w-full flex justify-between">
                <div className="w-12 h-12 bg-slate-900 rounded-md p-1.5 flex items-center justify-center">
                  <div className="w-6 h-6 border-4 border-white bg-slate-900" />
                </div>
                <div className="w-12 h-12 bg-slate-900 rounded-md p-1.5 flex items-center justify-center">
                  <div className="w-6 h-6 border-4 border-white bg-slate-900" />
                </div>
              </div>

              {/* Center Logo badge */}
              <div className="w-10 h-10 rounded-xl bg-red-600 text-white flex items-center justify-center font-black text-sm shadow-md">
                M
              </div>

              {/* Bottom simulated QR patterns */}
              <div className="w-full flex justify-between">
                <div className="w-12 h-12 bg-slate-900 rounded-md p-1.5 flex items-center justify-center">
                  <div className="w-6 h-6 border-4 border-white bg-slate-900" />
                </div>
                <div className="w-12 h-12 border-2 border-slate-900 grid grid-cols-2 gap-1 p-1">
                  <div className="bg-slate-900" />
                  <div className="bg-slate-400" />
                  <div className="bg-slate-700" />
                  <div className="bg-slate-900" />
                </div>
              </div>
            </div>
          </div>

          <div>
            <h4 className="text-base font-bold text-slate-900">{venueName}</h4>
            <p className="text-xs text-slate-500 mt-0.5">
              Wi-Fi: <strong>{locations[0].ssid}</strong> · Akses MoreAI Otomatis
            </p>
          </div>

          <div className="grid grid-cols-2 gap-2 pt-2">
            <button
              onClick={() => showToast(`QR Code untuk ${venueName} berhasil diunduh dalam format PDF/PNG resolusi tinggi!`, 'success')}
              className="py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition flex items-center justify-center gap-1.5 shadow-xs"
            >
              <Download className="w-4 h-4" />
              <span>Unduh QR</span>
            </button>
            <button
              onClick={() => showToast('Tautan portal tamu berhasil disalin ke clipboard.', 'success')}
              className="py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition flex items-center justify-center gap-1.5"
            >
              <Share2 className="w-4 h-4" />
              <span>Bagikan</span>
            </button>
          </div>
        </div>
      )}

      {/* LOCATIONS MANAGEMENT (Sheet 4) */}
      {partnerMode === 'locations' && (
        <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <button
              onClick={() => setPartnerMode('dashboard')}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-700"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h3 className="text-sm font-bold text-slate-900">Kelola Lokasi & Cabang</h3>
            <button
              onClick={() => showToast('Form pendaftaran cabang baru dibuka.', 'info')}
              className="text-xs font-bold text-red-600 flex items-center gap-1"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Tambah</span>
            </button>
          </div>

          <div className="space-y-3">
            {locations.map((loc) => (
              <div
                key={loc.id}
                className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2"
              >
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-slate-900">{loc.name}</h4>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      loc.status === 'active'
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : 'bg-slate-200 text-slate-600'
                    }`}
                  >
                    {loc.status === 'active' ? `Aktif · ${loc.plan}` : 'Nonaktif'}
                  </span>
                </div>
                <p className="text-[11px] text-slate-500">{loc.address}</p>

                <div className="pt-2 border-t border-slate-200/60 flex items-center justify-between text-[11px]">
                  <span className="text-slate-400">Pengunjung: <strong>{loc.dailyUsers}/hari</strong></span>
                  <button
                    onClick={() => {
                      setVenueName(loc.name);
                      setPartnerMode('qr');
                    }}
                    className="text-red-600 font-bold hover:underline"
                  >
                    Lihat QR Akses &gt;
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ANALYTICS & REPORTING (Sheet 4) */}
      {partnerMode === 'analytics' && (
        <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <button
              onClick={() => setPartnerMode('dashboard')}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-700"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h3 className="text-sm font-bold text-slate-900">Laporan & Analitik Partner</h3>
            <div className="w-5" />
          </div>

          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100">
              <span className="text-[10px] text-slate-400 block font-medium">Total Pengguna</span>
              <span className="text-lg font-black text-slate-900 block mt-0.5">1.248</span>
              <span className="text-[9px] text-emerald-600 font-semibold">+12%</span>
            </div>
            <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100">
              <span className="text-[10px] text-slate-400 block font-medium">Pengguna Unik</span>
              <span className="text-lg font-black text-slate-900 block mt-0.5">856</span>
              <span className="text-[9px] text-emerald-600 font-semibold">+8%</span>
            </div>
            <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100">
              <span className="text-[10px] text-slate-400 block font-medium">Akses AI</span>
              <span className="text-lg font-black text-slate-900 block mt-0.5">2.976</span>
              <span className="text-[9px] text-emerald-600 font-semibold">+18%</span>
            </div>
          </div>

          <div className="space-y-2 pt-2">
            <span className="text-xs font-bold text-slate-800">Distribusi Fitur AI Pengunjung:</span>
            <div className="space-y-2">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span>Chat AI</span>
                  <span className="font-bold">38%</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2">
                  <div className="bg-red-600 h-2 rounded-full" style={{ width: '38%' }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span>Create Studio</span>
                  <span className="font-bold">24%</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2">
                  <div className="bg-amber-500 h-2 rounded-full" style={{ width: '24%' }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span>Research</span>
                  <span className="font-bold">16%</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full" style={{ width: '16%' }} />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* PACKAGES MANAGEMENT (Sheet 4) */}
      {partnerMode === 'packages' && (
        <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <button
              onClick={() => setPartnerMode('dashboard')}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-700"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h3 className="text-sm font-bold text-slate-900">Kelola Paket Partner</h3>
            <div className="w-5" />
          </div>

          <div className="p-4 rounded-2xl bg-gradient-to-r from-red-600 to-rose-600 text-white space-y-1">
            <span className="text-[10px] uppercase font-bold text-red-200">Paket Aktif Saat Ini</span>
            <h4 className="text-base font-bold">Paket Business</h4>
            <p className="text-xs text-red-100">Kapasitas hingga 200 pengguna serentak · Aktif hingga 12 Jul 2026</p>
          </div>

          <div className="space-y-2">
            <div className="p-3 rounded-2xl border border-slate-200 flex justify-between items-center text-xs">
              <div>
                <span className="font-bold text-slate-900 block">Paket Basic</span>
                <span className="text-slate-500 text-[11px]">Hingga 50 pengguna · Gratis</span>
              </div>
              <button
                onClick={() => {
                  setSelectedPlan('Basic');
                  showToast('Beralih ke Paket Basic.', 'info');
                }}
                className="px-3 py-1 rounded-xl bg-slate-100 text-slate-700 font-semibold"
              >
                Pilih
              </button>
            </div>

            <div className="p-3 rounded-2xl border-2 border-red-500 bg-red-50/50 flex justify-between items-center text-xs">
              <div>
                <span className="font-bold text-slate-900 block">Paket Business (Aktif)</span>
                <span className="text-slate-500 text-[11px]">Hingga 200 pengguna · Rp 149.000/bln</span>
              </div>
              <span className="text-red-600 font-bold">Terpasang</span>
            </div>

            <div className="p-3 rounded-2xl border border-slate-200 flex justify-between items-center text-xs">
              <div>
                <span className="font-bold text-slate-900 block">Paket Enterprise</span>
                <span className="text-slate-500 text-[11px]">500+ pengguna · Integrasi Kustom</span>
              </div>
              <button
                onClick={() => showToast('Permintaan Paket Enterprise terkirim! Tim sales IndiHome akan menghubungi Anda.', 'success')}
                className="px-3 py-1 rounded-xl bg-slate-900 text-white font-semibold"
              >
                Kontak
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ONBOARDING STEPPER MODE (Sheet 4 Alur Utama Partner) */}
      {partnerMode === 'onboarding' && (
        <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <button
              onClick={() => setPartnerMode('dashboard')}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-700"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h3 className="text-sm font-bold text-slate-900">Alur Registrasi Partner (1-4)</h3>
            <button
              onClick={() => setOnboardingStep(1)}
              className="text-xs text-slate-500"
            >
              Reset
            </button>
          </div>

          {/* Stepper bubbles 1 - 2 - 3 */}
          <div className="flex items-center justify-center gap-3">
            {[1, 2, 3, 4].map((step) => (
              <div key={step} className="flex items-center gap-2">
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                    onboardingStep === step
                      ? 'bg-red-600 text-white'
                      : onboardingStep > step
                      ? 'bg-emerald-600 text-white'
                      : 'bg-slate-100 text-slate-400'
                  }`}
                >
                  {onboardingStep > step ? '✓' : step}
                </div>
                {step < 4 && <div className="w-6 h-0.5 bg-slate-200" />}
              </div>
            ))}
          </div>

          {/* STEP 1: Buat Akun Partner */}
          {onboardingStep === 1 && (
            <div className="space-y-3 pt-2">
              <h4 className="text-sm font-bold text-slate-900">1. Buat Akun Partner</h4>
              <p className="text-xs text-slate-500">Daftarkan bisnis atau lokasi Anda</p>

              <div>
                <label className="text-[11px] font-semibold text-slate-700 block mb-1">Nama Lengkap *</label>
                <input
                  type="text"
                  value={partnerName}
                  onChange={(e) => setPartnerName(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200"
                />
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-700 block mb-1">Email Bisnis *</label>
                <input
                  type="email"
                  value={businessEmail}
                  onChange={(e) => setBusinessEmail(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200"
                />
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-700 block mb-1">Nomor WhatsApp / HP *</label>
                <input
                  type="text"
                  defaultValue="0812 3456 7890"
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200"
                />
              </div>

              <button
                onClick={() => setOnboardingStep(2)}
                className="w-full py-2.5 rounded-xl bg-red-600 text-white text-xs font-bold hover:bg-red-700 transition shadow-xs mt-2"
              >
                Lanjutkan ke Lokasi
              </button>
            </div>
          )}

          {/* STEP 2: Verifikasi Lokasi */}
          {onboardingStep === 2 && (
            <div className="space-y-3 pt-2">
              <h4 className="text-sm font-bold text-slate-900">2. Verifikasi Lokasi Usaha</h4>
              <p className="text-xs text-slate-500">Lengkapi informasi fisik lokasi Wi-Fi</p>

              <div>
                <label className="text-[11px] font-semibold text-slate-700 block mb-1">Jenis Lokasi *</label>
                <select
                  value={venueType}
                  onChange={(e) => setVenueType(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white"
                >
                  <option>Coffee Shop / Restoran</option>
                  <option>Coworking Space</option>
                  <option>Kampus / Perpustakaan</option>
                  <option>Hotel / Penginapan</option>
                </select>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-700 block mb-1">Nama Lokasi / Usaha *</label>
                <input
                  type="text"
                  value={venueName}
                  onChange={(e) => setVenueName(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200"
                />
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-700 block mb-1">Alamat Lengkap *</label>
                <input
                  type="text"
                  value={venueAddress}
                  onChange={(e) => setVenueAddress(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200"
                />
              </div>

              {/* Pin Map placeholder */}
              <div className="h-20 bg-slate-100 rounded-xl border border-slate-200 flex items-center justify-center text-xs text-slate-500 gap-1.5">
                <MapPin className="w-4 h-4 text-red-600" />
                <span>Titik Koordinat Geofence: Terverifikasi (Semarang)</span>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => setOnboardingStep(1)}
                  className="flex-1 py-2.5 rounded-xl bg-slate-100 text-slate-700 text-xs font-semibold"
                >
                  Kembali
                </button>
                <button
                  onClick={() => setOnboardingStep(3)}
                  className="flex-1 py-2.5 rounded-xl bg-red-600 text-white text-xs font-bold hover:bg-red-700 transition"
                >
                  Pilih Paket
                </button>
              </div>
            </div>
          )}

          {/* STEP 3: Pilih Paket Partner */}
          {onboardingStep === 3 && (
            <div className="space-y-3 pt-2">
              <h4 className="text-sm font-bold text-slate-900">3. Pilih Paket Partner</h4>
              <p className="text-xs text-slate-500">Sesuaikan dengan kapasitas pengunjung</p>

              <div
                onClick={() => setSelectedPlan('Basic')}
                className={`p-3 rounded-2xl border cursor-pointer transition ${
                  selectedPlan === 'Basic'
                    ? 'border-red-600 bg-red-50/50'
                    : 'border-slate-200'
                }`}
              >
                <div className="flex justify-between items-center">
                  <span className="font-bold text-xs text-slate-900">Basic</span>
                  <span className="text-[10px] font-bold text-emerald-600">Gratis Aktivasi</span>
                </div>
                <p className="text-[11px] text-slate-500 mt-0.5">Wi-Fi & Akses MoreAI hingga 50 pengguna</p>
              </div>

              <div
                onClick={() => setSelectedPlan('Business')}
                className={`p-3 rounded-2xl border cursor-pointer transition ${
                  selectedPlan === 'Business'
                    ? 'border-red-600 bg-red-50/50 ring-2 ring-red-500/10'
                    : 'border-slate-200'
                }`}
              >
                <div className="flex justify-between items-center">
                  <span className="font-bold text-xs text-slate-900">Business (Rekomendasi)</span>
                  <span className="text-[10px] font-bold text-red-600">Rp 149.000 /bln</span>
                </div>
                <p className="text-[11px] text-slate-500 mt-0.5">Wi-Fi & Akses MoreAI hingga 200 pengguna</p>
              </div>

              <div
                onClick={() => setSelectedPlan('Enterprise')}
                className={`p-3 rounded-2xl border cursor-pointer transition ${
                  selectedPlan === 'Enterprise'
                    ? 'border-red-600 bg-red-50/50'
                    : 'border-slate-200'
                }`}
              >
                <div className="flex justify-between items-center">
                  <span className="font-bold text-xs text-slate-900">Enterprise</span>
                  <span className="text-[10px] font-bold text-slate-700">Hubungi Kami</span>
                </div>
                <p className="text-[11px] text-slate-500 mt-0.5">Kapasitas 500+ pengguna & dashboard kustom</p>
              </div>

              <button
                onClick={() => setOnboardingStep(4)}
                className="w-full py-2.5 rounded-xl bg-red-600 text-white text-xs font-bold hover:bg-red-700 transition shadow-xs mt-2"
              >
                Aktifkan Partner
              </button>
            </div>
          )}

          {/* STEP 4: Partner Aktif (Sheet 4) */}
          {onboardingStep === 4 && (
            <div className="text-center space-y-4 pt-3">
              <div className="w-16 h-16 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-10 h-10" />
              </div>

              <div>
                <h4 className="text-base font-bold text-slate-900">Partner Aktif!</h4>
                <p className="text-xs text-slate-500 mt-1 max-w-xs mx-auto">
                  Selamat! Anda telah resmi menjadi Partner Wi-Fi & AI Access bersama IndiHome.
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-left text-xs space-y-2">
                <div className="flex items-center gap-2 text-slate-700">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>Wi-Fi aktif untuk pelanggan venue</span>
                </div>
                <div className="flex items-center gap-2 text-slate-700">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>Akses MoreAI siap digunakan via QR scan</span>
                </div>
                <div className="flex items-center gap-2 text-slate-700">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>Kelola lokasi, pengguna, dan laporan analitik</span>
                </div>
              </div>

              <button
                onClick={() => setPartnerMode('dashboard')}
                className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition shadow-xs"
              >
                Masuk ke Dashboard Partner
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
