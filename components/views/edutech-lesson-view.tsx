'use client';

import React from 'react';
import { ArrowLeft, BookOpen, Clock } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';

interface EdutechLessonViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

export const EdutechLessonView: React.FC<EdutechLessonViewProps> = ({ onBack }) => {
  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <button onClick={onBack} className="p-1 rounded-lg text-slate-400 hover:text-slate-700" aria-label="Kembali">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="text-center">
          <h1 className="text-base font-bold text-slate-900 leading-tight">EduTech Lesson</h1>
          <span className="text-[10px] text-slate-500 font-medium">Menunggu katalog resmi</span>
        </div>
        <div className="w-5" />
      </div>

      <div className="p-5 rounded-3xl bg-gradient-to-r from-red-600 to-rose-600 text-white shadow-xs space-y-3">
        <div className="flex items-center gap-2 text-xs font-semibold text-red-100">
          <Clock className="w-3.5 h-3.5" />
          <span>Durasi belum tersedia</span>
        </div>
        <h2 className="text-lg font-black tracking-tight leading-snug">Materi pembelajaran belum terhubung</h2>
        <p className="text-xs text-red-100 leading-relaxed">
          Silabus, konten pelajaran, dan video hanya akan ditampilkan setelah katalog EduTech resmi tersedia melalui backend.
        </p>
      </div>

      <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-xs space-y-3">
        <div className="flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-slate-400" />
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Silabus Materi</h3>
        </div>
        <p className="text-xs leading-relaxed text-slate-500">
          Belum ada lesson resmi yang dapat dibuka atau ditandai selesai. Progress tidak akan ditulis menggunakan ID modul atau lesson contoh.
        </p>
      </div>
    </div>
  );
};
