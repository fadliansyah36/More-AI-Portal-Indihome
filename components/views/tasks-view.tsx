'use client';

import React, { useEffect, useState } from 'react';
import {
  CheckCircle2,
  Circle,
  Plus,
  ArrowRight,
  Clock,
  Sparkles,
  Bot,
  FileText,
  FileSpreadsheet,
  Image as ImageIcon,
  Download,
  Share2,
  ChevronRight,
  Layers,
  ArrowLeft,
} from 'lucide-react';
import { customerApi, type CustomerAgentRun } from '@/lib/api/client';
import { TaskItem } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';

interface TasksViewProps {
  onOpenWorkspaceFiles?: () => void;
  onOpenWorkflow?: () => void;
  onStartPrompt?: (prompt: string, agentKey?: 'manus' | 'planning') => void;
}

export const TasksView: React.FC<TasksViewProps> = ({ onOpenWorkspaceFiles, onOpenWorkflow, onStartPrompt }) => {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<'semua' | 'aktif' | 'selesai' | 'workflow' | 'artifacts'>('semua');
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [runs, setRuns] = useState<CustomerAgentRun[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    customerApi.agentRunsPage(50).then((page) => {
      if (!active) return;
      setRuns(page.items);
      setNextCursor(page.nextCursor);
      setTasks(page.items.map((run) => ({
        id: run.id,
        title: typeof run.input?.prompt === 'string' && run.input.prompt.trim()
          ? run.input.prompt.trim().slice(0, 100)
          : `Agent Run ${run.id.slice(0, 8)}`,
        time: run.created_at ? new Date(run.created_at).toLocaleString() : run.status,
        completed: run.status === 'succeeded',
        category: run.status,
      })));
    }).catch((error) => {
      if (active) setLoadError(error instanceof Error ? error.message : 'Riwayat run tidak dapat dimuat.');
    });
    return () => { active = false; };
  }, []);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);

  const handleAddTask = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTaskTitle.trim()) return;

    setShowAddModal(false);
    const prompt = newTaskTitle.trim();
    setNewTaskTitle('');
    if (onStartPrompt) {
      // Reuse the existing authenticated Chat -> FastAPI -> durable Agent Run
      // path; never create a local-only task record or placeholder task.
      onStartPrompt(prompt, 'manus');
    } else {
      showToast('Chat AI belum tersedia untuk membuat Agent Run.', 'error');
    }
  };

  const latestRun = runs[0];

  const handleLoadMore = async () => {
    if (!nextCursor || loadingMore) return;
    setLoadingMore(true);
    try {
      const page = await customerApi.agentRunsPage(50, nextCursor);
      setRuns((previous) => {
        const known = new Set(previous.map((run) => run.id));
        return [...previous, ...page.items.filter((run) => !known.has(run.id))];
      });
      setTasks((previous) => {
        const known = new Set(previous.map((task) => task.id));
        const additions = page.items.filter((run) => !known.has(run.id)).map((run) => ({
          id: run.id,
          title: typeof run.input?.prompt === 'string' && run.input.prompt.trim()
            ? run.input.prompt.trim().slice(0, 100)
            : `Agent Run ${run.id.slice(0, 8)}`,
          time: run.created_at ? new Date(run.created_at).toLocaleString() : run.status,
          completed: run.status === 'succeeded',
          category: run.status,
        }));
        return [...previous, ...additions];
      });
      setNextCursor(page.nextCursor);
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Riwayat run berikutnya tidak dapat dimuat.', 'error');
    } finally {
      setLoadingMore(false);
    }
  };

  const filteredTasks = tasks.filter((t) => {
    if (activeTab === 'aktif') return !t.completed;
    if (activeTab === 'selesai') return t.completed;
    return true;
  });

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Header & Section Title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Tasks & Workflow</h1>
          <p className="text-xs text-slate-500">Pantau progres pekerjaan AI dan artefak hasil kerja</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-red-600 hover:bg-red-700 text-white text-xs font-semibold shadow-xs active:scale-95 transition"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Tambah Tugas</span>
        </button>
      </div>

      {/* Mode Sub-tabs */}
      <div className="flex items-center gap-1 p-1 bg-white rounded-2xl border border-slate-200 shadow-2xs overflow-x-auto no-scrollbar">
        <button
          onClick={() => setActiveTab('semua')}
          className={`flex-1 min-w-[70px] py-1.5 text-xs font-semibold rounded-xl transition ${
            activeTab === 'semua'
              ? 'bg-red-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
          }`}
        >
          Semua
        </button>
        <button
          onClick={() => setActiveTab('aktif')}
          className={`flex-1 min-w-[70px] py-1.5 text-xs font-semibold rounded-xl transition ${
            activeTab === 'aktif'
              ? 'bg-red-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
          }`}
        >
          Aktif
        </button>
        <button
          onClick={() => setActiveTab('selesai')}
          className={`flex-1 min-w-[70px] py-1.5 text-xs font-semibold rounded-xl transition ${
            activeTab === 'selesai'
              ? 'bg-red-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
          }`}
        >
          Selesai
        </button>
        <button
          onClick={() => onOpenWorkflow?.()}
          className={`flex-1 min-w-[95px] py-1.5 text-xs font-semibold rounded-xl transition flex items-center justify-center gap-1 ${
            activeTab === 'workflow'
              ? 'bg-red-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
          }`}
        >
          <Layers className="w-3 h-3" />
          <span>Workflow AI</span>
        </button>
        <button
          onClick={() => onOpenWorkspaceFiles?.()}
          className={`flex-1 min-w-[95px] py-1.5 text-xs font-semibold rounded-xl transition flex items-center justify-center gap-1 ${
            activeTab === 'artifacts'
              ? 'bg-red-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
          }`}
        >
          <Sparkles className="w-3 h-3" />
          <span>Hasil Kerja</span>
        </button>
      </div>

      {/* View Mode: Task Checklist (Semua, Aktif, Selesai) */}
      {(activeTab === 'semua' || activeTab === 'aktif' || activeTab === 'selesai') && (
        <div className="space-y-2.5">
          {loadError && <div className="p-3 rounded-xl border border-rose-200 bg-rose-50 text-rose-700 text-xs">{loadError}</div>}
          {filteredTasks.length === 0 ? (
            <div className="p-8 text-center bg-white rounded-3xl border border-slate-100 text-slate-500">
              <CheckCircle2 className="w-10 h-10 mx-auto text-slate-300 mb-2" />
              <p className="text-xs font-medium">Belum ada Agent Run tersimpan</p>
              <p className="text-[11px] mt-1">Mulai percakapan melalui Chat AI untuk membuat workflow backend.</p>
            </div>
          ) : (
            filteredTasks.map((task) => (
              <div
                key={task.id}
                className={`p-3.5 rounded-2xl border transition-all flex items-center gap-3 group ${
                  task.completed
                    ? 'bg-slate-50/70 border-slate-200/60 opacity-80'
                    : 'bg-white border-slate-200/90 hover:border-red-200 shadow-xs'
                }`}
              >
                <button
                  type="button"
                  className={`w-6 h-6 rounded-full flex items-center justify-center transition shrink-0 ${
                    task.completed
                      ? 'bg-red-600 text-white'
                      : 'text-slate-400 group-hover:text-red-500'
                  }`}
                >
                  {task.completed ? (
                    <CheckCircle2 className="w-5 h-5" />
                  ) : (
                    <Circle className="w-5 h-5" />
                  )}
                </button>

                <div className="flex-1 min-w-0">
                  <h3
                    className={`text-xs sm:text-sm font-semibold truncate ${
                      task.completed ? 'line-through text-slate-400' : 'text-slate-900'
                    }`}
                  >
                    {task.title}
                  </h3>
                  <div className="flex items-center gap-2 text-[11px] text-slate-500 mt-0.5">
                    <span>{task.time}</span>
                    <span className="text-slate-300">·</span>
                    <span className="text-slate-600 font-medium">{task.category}</span>
                  </div>
                </div>

                {task.credits && (
                  <span className="text-[10px] font-bold text-red-600 bg-red-50 px-2 py-0.5 rounded-full border border-red-200 shrink-0">
                    +{task.credits}K
                  </span>
                )}
              </div>
            ))
          )}
          {nextCursor && (
            <button
              type="button"
              onClick={() => void handleLoadMore()}
              disabled={loadingMore}
              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-semibold text-slate-700 transition hover:border-red-200 hover:text-red-600 disabled:opacity-50"
            >
              {loadingMore ? 'Memuat riwayat…' : 'Muat Tugas Sebelumnya'}
            </button>
          )}

          {/* Quick Access to Campaign Workflow Card */}
          <div
            onClick={() => onOpenWorkflow?.()}
            className="cursor-pointer p-4 rounded-3xl bg-gradient-to-r from-slate-900 to-slate-800 text-white shadow-sm hover:shadow-md transition flex items-center justify-between"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-white/10 flex items-center justify-center text-amber-400">
                <Layers className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-xs font-bold">{latestRun ? `Workflow Terbaru · ${latestRun.id.slice(0, 8)}` : 'Workflow OpenManus'}</h4>
                <p className="text-[11px] text-slate-300">{latestRun ? `Status backend: ${latestRun.status}` : 'Belum ada Agent Run tersimpan'}</p>
              </div>
            </div>
            <ChevronRight className="w-5 h-5 text-slate-400" />
          </div>
        </div>
      )}

      {/* Workflow route is backed by persisted OpenManus agent runs. */}
      {activeTab === 'workflow' && (
        <div className="p-5 rounded-3xl bg-white border border-slate-100 shadow-xs space-y-3">
          <h2 className="text-sm font-bold text-slate-900">Workflow AI</h2>
          <p className="text-xs text-slate-500">{runs.length} Agent Run tersimpan di backend.</p>
          <button onClick={() => onOpenWorkflow?.()} className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition">
            Buka Detail Workflow
          </button>
        </div>
      )}

      {/* Artifact access is delegated to the authenticated Files API view. */}
      {activeTab === 'artifacts' && (
        <div className="p-5 rounded-3xl bg-white border border-slate-100 shadow-xs space-y-3">
          <p className="text-xs text-slate-600">Artefak hanya ditampilkan dari penyimpanan workspace yang terhubung ke backend.</p>
          <button onClick={() => onOpenWorkspaceFiles?.()} className="w-full py-3 rounded-2xl bg-red-600 text-white text-xs font-bold">Buka Workspace File</button>
        </div>
      )}

      {/* Modal Tambah Tugas */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-fadeIn">
          <div className="w-full max-w-sm rounded-3xl bg-white p-5 shadow-2xl border border-slate-100">
            <h3 className="text-base font-bold text-slate-900 mb-1">Tambah Tugas AI Baru</h3>
            <p className="text-xs text-slate-500 mb-3">Tuliskan instruksi yang akan dikirim ke Agent Chat untuk membuat Agent Run.</p>

            <form onSubmit={handleAddTask} className="space-y-3">
              <input
                type="text"
                value={newTaskTitle}
                onChange={(e) => setNewTaskTitle(e.target.value)}
                placeholder="Contoh: Analisis tren pasar kopi di Indonesia..."
                autoFocus
                className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500 text-slate-900"
              />

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 py-2 rounded-xl bg-slate-100 text-slate-700 text-xs font-semibold hover:bg-slate-200 transition"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  disabled={!newTaskTitle.trim()}
                  className="flex-1 py-2 rounded-xl bg-red-600 disabled:opacity-40 text-white text-xs font-semibold hover:bg-red-700 transition"
                >
                  Lanjutkan di Chat AI
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
