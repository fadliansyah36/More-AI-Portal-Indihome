'use client';

import React, { useState } from 'react';
import { ArrowLeft, Search, ChevronDown, ChevronUp, Headphones, Phone } from 'lucide-react';
import { useToast } from '@/components/ui/toast-context';

interface HelpFaqViewProps {
  onBack: () => void;
}

export const HelpFaqView: React.FC<HelpFaqViewProps> = ({ onBack }) => {
  const { showToast } = useToast();
  const [searchQuery, setSearchQuery] = useState('');
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const faqs = [
    {
      q: 'Cara mengakses MoreAI?',
      a: 'Buka browser Anda dan kunjungi portal MoreAI saat terhubung ke jaringan internet Global Partner ISP atau Wi-Fi mitra. Anda dapat langsung menginstal PWA ke home screen smartphone tanpa melalui app store.',
    },
    {
      q: 'Kenapa Wi-Fi saya tidak bisa terhubung?',
      a: 'Pastikan sinyal Wi-Fi Partner terdeteksi, masukkan kata sandi yang valid, dan setujui Syarat & Ketentuan pada captive portal yang muncul di layar perangkat Anda.',
    },
    {
      q: 'Cara mendapatkan AI Credit?',
      a: 'Benefit AI Credit hanya tersedia jika backend mengonfirmasi entitlement sponsor aktif. Besaran dan masa berlaku mengikuti konfigurasi partner.',
    },
    {
      q: 'Bagaimana cara menggunakan AI Tools?',
      a: 'Pilih kategori tools yang Anda inginkan (misal: Create, Research, atau Code), masukkan instruksi prompt, dan klik tombol generate.',
    },
  ];

  const filtered = faqs.filter((f) =>
    f.q.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <button
          onClick={onBack}
          className="p-1 rounded-lg text-slate-400 hover:text-slate-700"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-base font-bold text-slate-900 leading-tight">Bantuan &amp; FAQ</h1>
        <div className="w-5" />
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Cari pertanyaan bantuan..."
          className="w-full text-xs sm:text-sm pl-10 pr-4 py-2.5 rounded-2xl bg-white border border-slate-200 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500 transition shadow-2xs"
        />
      </div>

      {/* FAQ Accordion List (Sheet 3 Screen 13) */}
      <div className="space-y-2">
        {filtered.map((item, idx) => {
          const isOpen = openIndex === idx;
          return (
            <div
              key={idx}
              className="rounded-2xl bg-white border border-slate-100 shadow-2xs overflow-hidden transition"
            >
              <button
                onClick={() => setOpenIndex(isOpen ? null : idx)}
                className="w-full p-3.5 text-left flex items-center justify-between gap-3 text-xs font-bold text-slate-900 hover:text-red-600 transition"
              >
                <span>{item.q}</span>
                {isOpen ? (
                  <ChevronUp className="w-4 h-4 text-slate-400 shrink-0" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-slate-400 shrink-0" />
                )}
              </button>
              {isOpen && (
                <div className="px-3.5 pb-3.5 pt-0 text-xs text-slate-600 leading-relaxed border-t border-slate-50">
                  {item.a}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Contact Support Card & Button Hubungi Kami (Sheet 3) */}
      <div className="p-5 rounded-3xl bg-slate-50 border border-slate-200/80 text-center space-y-3">
        <div className="w-12 h-12 rounded-2xl bg-red-100 text-red-600 flex items-center justify-center mx-auto">
          <Headphones className="w-6 h-6" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-slate-900">Masih Butuh Bantuan?</h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Kanal dukungan akan ditampilkan setelah kontak resmi MoreAI atau partner dikonfigurasi.
          </p>
        </div>

        <button
          onClick={() => showToast('Kanal kontak dukungan belum dikonfigurasi. Silakan gunakan kanal bantuan resmi yang diberikan oleh operator layanan.', 'info')}
          className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition shadow-xs flex items-center justify-center gap-2"
        >
          <Phone className="w-4 h-4" />
          <span>Kontak dukungan belum tersedia</span>
        </button>
      </div>
    </div>
  );
};
