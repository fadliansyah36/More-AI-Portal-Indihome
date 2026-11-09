'use client';

import React, { useState } from 'react';
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
import { ARTIFACT_FILES, CAMPAIGN_WORKFLOW_STEPS, INITIAL_TASKS } from '@/lib/data';
import { TaskItem } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';

interface TasksViewProps {
  onOpenWorkspaceFiles?: () => void;
}

export const TasksView: React.FC<TasksViewProps> = ({ onOpenWorkspaceFiles }) => {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<'semua' | 'aktif' | 'selesai' | 'workflow' | 'artifacts'>('semua');
  const [tasks, setTasks] = useState<TaskItem[]>(INITIAL_TASKS);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);

  const toggleTask = (id: string) => {
    setTasks((prev) =>
      prev.map((t) => (t.id === id ? { ...t, completed: !t.completed } : t))
    );
  };

  const handleAddTask = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTaskTitle.trim()) return;

    const newTask: TaskItem = {
      id: `task-${Date.now()}`,
      title: newTaskTitle.trim(),
      time: 'Hari ini • ' + new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      completed: false,
      category: 'General',
      credits: 20,
    };

    setTasks([newTask, ...tasks]);
    setNewTaskTitle('');
    setShowAddModal(false);
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
          onClick={() => setActiveTab('workflow')}
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
          onClick={() => setActiveTab('artifacts')}
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
          {filteredTasks.length === 0 ? (
            <div className="p-8 text-center bg-white rounded-3xl border border-slate-100 text-slate-500">
              <CheckCircle2 className="w-10 h-10 mx-auto text-slate-300 mb-2" />
              <p className="text-xs font-medium">Tidak ada tugas pada filter ini</p>
            </div>
          ) : (
            filteredTasks.map((task) => (
              <div
                key={task.id}
                onClick={() => toggleTask(task.id)}
                className={`cursor-pointer p-3.5 rounded-2xl border transition-all flex items-center gap-3 group ${
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

          {/* Quick Access to Campaign Workflow Card */}
          <div
            onClick={() => setActiveTab('workflow')}
            className="cursor-pointer p-4 rounded-3xl bg-gradient-to-r from-slate-900 to-slate-800 text-white shadow-sm hover:shadow-md transition flex items-center justify-between"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-white/10 flex items-center justify-center text-amber-400">
                <Layers className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-xs font-bold">Campaign Launch Project (Live)</h4>
                <p className="text-[11px] text-slate-300">4 Agent kolaboratif sedang berjalan (75%)</p>
              </div>
            </div>
            <ChevronRight className="w-5 h-5 text-slate-400" />
          </div>
        </div>
      )}

      {/* View Mode: Workflow Progress (Sheet 6 - Campaign Launch Project) */}
      {activeTab === 'workflow' && (
        <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                Multi-Agent Workflow
              </span>
              <h2 className="text-base font-bold text-slate-900">Campaign Launch Project</h2>
            </div>
            <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
              75% Selesai
            </span>
          </div>

          {/* Progress Bar */}
          <div>
            <div className="flex justify-between text-xs text-slate-500 font-medium mb-1.5">
              <span>Total Progress Eksekusi</span>
              <span className="font-bold text-slate-900">75%</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
              <div
                className="bg-gradient-to-r from-red-600 to-rose-500 h-2.5 rounded-full transition-all duration-700"
                style={{ width: '75%' }}
              />
            </div>
          </div>

          {/* Stepper list */}
          <div className="space-y-3 pt-2">
            {CAMPAIGN_WORKFLOW_STEPS.map((step, idx) => (
              <div
                key={step.id}
                className="p-3 rounded-2xl bg-slate-50 border border-slate-200/80 flex items-start gap-3"
              >
                <div className="mt-0.5 shrink-0">
                  {step.status === 'completed' && (
                    <div className="w-6 h-6 rounded-full bg-emerald-600 text-white flex items-center justify-center text-xs">
                      ✓
                    </div>
                  )}
                  {step.status === 'in_progress' && (
                    <div className="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs animate-pulse">
                      ⏳
                    </div>
                  )}
                  {step.status === 'pending' && (
                    <div className="w-6 h-6 rounded-full bg-slate-200 text-slate-600 flex items-center justify-center text-xs">
                      {idx + 1}
                    </div>
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold text-slate-900">{step.agentName}</h3>
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                        step.status === 'completed'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : step.status === 'in_progress'
                          ? 'bg-blue-50 text-blue-700 border border-blue-200'
                          : 'bg-slate-100 text-slate-500'
                      }`}
                    >
                      {step.status === 'completed'
                        ? 'Selesai'
                        : step.status === 'in_progress'
                        ? `${step.progress}% Sedang Berjalan`
                        : 'Menunggu'}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-0.5">{step.role}</p>
                  <p className="text-[11px] text-slate-700 mt-1 font-medium bg-white p-2 rounded-xl border border-slate-100">
                    {step.outputSummary}
                  </p>
                </div>
              </div>
            ))}
          </div>

          <div className="pt-2 flex gap-2">
            <button
              onClick={() => setActiveTab('artifacts')}
              className="flex-1 py-2.5 rounded-2xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition shadow-xs text-center"
            >
              Lihat Hasil & Artefak
            </button>
            <button
              onClick={() => setActiveTab('semua')}
              className="px-4 py-2.5 rounded-2xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition"
            >
              Tutup
            </button>
          </div>
        </div>
      )}

      {/* View Mode: Hasil & Artefak (Sheet 6 - Hasil Pekerjaan) */}
      {activeTab === 'artifacts' && (
        <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <span className="text-[10px] uppercase font-bold text-emerald-600 tracking-wider flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" />
                Pekerjaan Berhasil Diselesaikan!
              </span>
              <h2 className="text-base font-bold text-slate-900">Hasil & Artefak Campaign</h2>
            </div>
          </div>

          {/* Artifact Files List matching Sheet 6 */}
          <div className="space-y-2.5">
            {ARTIFACT_FILES.slice(0, 4).map((file) => (
              <div
                key={file.id}
                className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80 flex items-center justify-between hover:bg-slate-100/60 transition group"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-10 h-10 rounded-xl bg-white border border-slate-200 flex items-center justify-center shrink-0 text-red-600 shadow-2xs">
                    {file.type === 'pdf' && <FileText className="w-5 h-5 text-red-600" />}
                    {file.type === 'image' && <ImageIcon className="w-5 h-5 text-amber-600" />}
                    {file.type === 'xlsx' && <FileSpreadsheet className="w-5 h-5 text-emerald-600" />}
                  </div>
                  <div className="min-w-0">
                    <h3 className="text-xs font-bold text-slate-900 truncate group-hover:text-red-600 transition">
                      {file.name}
                    </h3>
                    <p className="text-[10px] text-slate-500 mt-0.5">
                      {file.size} · {file.date}
                    </p>
                  </div>
                </div>

                <button
                  onClick={() => showToast(`Mengunduh ${file.name}... Berkas siap digunakan.`, 'success')}
                  className="p-2 rounded-xl bg-white text-slate-600 hover:text-red-600 hover:bg-red-50 border border-slate-200 transition shadow-2xs"
                  title="Unduh File"
                >
                  <Download className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>

          <div className="pt-2">
            <button
              onClick={() => {
                if (onOpenWorkspaceFiles) onOpenWorkspaceFiles();
              }}
              className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition shadow-xs flex items-center justify-center gap-2"
            >
              <span>Buka di Workspace File</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Modal Tambah Tugas */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-fadeIn">
          <div className="w-full max-w-sm rounded-3xl bg-white p-5 shadow-2xl border border-slate-100">
            <h3 className="text-base font-bold text-slate-900 mb-1">Tambah Tugas AI Baru</h3>
            <p className="text-xs text-slate-500 mb-3">Tuliskan pekerjaan yang ingin dijadwalkan</p>

            <form onSubmit={handleAddTask} className="space-y-3">
              <input
                type="text"
                value={newTaskTitle}
                onChange={(e) => setNewTaskTitle(e.target.value)}
                placeholder="Contoh: Analisis tren TikTok kopi..."
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
                  Simpan Tugas
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
