'use client';

import React, { useEffect, useState } from 'react';
import { GraduationCap, BookOpen, Brain, ClipboardCheck, Compass, Lightbulb, Sparkles } from 'lucide-react';
import { useToast } from '@/components/ui/toast-context';
import { learningApi, type CustomerLearningPathDetail, type CustomerLearningPathSummary } from '@/lib/api/client';

interface EdutechViewProps {
  onStartPrompt: (prompt: string, agentKey?: 'manus' | 'planning' | 'toolcall') => void;
}

const studyModes = [
  { key: 'learning_path', label: 'Susun learning path', description: 'Kurikulum bertahap dari dasar sampai mahir', icon: Compass },
  { key: 'tutor', label: 'Belajar dengan AI Tutor', description: 'Penjelasan interaktif sesuai tingkat pemahaman', icon: Brain },
  { key: 'quiz', label: 'Latihan dan kuis', description: 'Soal, pembahasan, dan evaluasi jawaban', icon: ClipboardCheck },
  { key: 'project', label: 'Praktik dan proyek', description: 'Belajar melalui studi kasus dan proyek nyata', icon: Lightbulb },
] as const;

type StudyMode = typeof studyModes[number]['key'];

const buildStudyPrompt = (topic: string, level: string, goal: string, mode: StudyMode) => {
  const modeInstructions: Record<StudyMode, string> = {
    learning_path: 'Buat learning path yang terstruktur: tujuan kompetensi, prasyarat, modul berurutan, lesson per modul, estimasi waktu belajar, latihan, dan kriteria kelulusan. Mulai dengan peta kurikulum yang bisa langsung dipelajari.',
    tutor: 'Bertindak sebagai AI tutor personal. Lakukan diagnostic singkat, jelaskan konsep bertahap dengan contoh, analogi, pertanyaan Socratic, dan cek pemahaman sebelum lanjut. Jangan hanya memberikan jawaban akhir.',
    quiz: 'Susun latihan diagnostik dan kuis bertingkat. Berikan soal satu per satu, tunggu jawaban student, nilai dengan rubrik transparan, jelaskan alasan jawaban, dan adaptasikan tingkat kesulitan.',
    project: 'Rancang project-based learning: problem statement, learning outcomes, tahapan kerja, artefak yang harus dibuat, rubrik penilaian, contoh penerapan, dan refleksi akhir.',
  };
  return [
    'Anda adalah MoreAI EduTech, AI Learning Coach dan tutor akademik untuk student dan mahasiswa.',
    'Jalankan sesi belajar melalui OpenManus Agent Runtime. Gunakan Planning untuk menyusun pembelajaran multi-langkah; gunakan knowledge_search bila materi pengetahuan pengguna tersedia. Jangan mengarang sumber atau sitasi. Bedakan fakta, asumsi, dan contoh.',
    'Konteks student:',
    'Topik: ' + topic.trim(),
    'Tingkat: ' + level,
    'Tujuan belajar: ' + (goal.trim() || 'Memahami topik secara konseptual dan mampu menerapkannya.'),
    'Mode: ' + mode,
    'Instruksi: ' + modeInstructions[mode],
    'Gunakan Bahasa Indonesia yang jelas, ramah, akademis, inklusif, dan sesuai tingkat student. Sertakan learning outcomes yang terukur, contoh, latihan aktif, umpan balik formatif, serta langkah berikutnya. Jangan mengklaim sertifikat atau nilai resmi. Simpan hasil sebagai percakapan dan Agent Run MoreAI yang dapat dilihat pada Chat dan Tasks.',
  ].join('\n');
};

