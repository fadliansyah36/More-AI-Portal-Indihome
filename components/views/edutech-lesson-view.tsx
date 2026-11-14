'use client';

import React, { useEffect, useState } from 'react';
import { ArrowLeft, BookOpen, Clock, AlertCircle, Loader2, CheckCircle2, ClipboardCheck, Sparkles } from 'lucide-react';
import { learningApi, type CustomerLearningPathDetail } from '@/lib/api/client';

interface EdutechLessonViewProps {
  onBack: () => void;
  pathId: string;
  lessonId: string;
  onStartPrompt: (prompt: string, agentKey?: 'manus' | 'planning' | 'toolcall') => void;
}

type LessonRecord = CustomerLearningPathDetail['modules'][number]['lessons'][number];

export const EdutechLessonView: React.FC<EdutechLessonViewProps> = ({ onBack, pathId, lessonId, onStartPrompt }) => {
  const [detail, setDetail] = useState<CustomerLearningPathDetail | null>(null);
  const [lesson, setLesson] = useState<LessonRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    learningApi.path(pathId)
      .then((result) => {
        if (!active) return;
        const canonicalLesson = result.modules.flatMap((module) => module.lessons).find((item) => item.id === lessonId) || null;
        setDetail(result);
        setLesson(canonicalLesson);
        if (!canonicalLesson) setError('Lesson tidak ditemukan pada learning path milik akun ini.');
      })
      .catch((cause) => {
        if (active) setError(cause instanceof Error ? cause.message : 'Materi lesson tidak dapat dimuat dari MoreAI API.');
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [pathId, lessonId]);

  const moduleTitle = detail?.modules.find((module) => module.lessons.some((item) => item.id === lessonId))?.title;

  const startQuizWithAgent = (quiz: LessonRecord['quizzes'][number]) => {
    if (!lesson || !detail) return;
    const safeQuestions = quiz.questions.map((question) => {
      if (!question || typeof question !== 'object' || Array.isArray(question)) return question;
      return Object.fromEntries(Object.entries(question as Record<string, unknown>)
        .filter(([key]) => !['answer', 'answer_key', 'correct_answer', 'explanation', 'rationale', 'grading_notes', 'rubric'].includes(key.toLowerCase())));
    });
    const prompt = [
      'Jalankan sesi assessment EduTech MoreAI melalui OpenManus Planning Agent.',
      'Path ID: ' + detail.path.id + ' | Path: ' + detail.path.title,
      'Lesson ID: ' + lesson.id + ' | Lesson: ' + lesson.title,
      'Quiz ID canonical: ' + quiz.id + ' | Quiz: ' + quiz.title,
      'Nilai lulus: ' + quiz.pass_score,
      'Pertanyaan learner-safe (tanpa answer key):',
      JSON.stringify(safeQuestions),
      'Alur wajib: tampilkan satu pertanyaan pada satu waktu, tunggu jawaban aktual student, catat jawaban per question_id, lalu lanjutkan sampai semua pertanyaan terjawab. Jangan memberi atau menebak answer key. Jangan membuat skor, feedback, atau rubric sendiri. Setelah jawaban lengkap, panggil tool answer_assess dengan quiz_id dan array answers berisi question_id serta jawaban aktual student. Worker akan mengambil answer key canonical dan melakukan deterministic grading. Laporkan score, feedback, dan status lulus hanya dari hasil tool. Jangan mengklaim assessment tersimpan jika tool gagal. Hasil Agent Run dan assessment harus dapat ditelusuri dari Tasks.',
    ].join('\n');
    onStartPrompt(prompt, 'planning');
  };

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <button onClick={onBack} className="p-1 rounded-lg text-slate-400 hover:text-slate-700" aria-label="Kembali">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="text-center min-w-0 px-2">
          <h1 className="text-base font-bold text-slate-900 leading-tight">EduTech Lesson</h1>
          <span className="text-[10px] text-slate-500 font-medium">Materi kanonis MoreAI</span>
        </div>
        <div className="w-5" />
      </div>

      {loading ? (
        <div className="rounded-3xl border border-slate-100 bg-white p-8 flex items-center justify-center gap-2 text-xs text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin" /> Memuat materi tersimpan…
        </div>
      ) : error ? (
        <div role="alert" className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-700 flex items-start gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" /> {error}
        </div>
      ) : lesson && detail ? (
        <>
          <div className="rounded-3xl border border-slate-100 bg-white p-4 shadow-2xs space-y-2">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-red-600">{detail.path.title}</p>
            <h2 className="text-lg font-bold leading-snug text-slate-900">{lesson.title}</h2>
            <p className="text-[11px] text-slate-500">{moduleTitle} · Versi {lesson.content_version} · {lesson.progress?.progress_percent ?? 0}% progress</p>
            <div className="flex flex-wrap gap-3 text-[10px] text-slate-500">
              <span className="inline-flex items-center gap-1"><Clock className="h-3.5 w-3.5" /> Estimasi sesuai modul</span>
              <span className="inline-flex items-center gap-1"><CheckCircle2 className="h-3.5 w-3.5" /> {lesson.progress?.status === 'completed' ? 'Selesai' : lesson.progress?.status === 'in_progress' ? 'Sedang dipelajari' : 'Belum dimulai'}</span>
            </div>
          </div>

          {lesson.objectives.length > 0 && (
            <section className="rounded-3xl border border-slate-100 bg-white p-4 shadow-2xs space-y-2">
              <h3 className="text-xs font-bold text-slate-900">Tujuan pembelajaran</h3>
              <ul className="list-disc space-y-1 pl-5 text-xs text-slate-600">
                {lesson.objectives.map((objective, index) => <li key={index}>{objective}</li>)}
              </ul>
            </section>
          )}

          <section className="rounded-3xl border border-slate-100 bg-white p-4 shadow-2xs space-y-3">
            <div className="flex items-center gap-2"><BookOpen className="h-4 w-4 text-red-600" /><h3 className="text-xs font-bold text-slate-900">Materi pembelajaran tersimpan</h3></div>
            {lesson.content_md.trim() ? (
              <article className="whitespace-pre-wrap break-words text-xs leading-7 text-slate-700">{lesson.content_md}</article>
            ) : (
              <p className="rounded-xl bg-slate-50 p-3 text-xs text-slate-500">Materi belum tersedia pada versi tersimpan. Lesson ini belum menampilkan konten contoh atau placeholder.</p>
            )}
          </section>

          {lesson.quizzes.length > 0 && (
            <section className="rounded-3xl border border-slate-100 bg-white p-4 shadow-2xs space-y-2">
              <div className="flex items-center gap-2"><ClipboardCheck className="h-4 w-4 text-blue-600" /><h3 className="text-xs font-bold text-slate-900">Kuis tersimpan</h3></div>
              {lesson.quizzes.map((quiz) => (
                <div key={quiz.id} className="rounded-xl border border-slate-200 p-3">
                  <p className="text-xs font-semibold text-slate-800">{quiz.title}</p>
                  <p className="mt-1 text-[10px] text-slate-500">{quiz.questions.length} soal · Nilai lulus {quiz.pass_score}</p>
                  {quiz.attempts[0] && <p className="mt-1 text-[10px] font-semibold text-slate-700">Percobaan terakhir: {quiz.attempts[0].score}/100 {quiz.attempts[0].passed ? '· Lulus' : '· Belum lulus'}</p>}
                  <button type="button" onClick={() => startQuizWithAgent(quiz)} className="mt-2 inline-flex items-center gap-1.5 rounded-xl bg-red-600 px-3 py-2 text-[10px] font-semibold text-white transition hover:bg-red-700"><Sparkles className="h-3 w-3" /> Kerjakan dengan AI Tutor</button>
                </div>
              ))}
            </section>
          )}
        </>
      ) : null}
    </div>
  );
};
