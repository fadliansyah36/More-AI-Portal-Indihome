'use client';

import React, { useEffect, useState } from 'react';
import {
  GraduationCap,
  PlayCircle,
  Star,
  Clock,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  ArrowLeft,
  Award,
} from 'lucide-react';
import { EDUTECH_MODULES } from '@/lib/data';
import { EduTechModule } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';
import { learningApi } from '@/lib/api/client';

export const EdutechView: React.FC = () => {
  const { showToast } = useToast();
  const [activeCategory, setActiveCategory] = useState<'semua' | 'ai' | 'produktivitas' | 'karier'>('semua');
  const [selectedModule, setSelectedModule] = useState<EduTechModule | null>(null);
  const [completedLessons, setCompletedLessons] = useState<string[]>([]);
  const [progressLoading, setProgressLoading] = useState(true);
  const [savingLesson, setSavingLesson] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    learningApi.progress()
      .then(({ items }) => {
        if (active) setCompletedLessons(items.map((item) => item.module_key + ':' + item.lesson_key));
      })
      .catch((error) => {
        if (active) showToast(error instanceof Error ? error.message : 'Progress belajar gagal dimuat.', 'error');
      })
      .finally(() => { if (active) setProgressLoading(false); });
    return () => { active = false; };
  }, [showToast]);

  const toggleLesson = async (moduleKey: string, lesson: string) => {
    const key = moduleKey + ':' + lesson;
    if (savingLesson) return;
    const completed = !completedLessons.includes(key);
    setSavingLesson(key);
    try {
      await learningApi.setProgress(moduleKey, lesson, completed);
      setCompletedLessons((prev) => completed ? [...prev, key] : prev.filter((item) => item !== key));
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Progress belajar gagal disimpan.', 'error');
    } finally {
      setSavingLesson(null);
    }
  };

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Title */}
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">AI Content & EduTech</h1>
        <p className="text-xs text-slate-500">
          Modul edukasi terstruktur, tips prompting, dan penguasaan AI untuk produktivitas
        </p>
      </div>

      {/* Hero Banner: Belajar Lebih Mudah dengan AI */}
      <div className="p-4 rounded-3xl bg-gradient-to-r from-red-600 to-rose-700 text-white shadow-xs flex items-center justify-between">
        <div className="space-y-1.5 max-w-[70%]">
          <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-white/20 text-[10px] font-bold">
            <GraduationCap className="w-3.5 h-3.5 text-amber-300" />
            <span>EduTech Global Partner</span>
          </div>
          <h3 className="text-sm sm:text-base font-bold leading-tight">
            Belajar Lebih Mudah dengan AI
          </h3>
          <p className="text-xs text-red-100">
            Kuasai skill prompt engineering dan AI workflow untuk karir & usaha Anda.
          </p>
        </div>
        <div className="w-14 h-14 rounded-2xl bg-white/20 border border-white/30 flex items-center justify-center shrink-0">
          <GraduationCap className="w-8 h-8 text-white" />
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1 p-1 bg-white rounded-2xl border border-slate-200 shadow-2xs">
        {(['semua', 'ai', 'produktivitas', 'karier'] as const).map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-xl capitalize transition ${
              activeCategory === cat
                ? 'bg-red-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Modules List (Exact from Sheet 3, 5) */}
      <div className="space-y-2.5">
        {EDUTECH_MODULES.map((mod) => (
          <div
            key={mod.id}
            onClick={() => setSelectedModule(mod)}
            className="cursor-pointer p-4 rounded-3xl bg-white border border-slate-100 hover:border-red-200 shadow-2xs hover:shadow-xs transition flex items-start gap-3.5 group"
          >
            <div className="w-11 h-11 rounded-2xl bg-red-50 text-red-600 flex items-center justify-center shrink-0 border border-red-100 group-hover:scale-105 transition-transform">
              <PlayCircle className="w-6 h-6" />
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <h3 className="text-xs sm:text-sm font-bold text-slate-900 group-hover:text-red-600 transition">
                  {mod.title}
                </h3>
                <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-red-500 group-hover:translate-x-0.5 transition" />
              </div>

              <div className="flex items-center gap-2 text-[11px] text-slate-500 mt-1">
                <span>{mod.duration}</span>
                <span>·</span>
                <span>Level {mod.level}</span>
                <span>·</span>
                <span className="flex items-center gap-0.5 text-amber-500 font-semibold">
                  <Star className="w-3 h-3 fill-current" />
                  <span>{mod.rating} ({mod.reviewsCount})</span>
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Module Detail & Interactive Lessons Modal */}
      {selectedModule && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-fadeIn">
          <div className="w-full max-w-sm rounded-3xl bg-white p-5 shadow-2xl border border-slate-100 text-slate-800 space-y-3.5">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <span className="text-[10px] font-bold text-red-600 uppercase tracking-wider">
                Silabus Modul
              </span>
              <button
                onClick={() => setSelectedModule(null)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <h3 className="text-base font-bold text-slate-900 leading-tight">
              {selectedModule.title}
            </h3>

            <div className="flex items-center gap-3 text-xs text-slate-500 font-medium">
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                <span>{selectedModule.duration}</span>
              </span>
              <span className="flex items-center gap-1 text-amber-500">
                <Star className="w-3.5 h-3.5 fill-current" />
                <span>{selectedModule.rating} ({selectedModule.reviewsCount})</span>
              </span>
              <span className="px-2 py-0.5 rounded-full bg-slate-100 text-[10px] text-slate-700 font-semibold">
                {selectedModule.level}
              </span>
            </div>

            <div className="space-y-2 pt-1">
              <span className="text-xs font-bold text-slate-900 block">Daftar Materi:</span>
              <div className="space-y-1.5">
                {selectedModule.lessons.map((lesson, idx) => {
                  const progressKey = selectedModule.id + ':' + lesson;
                  const isDone = completedLessons.includes(progressKey);
                  return (
                    <div
                      key={idx}
                      onClick={() => void toggleLesson(selectedModule.id, lesson)}
                      className={`cursor-pointer p-2.5 rounded-xl border text-xs flex items-center justify-between transition ${
                        isDone
                          ? 'bg-emerald-50/80 border-emerald-200 text-emerald-800 font-medium'
                          : 'bg-slate-50 border-slate-100 text-slate-700 hover:bg-slate-100'
                      }`}
                    >
                      <span>{lesson}{progressLoading ? ' · memuat' : savingLesson === progressKey ? ' · menyimpan' : ''}</span>
                      <CheckCircle2
                        className={`w-4 h-4 shrink-0 ml-2 ${
                          isDone ? 'text-emerald-600' : 'text-slate-300'
                        }`}
                      />
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="pt-2">
              <button
                onClick={() => {
                  showToast(`Selamat! Anda telah memulai modul: ${selectedModule.title}`, 'success');
                  setSelectedModule(null);
                }}
                className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition shadow-xs"
              >
                Mulai Belajar Sekarang
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