export const EdutechView: React.FC<EdutechViewProps> = ({ onStartPrompt }) => {
  const { showToast } = useToast();
  const [savedProgressCount, setSavedProgressCount] = useState(0);
  const [savedPaths, setSavedPaths] = useState<CustomerLearningPathSummary[]>([]);
  const [selectedPath, setSelectedPath] = useState<CustomerLearningPathDetail | null>(null);
  const [pathsLoading, setPathsLoading] = useState(true);
  const [progressLoading, setProgressLoading] = useState(true);
  const [topic, setTopic] = useState('');
  const [level, setLevel] = useState('Mahasiswa / Perguruan Tinggi');
  const [goal, setGoal] = useState('');
  const [mode, setMode] = useState<StudyMode>('learning_path');

  useEffect(() => {
    let active = true;
    learningApi.paths(20)
      .then(({ items }) => { if (active) setSavedPaths(items); })
      .catch((error) => { if (active) showToast(error instanceof Error ? error.message : 'Learning path gagal dimuat.', 'error'); })
      .finally(() => { if (active) setPathsLoading(false); });
    learningApi.progress()
      .then(({ total_count }) => {
        if (active) setSavedProgressCount(total_count);
      })
      .catch((error) => {
        if (active) showToast(error instanceof Error ? error.message : 'Progress belajar gagal dimuat.', 'error');
      })
      .finally(() => { if (active) setProgressLoading(false); });
    return () => { active = false; };
  }, [showToast]);

  const openLearningPath = async (pathId: string) => {
    try { setSelectedPath(await learningApi.path(pathId)); }
    catch (error) { showToast(error instanceof Error ? error.message : 'Detail learning path gagal dimuat.', 'error'); }
  };

  const startLesson = (path: CustomerLearningPathDetail['path'], moduleTitle: string, lesson: CustomerLearningPathDetail['modules'][number]['lessons'][number]) => {
    const prompt = [
      'Lanjutkan sesi pembelajaran first-party MoreAI EduTech dari artefak kurikulum tersimpan.',
      'Path ID: ' + path.id + ' | Judul: ' + path.title,
      'Lesson ID: ' + lesson.id + ' | Versi konten: ' + lesson.content_version,
      'Modul: ' + moduleTitle + ' | Lesson: ' + lesson.title,
      'Status lesson: ' + lesson.status + ' | Progress saat ini: ' + (lesson.progress?.progress_percent ?? 0) + '%',
      'Materi tersimpan (gunakan sebagai konteks, jangan mengarang sumber):',
      lesson.content_md || 'Materi belum dibuat. Gunakan lesson_generate untuk mengembangkan lesson ini.',
      'Bimbing student secara Socratic, berikan latihan aktif dan umpan balik formatif. Setelah sesi belajar benar-benar selesai, gunakan learning_progress_update dengan lesson_id yang sama dan status completed; jika masih berjalan, gunakan in_progress. Jangan mengklaim progress tersimpan tanpa hasil tool.',
    ].join('\\n');
    onStartPrompt(prompt, 'planning');
  };

  const startLearning = () => {
    if (topic.trim().length < 3) {
      showToast('Masukkan topik belajar minimal 3 karakter.', 'info');
      return;
    }
    onStartPrompt(buildStudyPrompt(topic, level, goal, mode), 'planning');
  };

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">AI Content &amp; EduTech</h1>
        <p className="text-xs text-slate-500">
          Ruang belajar internal MoreAI untuk student dan mahasiswa, didukung AI Agent OpenManus.
        </p>
      </div>

      <div className="p-4 rounded-3xl bg-gradient-to-r from-red-600 to-rose-700 text-white shadow-xs flex items-center justify-between">
        <div className="space-y-1.5 max-w-[75%]">
          <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-white/20 text-[10px] font-bold">
            <GraduationCap className="w-3.5 h-3.5 text-amber-300" />
            <span>MoreAI AI Learning</span>
          </div>
          <h3 className="text-sm sm:text-base font-bold leading-tight">Belajar bersama AI Tutor</h3>
          <p className="text-xs text-red-100">
            Susun kurikulum personal, pelajari konsep, berlatih, dan evaluasi pemahaman dalam satu workspace AI.
          </p>
        </div>
        <div className="w-14 h-14 rounded-2xl bg-white/20 border border-white/30 flex items-center justify-center shrink-0">
          <GraduationCap className="w-8 h-8 text-white" />
        </div>
      </div>

      <div className="rounded-3xl border border-slate-100 bg-white p-4 shadow-2xs space-y-3">
        <div className="flex items-center gap-2 text-slate-800">
          <Sparkles className="w-4 h-4 text-red-600" />
          <h2 className="text-xs font-bold uppercase tracking-wider">Mulai sesi belajar dengan AI Agent</h2>
        </div>
        <div className="space-y-1.5">
          <label htmlFor="edutech-topic" className="text-xs font-semibold text-slate-700">Apa yang ingin dipelajari?</label>
          <input id="edutech-topic" value={topic} onChange={(event) => setTopic(event.target.value)} maxLength={180} placeholder="Contoh: Machine Learning, Akuntansi, atau Statistik" className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-3.5 py-3 text-xs text-slate-900 outline-none transition focus:border-red-500 focus:ring-2 focus:ring-red-500/10" />
        </div>
        <div className="space-y-1.5">
          <label htmlFor="edutech-level" className="text-xs font-semibold text-slate-700">Tingkat pembelajaran</label>
          <select id="edutech-level" value={level} onChange={(event) => setLevel(event.target.value)} className="w-full rounded-2xl border border-slate-200 bg-white px-3.5 py-3 text-xs text-slate-800 outline-none focus:border-red-500">
            <option>Pelajar SMA / SMK</option>
            <option>Mahasiswa / Perguruan Tinggi</option>
            <option>Pasca Sarjana / Peneliti</option>
            <option>Pemula / Belajar Mandiri</option>
            <option>Menengah</option>
            <option>Lanjutan / Profesional</option>
          </select>
        </div>
        <div className="space-y-1.5">
          <label htmlFor="edutech-goal" className="text-xs font-semibold text-slate-700">Target belajar (opsional)</label>
          <textarea id="edutech-goal" value={goal} onChange={(event) => setGoal(event.target.value)} maxLength={1000} rows={2} placeholder="Contoh: Persiapan ujian, memahami teori, atau membangun portofolio..." className="w-full resize-y rounded-2xl border border-slate-200 bg-slate-50 px-3.5 py-3 text-xs text-slate-900 outline-none focus:border-red-500 focus:ring-2 focus:ring-red-500/10" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {studyModes.map((item) => {
            const Icon = item.icon;
            const selected = mode === item.key;
            return (
              <button key={item.key} type="button" onClick={() => setMode(item.key)} aria-pressed={selected} className={`flex items-start gap-2.5 rounded-2xl border p-3 text-left transition ${selected ? 'border-red-300 bg-red-50 ring-1 ring-red-100' : 'border-slate-200 bg-white hover:border-slate-300'}`}>
                <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-xl ${selected ? 'bg-red-100 text-red-600' : 'bg-slate-100 text-slate-500'}`}><Icon className="h-4 w-4" /></span>
                <span className="min-w-0"><span className="block text-xs font-bold text-slate-900">{item.label}</span><span className="mt-0.5 block text-[10px] leading-relaxed text-slate-500">{item.description}</span></span>
              </button>
            );
          })}
        </div>
        <button type="button" onClick={startLearning} disabled={topic.trim().length < 3} className="w-full rounded-2xl bg-red-600 px-4 py-3.5 text-xs font-bold text-white shadow-xs transition hover:bg-red-700 disabled:cursor-not-allowed disabled:bg-slate-300">
          Mulai belajar dengan OpenManus Agent
        </button>
        <p className="text-[10px] leading-relaxed text-slate-400">Sesi akan diproses sebagai Agent Run persisten. Status, langkah kerja, dan hasilnya tersedia di Chat dan Tasks. Ketersediaan mengikuti worker dan konfigurasi model MoreAI.</p>
      </div>

      <div className="rounded-3xl border border-slate-100 bg-white p-4 shadow-2xs flex items-center gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-blue-600"><BookOpen className="h-5 w-5" /></div>
        <div className="min-w-0">
          <h3 className="text-xs font-bold text-slate-900">Progress belajar tersimpan</h3>
          <p className="mt-1 text-[11px] text-slate-500">{progressLoading ? 'Memuat progress akun…' : savedProgressCount + ' catatan progress tersimpan pada akun Anda.'}</p>
        </div>
      </div>
    </div>
  );
};
