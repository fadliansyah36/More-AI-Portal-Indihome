'use client';

import React, { useEffect, useState } from 'react';
import {
  Building2,
  MapPin,
  QrCode,
  BarChart3,
  Package,
  CheckCircle2,
  Plus,
  ArrowLeft,
  Sparkles,
} from 'lucide-react';
import { partnerApi } from '@/lib/api/client';
import type { PartnerContext, PartnerLocationRecord, PartnerTenantOption } from '@/lib/api/client';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';

export interface PartnerPortalViewProps {
  initialMode?: 'dashboard' | 'onboarding' | 'qr' | 'locations' | 'analytics' | 'packages' | 'promo';
  onNavigateTab?: (tab: NavigationTab) => void;
}

const addressLabel = (value: unknown): string => {
  if (typeof value === 'string') return value;
  if (!value || typeof value !== 'object') return 'Alamat belum tersedia';
  const address = value as Record<string, unknown>;
  return [
    address.formatted_address, address.label, address.street,
    address.city, address.province, address.postal_code,
  ].filter((part): part is string => typeof part === 'string' && part.trim().length > 0).join(', ')
    || 'Alamat belum tersedia';
};

export const PartnerPortalView: React.FC<PartnerPortalViewProps> = ({
  initialMode = 'dashboard',
  onNavigateTab,
}) => {
  const { showToast } = useToast();
  const [partnerMode, setPartnerMode] = useState<'dashboard' | 'onboarding' | 'qr' | 'locations' | 'analytics' | 'packages' | 'promo'>(initialMode);
  const [onboardingStep, setOnboardingStep] = useState<1 | 2 | 3 | 4>(1);
  const [locations, setLocations] = useState<PartnerLocationRecord[]>([]);
  const [partnerContext, setPartnerContext] = useState<PartnerContext | null>(null);
  const [partnerTenants, setPartnerTenants] = useState<PartnerTenantOption[]>([]);
  const [selectedPartnerId, setSelectedPartnerId] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [partnerError, setPartnerError] = useState<string | null>(null);

  // Registration fields remain blank until a persisted onboarding API is available.
  const [partnerName, setPartnerName] = useState('');
  const [businessEmail, setBusinessEmail] = useState('');
  const [venueName, setVenueName] = useState('');
  const [venueType, setVenueType] = useState('Coffee Shop / Restoran');
  const [venueAddress, setVenueAddress] = useState('');

  useEffect(() => {
    let active = true;
    partnerApi.tenants()
      .then((tenants) => {
        if (!active) return;
        setPartnerTenants(tenants);
        if (tenants.length === 1) setSelectedPartnerId(tenants[0].tenant.id);
        if (tenants.length === 0) setPartnerError('Tidak ada tenant Partner aktif pada akun ini.');
      })
      .catch((error: unknown) => {
        if (!active) return;
        const message = error instanceof Error ? error.message : 'Daftar tenant Partner tidak dapat dimuat.';
        setPartnerError(message);
        showToast(message, 'error');
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });
    return () => { active = false; };
  }, [showToast]);

  useEffect(() => {
    if (!selectedPartnerId) return;
    let active = true;
    setIsLoading(true);
    setPartnerError(null);
    setPartnerContext(null);
    setLocations([]);
    Promise.all([
      partnerApi.context(selectedPartnerId),
      partnerApi.locations(selectedPartnerId),
    ])
      .then(([context, rows]) => {
        if (!active) return;
        setPartnerContext(context);
        setVenueName(context.tenant.display_name || context.tenant.legal_name || '');
        setLocations(rows);
      })
      .catch((error: unknown) => {
        if (!active) return;
        const message = error instanceof Error ? error.message : 'Data tenant Partner tidak dapat dimuat.';
        setPartnerError(message);
        showToast(message, 'error');
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });
    return () => { active = false; };
  }, [selectedPartnerId, showToast]);

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
            Kelola lokasi berdasarkan tenant dan role Partner yang diverifikasi server
          </p>
          {partnerTenants.length > 1 && (
            <label className="mt-2 block max-w-sm text-xs font-medium text-slate-600">
              Tenant aktif
              <select
                value={selectedPartnerId}
                onChange={(event) => setSelectedPartnerId(event.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800"
              >
                <option value="">Pilih tenant Partner</option>
                {partnerTenants.map((item) => (
                  <option key={item.tenant.id} value={item.tenant.id}>
                    {item.tenant.display_name || item.tenant.legal_name}
                  </option>
                ))}
              </select>
            </label>
          )}
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

      {partnerError && (
        <div role="alert" className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
          {partnerError}
        </div>
      )}

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
                  <h2 className="text-sm font-bold text-slate-900">Halo, {partnerContext?.tenant.display_name || 'Partner'} 👋</h2>
                </div>
                <p className="text-xs text-slate-500 font-medium">{venueName}</p>
                <div className="flex items-center gap-1.5 text-[10px] text-emerald-600 font-semibold mt-0.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span>Status Tenant: {partnerContext?.tenant.status === 'active' ? 'Aktif' : 'Perlu verifikasi'}</span>
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

          {/* Live tenant inventory; analytics stay unreported until their API exists. */}
          <div className="grid grid-cols-2 gap-2.5">
            <div className="p-4 rounded-3xl bg-white border border-slate-100 shadow-xs">
              <div className="flex items-center justify-between text-slate-400 mb-1">
                <span className="text-xs font-semibold">Lokasi Terdaftar</span>
                <Building2 className="w-4 h-4 text-blue-500" />
              </div>
              <span className="text-2xl font-black text-slate-900 tracking-tight">{isLoading ? '—' : locations.length}</span>
              <span className="text-[10px] text-slate-500 block mt-0.5">Dari tenant yang terautentikasi</span>
            </div>
            <div className="p-4 rounded-3xl bg-white border border-slate-100 shadow-xs">
              <div className="flex items-center justify-between text-slate-400 mb-1">
                <span className="text-xs font-semibold">Akses AI</span>
                <Sparkles className="w-4 h-4 text-red-500" />
              </div>
              <span className="text-sm font-bold text-slate-700">Belum tersedia</span>
              <span className="text-[10px] text-slate-500 block mt-1">Menunggu endpoint analytics partner</span>
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

          {/* Locations Preview: real locations only. */}
          <div className="bg-white rounded-3xl p-4 border border-slate-100 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Titik Wi-Fi Partner Terdaftar</h3>
              <button onClick={() => setPartnerMode('locations')} className="text-xs text-red-600 font-semibold">Lihat Semua</button>
            </div>
            {isLoading ? (
              <p className="py-4 text-center text-xs text-slate-500">Memuat lokasi tenant…</p>
            ) : locations.length === 0 ? (
              <p className="rounded-xl bg-slate-50 p-4 text-center text-xs text-slate-500">Belum ada lokasi yang terdaftar.</p>
            ) : (
              <div className="space-y-2">
                {locations.slice(0, 3).map((loc) => (
                  <div key={loc.id} className="p-3 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-between gap-2">
                    <div>
                      <h4 className="text-xs font-bold text-slate-900">{loc.name}</h4>
                      <span className="text-[10px] text-slate-500">{addressLabel(loc.address)}</span>
                    </div>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${loc.status === 'active' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-200 text-slate-600'}`}>
                      {loc.status === 'active' ? 'Aktif' : 'Nonaktif'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* QR access is not simulated before the backend issues a tenant artifact. */}
      {partnerMode === 'qr' && (
        <div className="bg-white rounded-3xl p-6 border border-slate-100 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <button onClick={() => setPartnerMode('dashboard')} className="p-1 rounded-lg text-slate-400 hover:text-slate-700">
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h3 className="text-sm font-bold text-slate-900">QR Akses Wi-Fi & MoreAI</h3>
            <div className="w-5" />
          </div>
          <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center">
            <QrCode className="mx-auto h-10 w-10 text-slate-400" />
            <p className="mt-3 text-sm font-semibold text-slate-800">QR belum diterbitkan</p>
            <p className="mt-1 text-xs text-slate-500">QR akan tersedia setelah provisioning gateway dan artifact API diaktifkan.</p>
            {locations[0] && <p className="mt-3 text-xs font-medium text-slate-700">{locations[0].name}</p>}
          </div>
        </div>
      )}

      {/* Tenant-scoped locations loaded from FastAPI. */}
      {partnerMode === 'locations' && (
        <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <button onClick={() => setPartnerMode('dashboard')} className="p-1 rounded-lg text-slate-400 hover:text-slate-700">
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h3 className="text-sm font-bold text-slate-900">Kelola Lokasi & Cabang</h3>
            <button type="button" disabled title="Endpoint pendaftaran lokasi belum tersedia" className="text-xs font-bold text-slate-400 flex items-center gap-1 cursor-not-allowed">
              <Plus className="w-3.5 h-3.5" /><span>Tambah</span>
            </button>
          </div>
          {isLoading ? (
            <p className="py-8 text-center text-xs text-slate-500">Memuat lokasi tenant…</p>
          ) : locations.length === 0 ? (
            <p className="rounded-xl bg-slate-50 p-4 text-center text-xs text-slate-500">Belum ada lokasi yang terdaftar pada tenant ini.</p>
          ) : (
            <div className="space-y-3">
              {locations.map((loc) => (
                <div key={loc.id} className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <h4 className="text-xs font-bold text-slate-900">{loc.name}</h4>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${loc.status === 'active' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-200 text-slate-600'}`}>
                      {loc.status === 'active' ? 'Aktif' : 'Nonaktif'}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500">{addressLabel(loc.address)}</p>
                  <p className="text-[10px] text-slate-400">Akses data dibatasi oleh membership dan tenant server-side.</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* No fabricated analytics: waiting for partner reporting API and RLS contract. */}
      {partnerMode === 'analytics' && (
        <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <button onClick={() => setPartnerMode('dashboard')} className="p-1 rounded-lg text-slate-400 hover:text-slate-700">
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h3 className="text-sm font-bold text-slate-900">Laporan & Analitik Partner</h3>
            <div className="w-5" />
          </div>
          <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center">
            <BarChart3 className="mx-auto h-9 w-9 text-slate-400" />
            <p className="mt-3 text-sm font-semibold text-slate-800">Data analitik belum tersedia</p>
            <p className="mt-1 text-xs text-slate-500">Pengguna, akses AI, dan distribusi fitur hanya akan ditampilkan setelah endpoint reporting partner tersedia.</p>
          </div>
        </div>
      )}

      {/* Package catalogue and pricing are not yet backed by an approved API contract. */}
      {partnerMode === 'packages' && (
        <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <button onClick={() => setPartnerMode('dashboard')} className="p-1 rounded-lg text-slate-400 hover:text-slate-700">
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h3 className="text-sm font-bold text-slate-900">Paket Partner</h3>
            <div className="w-5" />
          </div>
          <p className="rounded-2xl bg-slate-50 p-4 text-xs text-slate-600">
            Paket, harga, kuota, dan masa aktif belum tersedia dari FastAPI. Tidak ada perubahan paket yang dikirim atau disimulasikan dari layar ini.
          </p>
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
                  placeholder="Masukkan nomor WhatsApp bisnis"
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
                <span>Verifikasi geofence akan dilakukan melalui layanan server</span>
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

          {/* Package selection remains disabled until package and onboarding APIs are approved. */}
          {onboardingStep === 3 && (
            <div className="space-y-3 pt-2">
              <h4 className="text-sm font-bold text-slate-900">3. Paket Partner</h4>
              <p className="rounded-2xl bg-slate-50 p-4 text-xs text-slate-600">
                Katalog paket dan proses aktivasi belum terhubung ke backend. Data registrasi belum disimpan dan tenant tidak akan diaktifkan dari form simulasi.
              </p>
              <button onClick={() => setPartnerMode('dashboard')} className="w-full py-2.5 rounded-xl bg-slate-100 text-slate-700 text-xs font-bold">
                Kembali ke Dashboard
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
                <h4 className="text-base font-bold text-slate-900">Status Pendaftaran Belum Tersimpan</h4>
                <p className="text-xs text-slate-500 mt-1 max-w-xs mx-auto">
                  Layar ini belum terhubung ke endpoint pendaftaran Partner. Tidak ada aktivasi tenant yang dilakukan.
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-left text-xs space-y-2">
                <div className="flex items-center gap-2 text-slate-700">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>Status Wi-Fi belum diverifikasi oleh backend</span>
                </div>
                <div className="flex items-center gap-2 text-slate-700">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>QR belum diterbitkan oleh backend</span>
                </div>
                <div className="flex items-center gap-2 text-slate-700">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>Fitur tenant aktif mengikuti role dan izin server</span>
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
