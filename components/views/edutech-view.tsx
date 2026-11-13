'use client';

import React, { useEffect, useState } from 'react';
import { GraduationCap, BookOpen } from 'lucide-react';
import { useToast } from '@/components/ui/toast-context';
import { learningApi } from '@/lib/api/client';

export const EdutechView: React.FC = () => {
  const { showToast } = useToast();
  const [activeCategory, setActiveCategory] = useState<'semua' | 'ai' | 'produktivitas' | 'karier'>('semua');
  const [savedProgressCount, setSavedProgressCount] = useState(0);
  const [progressLoading, setProgressLoading] = useState(true);

  useEffect(() => {
    let active = true;
    learningApi.progress()
      .then(({ items }) => {
        if (active) setSavedProgressCount(items.length);
      })
      .catch((error) => {
        if (active) showToast(error instanceof Error ? error.message : 'Progress belajar gagal dimuat.', 'error');
      })
      .finally(() => { if (active) setProgressLoading(false); });
    return () => { active = false; };
  }, [showToast]);

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">AI Content & EduTech</h1>
        <p className="text-xs text-slate-500">
          Katalog pembelajaran dan materi resmi akan ditampilkan setelah integrasi EduTech tersedia.
        </p>
      </div>

      <div className="p-4 rounded-3xl bg-gradient-to-r from-red-600 to-rose-700 text-white shadow-xs flex items-center justify-between">
        <div className="space-y-1.5 max-w-[70%]">
          <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-white/20 text-[10px] font-bold">
            <GraduationCap className="w-3.5 h-3.5 text-amber-300" />
            <span>EduTech Integration</span>
          </div>
          <h3 className="text-sm sm:text-base font-bold leading-tight">Katalog EduTech menunggu koneksi resmi</h3>
          <p className="text-xs text-red-100">
            Materi, durasi, level, dan video hanya akan berasal dari katalog backend yang terverifikasi.
          </p>
        </div>
        <div className="w-14 h-14 rounded-2xl bg-white/20 border border-white/30 flex items-center justify-center shrink-0">
          <GraduationCap className="w-8 h-8 text-white" />
        </div>
      </div>

      <div className="flex items-center gap-1 p-1 bg-white rounded-2xl border border-slate-200 shadow-2xs">
        {(['semua', 'ai', 'produktivitas', 'karier'] as const).map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-xl capitalize transition ${
              activeCategory === cat ? 'bg-red-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      <div className="rounded-3xl border border-slate-100 bg-white p-5 shadow-2xs space-y-3">
        <div className="flex items-center gap-2 text-slate-700">
          <BookOpen className="w-5 h-5 text-slate-400" />
          <h3 className="text-xs font-bold">Katalog belum tersedia</h3>
        </div>
        <p className="text-xs leading-relaxed text-slate-500">
          Tidak ada kursus contoh yang ditampilkan sebagai materi aktif. Katalog, enrollment, sertifikat, dan protected video delivery belum terhubung ke provider EduTech resmi.
        </p>
        <p className="text-[11px] text-slate-400">
          {progressLoading ? 'Memuat progress tersimpan…' : `${savedProgressCount} catatan progress tersimpan pada akun Anda.`}
        </p>
      </div>
    </div>
  );
};
