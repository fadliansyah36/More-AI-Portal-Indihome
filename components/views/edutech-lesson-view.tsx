'use client';

import React, { useEffect, useState } from 'react';
import { ArrowLeft, Clock, CheckCircle2, BookOpen } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';
import { learningApi } from '@/lib/api/client';

interface EdutechLessonViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

export const EdutechLessonView: React.FC<EdutechLessonViewProps> = ({
  onBack,
  onNavigateTab,
}) => {
  const { showToast } = useToast();
  const [completed, setCompleted] = useState<string[]>([]);
  const [loadingProgress, setLoadingProgress] = useState(true);
  const [savingLesson, setSavingLesson] = useState<string | null>(null);
  const lessons = [
    { key: 'apa-itu-ai', title: '1. Apa itu AI?', desc: 'Konsep dasar kecerdasan buatan dan model bahasa besar.' },
    { key: 'manfaat-ai', title: '2. Manfaat AI', desc: 'Penerapan AI untuk menghemat waktu kerja & belajar sehari-hari.' },
    { key: 'etika-praktik-prompting', title: '3. Etika & Praktik Prompting', desc: 'Menulis instruksi jelas tanpa halusinasi informasi.' },
  ];

  useEffect(() => {
    let active = true;
    learningApi.progress()
      .then(({ items }) => {
        if (active) setCompleted(items.filter((item) => item.module_key === 'edu-1').map((item) => item.lesson_key));
      })
      .catch((error) => {
        if (active) showToast(error instanceof Error ? error.message : 'Progress belajar gagal dimuat.', 'error');
      })
      .finally(() => { if (active) setLoadingProgress(false); });
    return () => { active = false; };
  }, [showToast]);

  const toggleLesson = async (lessonKey: string) => {
    if (savingLesson || loadingProgress) return;
    const nextCompleted = !completed.includes(lessonKey);
    setSavingLesson(lessonKey);
    try {
      await learningApi.setProgress('edu-1', lessonKey, nextCompleted);
      setCompleted((prev) => nextCompleted ? [...prev, lessonKey] : prev.filter((key) => key !== lessonKey));
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Progress belajar gagal disimpan.', 'error');
    } finally {
      setSavingLesson(null);
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
          <h1 className="text-base font-bold text-slate-900 leading-tight">Mengenal AI untuk Pemula</h1>
          <span className="text-[10px] text-slate-500 font-medium">Materi pengantar MoreAI</span>
        </div>
        <div className="w-5" />
      </div>

      {/* Visual Header Banner (Sheet 5 Screen 11) */}
      <div className="p-5 rounded-3xl bg-gradient-to-r from-red-600 to-rose-600 text-white shadow-xs space-y-3">
        <div className="flex items-center gap-2 text-xs font-semibold text-red-100">
          <span className="flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" />
            <span>5 menit</span>
          </span>
        </div>

        <h2 className="text-lg font-black tracking-tight leading-snug">
          Mengenal AI untuk Pemula
        </h2>
        <p className="text-xs text-red-100 leading-relaxed">
          Pelajari dasar-dasar AI, manfaatnya dalam kehidupan sehari-hari, dan cara menggunakannya dengan mudah.
        </p>

        <p className="rounded-xl border border-white/25 bg-white/10 px-3 py-2 text-[11px] leading-relaxed text-red-50">
          Materi video belum tersedia. Anda tetap dapat membaca silabus dan menyimpan progress penyelesaian materi.
        </p>
      </div>

      {/* Daftar Materi (Sheet 5 Screen 11) */}
      <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-xs space-y-3">
        <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
          Silabus Materi:
        </h3>

        <div className="space-y-2">
          {loadingProgress && <p className="text-[10px] text-slate-400">Memuat progress tersimpan…</p>}
          {lessons.map((lesson) => {
            const isDone = completed.includes(lesson.key);
            return (
              <div
                key={lesson.key}
                onClick={() => void toggleLesson(lesson.key)}
                className={`cursor-pointer p-3.5 rounded-2xl border transition flex items-center justify-between ${
                  isDone
                    ? 'bg-emerald-50/70 border-emerald-200'
                    : 'bg-slate-50 border-slate-100 hover:bg-slate-100/70'
                }`}
              >
                <div>
                  <h4 className="text-xs font-bold text-slate-900">{lesson.title}</h4>
                  <p className="text-[11px] text-slate-500 mt-0.5">{lesson.desc}</p>
                </div>
                <CheckCircle2
                  className={`w-5 h-5 shrink-0 ml-2 ${
                    isDone ? 'text-emerald-600' : 'text-slate-300'
                  }`}
                />
                {savingLesson === lesson.key && <span className="text-[9px] text-slate-400 ml-1">Menyimpan…</span>}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
