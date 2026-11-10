'use client';

import React, { useState } from 'react';
import {
  X,
  Smartphone,
  ChevronRight,
  Layers,
  Sparkles,
  Wifi,
  Building2,
  CheckCircle2,
  GraduationCap,
  FileText,
  Search,
} from 'lucide-react';
import { NavigationTab } from '@/types/moreai';

interface ScreenGalleryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectScreen: (tab: NavigationTab) => void;
  currentScreen: NavigationTab;
}

export const ScreenGalleryModal: React.FC<ScreenGalleryModalProps> = ({
  isOpen,
  onClose,
  onSelectScreen,
  currentScreen,
}) => {
  const [activeSheet, setActiveSheet] = useState<1 | 2 | 3 | 4 | 5 | 6>(6);

  if (!isOpen) return null;

  const sheets = [
    { id: 6, title: 'Sheet 6: AI Agent & Workflow (12 Halaman)', icon: Layers },
    { id: 1, title: 'Sheet 1: Customer Workspace (11 Halaman)', icon: Smartphone },
    { id: 2, title: 'Sheet 2: Mobile First Core (10 Halaman)', icon: Sparkles },
    { id: 3, title: 'Sheet 3: Captive Portal Customer (13 Halaman)', icon: Wifi },
    { id: 4, title: 'Sheet 4: Partner Wi-Fi & AI B2B (13 Halaman)', icon: Building2 },
    { id: 5, title: 'Sheet 5: Wi-Fi Management & Tools (14 Halaman)', icon: Wifi },
  ] as const;

  const screensBySheet: Record<number, { id: NavigationTab; title: string; desc: string; sheetTag: string }[]> = {
    6: [
      { id: 'splash', title: '1. Splash Screen', desc: 'Monas & Jakarta Skyline silhouette, "Akses AI untuk Semua"', sheetTag: 'Sheet 6 #1' },
      { id: 'onboarding', title: '2. Onboarding Carousel', desc: 'Ilustrasi kreator muda dengan laptop & 4 ikon AI melayang', sheetTag: 'Sheet 6 #2' },
      { id: 'login', title: '3. Login / Registrasi', desc: 'Tabs Masuk/Daftar, Email/HP, Password, Google/Apple/Partner SSO', sheetTag: 'Sheet 6 #3' },
      { id: 'home', title: '4. Home Dashboard', desc: 'Selamat Pagi Andi Pratama, prompt input, 4 quick buttons, recent tasks', sheetTag: 'Sheet 6 #4' },
      { id: 'chat', title: '5. Workspace Chat', desc: 'Chat AI & Research: strategi marketing UMKM coffee shop', sheetTag: 'Sheet 6 #5' },
      { id: 'agents', title: '6. AI Agent Studio', desc: 'Research, Marketing, Writing, Design, & Data Analyst agents', sheetTag: 'Sheet 6 #6' },
      { id: 'workflow_progress', title: '7. Workflow Progress', desc: 'Campaign Launch Project (75%), 4 agent pipeline stepper', sheetTag: 'Sheet 6 #7' },
      { id: 'artifacts_result', title: '8. Hasil & Artifacts', desc: 'Pekerjaan selesai, Proposal_Marketing.pdf, Campaign.png, Calendar.xlsx', sheetTag: 'Sheet 6 #8' },
      { id: 'benefits', title: '9. AI Credit Center', desc: 'Partner Free ISP, Saldo 8.500 (2.5M token), riwayat pemakaian', sheetTag: 'Sheet 6 #9' },
      { id: 'files', title: '10. Files & Library', desc: 'Pencarian berkas, kategori Dokumen, Gambar, Lainnya & FAB (+)', sheetTag: 'Sheet 6 #10' },
      { id: 'profile', title: '11. Settings / Pengaturan', desc: 'Profil Andi Pratama, Notifikasi, Keamanan, Mode Gelap, Keluar', sheetTag: 'Sheet 6 #11' },
      { id: 'partner_access_promo', title: '12. Partner Access', desc: 'Global Partner ISP x MoreAI AI Credit Free untuk Pelanggan Partner', sheetTag: 'Sheet 6 #12' },
    ],
    1: [
      { id: 'splash', title: 'Login & Onboarding', desc: 'Robot asisten melambai, Monas, Masuk & Daftar Akun', sheetTag: 'Sheet 1 #1' },
      { id: 'home', title: 'Beranda Customer', desc: 'Selamat Pagi Indonesia, 5 quick icons, Proyek Terbaru', sheetTag: 'Sheet 1 #2' },
      { id: 'chat', title: 'Chat AI', desc: 'Percakapan MoreAI dengan quick suggestion chips', sheetTag: 'Sheet 1 #3' },
      { id: 'create', title: 'Create Studio', desc: 'Tulis Konten, Generate Gambar, Ringkasan Dokumen, Terjemah', sheetTag: 'Sheet 1 #4' },
      { id: 'tools_catalog', title: 'Tools Catalog', desc: 'Analisis Data, Ringkasan PDF, Mind Map, Planner, Desain Gambar', sheetTag: 'Sheet 1 #5' },
      { id: 'files', title: 'Files Saya', desc: 'Laporan_Marketing.pdf, Ide_Konten.docx, Gambar_Produk.png', sheetTag: 'Sheet 1 #6' },
      { id: 'profile', title: 'Profile (Budi Santoso)', desc: 'Budi Santoso, Akun Saya, Benefit & Credit, Bantuan & FAQ', sheetTag: 'Sheet 1 #7' },
      { id: 'benefits', title: 'Benefit & Credit', desc: 'AI Credit Free Partner ISP 100.000 Poin, Aktifkan Sekarang', sheetTag: 'Sheet 1 #8' },
      { id: 'tasks', title: 'Tasks Management', desc: 'Daftar tugas aktif & selesai dengan poin kredit', sheetTag: 'Sheet 1 #9' },
      { id: 'research', title: 'Research AI', desc: 'Topik Populer: AI untuk Pendidikan, Dampak AI di UMKM', sheetTag: 'Sheet 1 #10' },
      { id: 'analytics', title: 'Analytics View', desc: 'Total Aktivitas 12.5K (+12%), grafik wave visual merah', sheetTag: 'Sheet 1 #11' },
    ],
    2: [
      { id: 'home', title: 'Beranda Mobile First', desc: 'Akses MoreAI di mana saja, kapan saja, dari perangkat apa saja', sheetTag: 'Sheet 2 #1' },
      { id: 'chat', title: 'Chat AI Assistant', desc: 'Bilah pesan interaktif dengan sumber terverifikasi', sheetTag: 'Sheet 2 #2' },
      { id: 'research', title: 'Research Pasar', desc: 'Tren AI di Indonesia, Strategi Digital Marketing', sheetTag: 'Sheet 2 #3' },
      { id: 'create', title: 'Create Multi-Format', desc: 'Teks ke Dokumen, Gambar ke Gambar, Presentasi AI', sheetTag: 'Sheet 2 #4' },
      { id: 'analyse', title: 'Analyze Dropzone', desc: 'Unggah file atau seret di sini (PDF, DOC, XLS), analisis KPI', sheetTag: 'Sheet 2 #5' },
      { id: 'code', title: 'Code Runner Python', desc: 'def greet(name), tombol Run Code, Hasil Output Hello MoreAI!', sheetTag: 'Sheet 2 #6' },
      { id: 'tasks', title: 'Tasks List', desc: 'Checklist tugas pemasaran & riset harian', sheetTag: 'Sheet 2 #7' },
      { id: 'files', title: 'File Explorer', desc: 'Folder Dokumen, Gambar, Presentasi', sheetTag: 'Sheet 2 #8' },
      { id: 'profile', title: 'Profile (Siti Nurhaliza)', desc: 'Siti Nurhaliza, Sisa Kuota 10.000 Credits', sheetTag: 'Sheet 2 #9' },
      { id: 'benefits', title: 'Benefit Partner ISP', desc: 'Akses Model AI Lokal, Integrasi Global Network', sheetTag: 'Sheet 2 #10' },
    ],
    3: [
      { id: 'splash', title: '1. Splash Screen Captive', desc: 'Internet Terhubung, AI Memberdayakan', sheetTag: 'Sheet 3 #1' },
      { id: 'login', title: '2. Login / Registrasi Tamu', desc: 'Masuk dengan Akun Partner ISP atau Daftar Akun Baru', sheetTag: 'Sheet 3 #2' },
      { id: 'captive_terms', title: '3. Syarat & Ketentuan Akses', desc: 'Persetujuan kebijakan jaringan & kuota AI sponsor', sheetTag: 'Sheet 3 #3' },
      { id: 'captive_otp', title: '4. Verifikasi OTP Nomor HP', desc: 'Input 6 digit kode SMS / WhatsApp verifikasi tamu', sheetTag: 'Sheet 3 #4' },
      { id: 'captive_success', title: '5. Sukses Terhubung Wi-Fi', desc: 'Notifikasi berhasil terkoneksi, bonus 100K poin aktif', sheetTag: 'Sheet 3 #5' },
      { id: 'captive', title: '6. Beranda Captive Customer', desc: 'Alur interaktif dan ringkasan portal tamu di venue', sheetTag: 'Sheet 3 #6' },
      { id: 'tools_catalog', title: '7. MoreAI Tools Tamu', desc: 'Katalog tools ringkasan teks, terjemahan, dan generator gambar', sheetTag: 'Sheet 3 #7' },
      { id: 'edutech', title: '8. EduTech Belajar AI', desc: 'Belajar lebih mudah dengan AI, daftar kursus', sheetTag: 'Sheet 3 #8' },
      { id: 'benefits', title: '9. Benefit & Credit Portal', desc: 'AI Credit Anda 100.000 Poin, periode berlaku', sheetTag: 'Sheet 3 #9' },
      { id: 'wifi_session', title: '10. Sesi Penggunaan Wi-Fi', desc: 'Monitor countdown durasi sesi & penggunaan kuota real-time', sheetTag: 'Sheet 3 #10' },
      { id: 'account_upgrade', title: '11. Upgrade ke Akun Penuh', desc: 'Buka penyimpanan permanen cloud & agen tanpa batas', sheetTag: 'Sheet 3 #11' },
      { id: 'notifications', title: '12. Notifikasi Pelanggan', desc: 'Promo AI Credit, Update Layanan Wi-Fi, Tips Produktivitas', sheetTag: 'Sheet 3 #12' },
      { id: 'help_faq', title: '13. Bantuan & FAQ', desc: 'Accordion tanya-jawab & Layanan Pelanggan 24/7', sheetTag: 'Sheet 3 #13' },
    ],
    4: [
      { id: 'partner_login', title: '1. Login Mitra Venue B2B', desc: 'Otentikasi khusus pemilik kafe, resto, & coworking', sheetTag: 'Sheet 4 #1' },
      { id: 'partner', title: '2-3. Dashboard Partner Utama', desc: 'Halo Farhan - CoffeeHouse Semarang, status aktif, 126 pengunjung', sheetTag: 'Sheet 4 #2-3' },
      { id: 'partner_live_sessions', title: '4. Live Session Monitor', desc: 'Daftar perangkat tamu yang sedang aktif menggunakan AI', sheetTag: 'Sheet 4 #4' },
      { id: 'partner_gateway_config', title: '5. Konfigurasi SSID & Gateway', desc: 'Setup MikroTik Hotspot, UniFi, & ONT Fiber Global ISP', sheetTag: 'Sheet 4 #5' },
      { id: 'partner_staff', title: '6. Manajemen Staf Venue', desc: 'Kelola hak akses kasir, supervisor, & tim front desk', sheetTag: 'Sheet 4 #6' },
      { id: 'partner_locations', title: '7. Kelola Lokasi Cabang', desc: 'CoffeeHouse Semarang, Resto Nusantara, Coworking Space', sheetTag: 'Sheet 4 #7' },
      { id: 'partner_qr', title: '8. QR Akses Meja & Kasir', desc: 'QR Code resmi Wi-Fi & MoreAI resolusi tinggi siap cetak', sheetTag: 'Sheet 4 #8' },
      { id: 'partner_analytics', title: '9-10. Data Pengguna & Laporan', desc: '1.248 Total Pengguna, 2.976 Akses AI, fitur AI terfavorit', sheetTag: 'Sheet 4 #9-10' },
      { id: 'partner_packages', title: '11. Kelola Paket Partner', desc: 'Paket Basic, Business (Aktif), Enterprise', sheetTag: 'Sheet 4 #11' },
      { id: 'partner_promo', title: '12. Promo & Materi Pemasaran', desc: 'Poster A3, X-Banner Standing, Stiker Meja, Template Medsos', sheetTag: 'Sheet 4 #12' },
      { id: 'partner_api_settings', title: '13. API & Webhook Gateway', desc: 'Manajemen live API key mitra & endpoint callback realtime', sheetTag: 'Sheet 4 #13' },
    ],
    5: [
      { id: 'splash', title: '1. Splash Screen Wi-Fi', desc: 'Akses internet cepat & AI terintegrasi', sheetTag: 'Sheet 5 #1' },
      { id: 'register', title: '2. Daftar Akun Baru', desc: 'Nama Lengkap, Email, Nomor HP, Password, Syarat & Ketentuan', sheetTag: 'Sheet 5 #2' },
      { id: 'welcome_success', title: '3. Selamat Datang di MoreAI', desc: 'Kartu rumah dengan sinyal Wi-Fi, tombol Mulai', sheetTag: 'Sheet 5 #3' },
      { id: 'home', title: '4. Dashboard Pelanggan', desc: 'Beranda utama ekosistem Global Partner ISP & MoreAI', sheetTag: 'Sheet 5 #4' },
      { id: 'speedtest', title: '5. Speedtest & Status Sinyal', desc: 'Uji kecepatan 104.2 Mbps, latency 9ms, status fiber', sheetTag: 'Sheet 5 #5' },
      { id: 'wifi', title: '6. Wi-Fi Management 100 Mbps', desc: 'Router status, IP gateway, ganti password, atur jadwal', sheetTag: 'Sheet 5 #6' },
      { id: 'devices_connected', title: '7. Perangkat Terhubung (5)', desc: 'iPhone 15, Laptop ASUS, Samsung Galaxy, Smart TV, Smart Home', sheetTag: 'Sheet 5 #7' },
      { id: 'device_access_control', title: '8. Kontrol Akses & Bandwidth', desc: 'Limit kecepatan per device & Safe Browsing anak', sheetTag: 'Sheet 5 #8' },
      { id: 'tools_catalog', title: '9. MoreAI Tools Spesial', desc: 'Chat AI, Image Gen, Document Creator, Code, Translator, Voice', sheetTag: 'Sheet 5 #9' },
      { id: 'edutech', title: '10. AI Learning Hub', desc: 'Koleksi materi edukasi: Mengenal AI, Prompting Efektif', sheetTag: 'Sheet 5 #10' },
      { id: 'edutech_lesson', title: '11. Detail Modul Belajar', desc: 'Mengenal AI untuk Pemula (5 menit • 4.8 bintang), silabus', sheetTag: 'Sheet 5 #11' },
      { id: 'partner_vouchers', title: '12. Voucher Diskon Mitra Kafe', desc: 'Klaim diskon Rp 50.000, promo kopi, & ekstra kredit AI', sheetTag: 'Sheet 5 #12' },
      { id: 'token_ledger', title: '13. Riwayat Transaksi & Ledger', desc: 'Audit saldo token, mutasi debit/kredit, & referensi hash', sheetTag: 'Sheet 5 #13' },
      { id: 'security_settings', title: '14. Pusat Keamanan & 2FA', desc: 'Autentikasi 2-faktor, ubah kata sandi, & sesi aktif', sheetTag: 'Sheet 5 #14' },
    ],
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-3 sm:p-5 animate-fadeIn">
      <div className="w-full max-w-2xl bg-white rounded-3xl shadow-2xl border border-slate-100 flex flex-col max-h-[90vh] overflow-hidden">
        {/* Top Title Bar */}
        <div className="p-4 sm:p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/70">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-red-600 animate-pulse" />
              <h2 className="text-base sm:text-lg font-black text-slate-900 tracking-tight">
                Direktori Seluruh Halaman UI/UX (Sheet 1 — 6)
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Pilih dan buka langsung halaman apa pun dari 6 lembar desain referensi
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Sheet Selector Tabs */}
        <div className="px-4 py-2 bg-white border-b border-slate-100 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
          {sheets.map((s) => (
            <button
              key={s.id}
              onClick={() => setActiveSheet(s.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition flex items-center gap-1.5 shrink-0 ${
                activeSheet === s.id
                  ? 'bg-red-600 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              <s.icon className="w-3.5 h-3.5" />
              <span>Sheet {s.id}</span>
            </button>
          ))}
        </div>

        {/* Sheet Description Banner */}
        <div className="px-5 py-2.5 bg-red-50/50 border-b border-red-100 flex items-center justify-between">
          <span className="text-xs font-bold text-red-900">
            {sheets.find((s) => s.id === activeSheet)?.title}
          </span>
          <span className="text-[10px] text-red-600 font-semibold bg-white px-2 py-0.5 rounded-full border border-red-200">
            {screensBySheet[activeSheet].length} Halaman Siap
          </span>
        </div>

        {/* Screens Grid for the Active Sheet */}
        <div className="p-4 sm:p-5 overflow-y-auto space-y-2 flex-1">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {screensBySheet[activeSheet].map((item) => {
              const isCurrent = currentScreen === item.id;
              return (
                <div
                  key={item.sheetTag + item.id}
                  onClick={() => {
                    onSelectScreen(item.id);
                    onClose();
                  }}
                  className={`cursor-pointer p-3.5 rounded-2xl border transition flex items-start justify-between gap-3 group ${
                    isCurrent
                      ? 'bg-red-50 border-red-400 ring-2 ring-red-500/20'
                      : 'bg-white border-slate-100 hover:border-red-200 hover:bg-slate-50/80 shadow-2xs'
                  }`}
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5 mb-1">
                      <span className="text-[9px] font-bold uppercase tracking-wider text-red-600 bg-red-50 px-1.5 py-0.5 rounded-md border border-red-200">
                        {item.sheetTag}
                      </span>
                      {isCurrent && (
                        <span className="text-[9px] font-bold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded-md">
                          Sedang Dibuka
                        </span>
                      )}
                    </div>
                    <h3 className="text-xs font-bold text-slate-900 group-hover:text-red-600 transition truncate">
                      {item.title}
                    </h3>
                    <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-2 leading-relaxed">
                      {item.desc}
                    </p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-red-600 group-hover:translate-x-0.5 transition shrink-0 mt-1" />
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="p-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 px-5">
          <span>Total 70+ halaman &amp; varian alur terimplementasi</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs"
          >
            Tutup Direktori
          </button>
        </div>
      </div>
    </div>
  );
};
