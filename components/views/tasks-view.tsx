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
  Loader2,
  Share2,
  ChevronRight,
  Layers,
  ArrowLeft,
} from 'lucide-react';
import { artifactApi, customerApi, moreAiApiStream, type CustomerAgentRun, type CustomerAgentRunActivity, type CustomerWorkflowStep, type CustomerAgentRunProgress, type CustomerArtifact } from '@/lib/api/client';
import { agentRunStatusLabel, isTerminalAgentRunStatus } from '@/lib/api/agent-run-status';
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
  const [artifacts, setArtifacts] = useState<CustomerArtifact[]>([]);
  const [downloadingArtifactId, setDownloadingArtifactId] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [nextArtifactCursor, setNextArtifactCursor] = useState<string | null>(null);
  const [loadingMoreArtifacts, setLoadingMoreArtifacts] = useState(false);
  const [artifactPaginationError, setArtifactPaginationError] = useState<string | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    Promise.allSettled([customerApi.agentRunsPage(50), artifactApi.listPage(50)]).then(([runResult, artifactResult]) => {
      if (!active) return;
      if (runResult.status === 'fulfilled') {
        const page = runResult.value;
        setRuns(page.items);
        setNextCursor(page.nextCursor);
        setTasks(page.items.map((run) => ({
          id: run.id,
          title: typeof run.input?.prompt === 'string' && run.input.prompt.trim()
            ? run.input.prompt.trim().slice(0, 100)
            : `Agent Run ${run.id.slice(0, 8)}`,
          time: run.created_at ? new Date(run.created_at).toLocaleString() : run.status,
          completed: isTerminalAgentRunStatus(run.status),
          category: agentRunStatusLabel(run.status),
        })));
      } else {
        setLoadError(runResult.reason instanceof Error ? runResult.reason.message : 'Riwayat run tidak dapat dimuat.');
      }
      if (artifactResult.status === 'fulfilled') {
        setArtifacts(artifactResult.value.items);
        setNextArtifactCursor(artifactResult.value.nextCursor);
      }
      else setLoadError((previous) => previous || (artifactResult.reason instanceof Error ? artifactResult.reason.message : 'Artefak tidak dapat dimuat.'));
    });
    return () => { active = false; };
  }, []);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedRun, setSelectedRun] = useState<CustomerAgentRun | null>(null);
  const [runSteps, setRunSteps] = useState<CustomerWorkflowStep[]>([]);
  const [runActivity, setRunActivity] = useState<CustomerAgentRunActivity[]>([]);
  const [runProgress, setRunProgress] = useState<CustomerAgentRunProgress | null>(null);
  const [runDetailLoading, setRunDetailLoading] = useState(false);
  const [runDetailError, setRunDetailError] = useState<string | null>(null);
  const [cancellingRun, setCancellingRun] = useState(false);
  const [retryingRun, setRetryingRun] = useState(false);

  const openRunDetails = async (run: CustomerAgentRun) => {
    setSelectedRun(run);
    setRunSteps([]);
    setRunActivity([]);
    setRunProgress(null);
    setRunDetailError(null);
    setRunDetailLoading(true);
    const [stepsResult, activityResult, runResult, progressResult] = await Promise.allSettled([
      customerApi.getRunSteps(run.id),
      customerApi.getRunActivity(run.id, 0, 200),
      customerApi.getRun(run.id),
      customerApi.getRunProgress(run.id),
    ]);
    if (stepsResult.status === 'fulfilled') setRunSteps(stepsResult.value);
    if (activityResult.status === 'fulfilled') setRunActivity(activityResult.value.items);
    if (runResult.status === 'fulfilled') {
      setSelectedRun(runResult.value);
      setRuns((current) => current.map((item) => item.id === run.id ? runResult.value : item));
    }
    if (progressResult.status === 'fulfilled') setRunProgress(progressResult.value);
    const errors = [stepsResult, activityResult, runResult, progressResult]
      .filter((result) => result.status === 'rejected')
      .map((result) => result.reason instanceof Error ? result.reason.message : 'Data lifecycle Agent Run tidak dapat dimuat.');
    if (errors.length) setRunDetailError(errors.join(' · '));
    setRunDetailLoading(false);
  };

  // Keep an opened Task detail synchronized with the durable worker event stream.
  // The run snapshot and event cursor remain server-authoritative; reconnect/replay
  // is handled by the shared authenticated SSE client.
  useEffect(() => {
    if (!selectedRun || isTerminalAgentRunStatus(selectedRun.status)) return;
    const controller = new AbortController();
    let active = true;
    const runId = selectedRun.id;
    const refreshSnapshot = async () => {
      const [runResult, stepsResult, activityResult, progressResult] = await Promise.allSettled([
        customerApi.getRun(runId),
        customerApi.getRunSteps(runId),
        customerApi.getRunActivity(runId, 0, 200),
        customerApi.getRunProgress(runId),
      ]);
      if (!active) return;
      if (runResult.status === 'fulfilled') {
        const fresh = runResult.value;
        setSelectedRun(fresh);
        setRuns(current => current.map(item => item.id === runId ? fresh : item));
        setTasks(current => current.map(task => task.id === runId
          ? { ...task, completed: isTerminalAgentRunStatus(fresh.status), category: agentRunStatusLabel(fresh.status) }
          : task));
      }
      if (stepsResult.status === 'fulfilled') setRunSteps(stepsResult.value);
      if (activityResult.status === 'fulfilled') setRunActivity(activityResult.value.items);
      if (progressResult.status === 'fulfilled') setRunProgress(progressResult.value);
    };
    void moreAiApiStream(customerApi.streamRun(runId), ({ event }) => {
      if (!active) return;
      if (['run.started', 'run.progress', 'worker.checkpoint', 'planning.step.started',
        'planning.step.completed', 'planning.step.failed', 'tool.started', 'tool.completed',
        'tool.failed', 'tool.approval_requested', 'run.resume_queued', 'run.completed',
        'run.failed', 'run.cancelled', 'run.timed_out', 'run.expired'].includes(event)) {
        void refreshSnapshot();
      }
    }, { signal: controller.signal, maxReconnects: 20 }).catch(error => {
      if (active && !(error instanceof DOMException && error.name === 'AbortError')) {
        setRunDetailError(error instanceof Error ? error.message : 'Stream Agent Run terputus; muat ulang detail untuk mencoba lagi.');
      }
    });
    return () => {
      active = false;
      controller.abort();
    };
  }, [selectedRun?.id, selectedRun?.status]);

  const cancelSelectedRun = async () => {
    if (!selectedRun || isTerminalAgentRunStatus(selectedRun.status) || cancellingRun) return;
    setCancellingRun(true);
    setRunDetailError(null);
    try {
      const result = await customerApi.cancelRun(selectedRun.id);
      const refreshed = await customerApi.getRun(selectedRun.id);
      setSelectedRun(refreshed);
      setRuns((current) => current.map((item) => item.id === refreshed.id ? refreshed : item));
      setTasks((current) => current.map((task) => task.id === refreshed.id
        ? { ...task, completed: isTerminalAgentRunStatus(refreshed.status), category: agentRunStatusLabel(refreshed.status) }
        : task));
      showToast(result.status === 'cancel_requested' ? 'Permintaan pembatalan diteruskan ke worker.' : 'Status Agent Run diperbarui.', 'success');
    } catch (cause) {
      setRunDetailError(cause instanceof Error ? cause.message : 'Permintaan pembatalan gagal.');
    } finally {
      setCancellingRun(false);
    }
  };

  const retrySelectedRun = async () => {
    if (!selectedRun || !isTerminalAgentRunStatus(selectedRun.status) || retryingRun) return;
    setRetryingRun(true);
    setRunDetailError(null);
    try {
      const queued = await customerApi.retryRun(selectedRun.id, crypto.randomUUID());
      setSelectedRun(queued.run);
      setRuns((current) => [queued.run, ...current.filter((item) => item.id !== queued.run.id)]);
      showToast('Retry dibuat sebagai Agent Run baru melalui antrean backend.', 'success');
      await openRunDetails(queued.run);
    } catch (cause) {
      setRunDetailError(cause instanceof Error ? cause.message : 'Retry Agent Run gagal dibuat.');
    } finally {
      setRetryingRun(false);
    }
  };

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

  const downloadArtifact = async (artifactId: string) => {
    if (downloadingArtifactId) return;
    setDownloadingArtifactId(artifactId);
    try {
      const result = await artifactApi.signedDownload(artifactId);
      window.open(result.url, '_blank', 'noopener,noreferrer');
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Artefak gagal diunduh.', 'error');
    } finally {
      setDownloadingArtifactId(null);
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
          completed: isTerminalAgentRunStatus(run.status),
          category: agentRunStatusLabel(run.status),
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

  const handleLoadMoreArtifacts = async () => {
    if (!nextArtifactCursor || loadingMoreArtifacts) return;
    setLoadingMoreArtifacts(true);
    setArtifactPaginationError(null);
    try {
      const page = await artifactApi.listPage(50, nextArtifactCursor);
      setArtifacts((current) => {
        const known = new Set(current.map((artifact) => artifact.id));
        return [...current, ...page.items.filter((artifact) => !known.has(artifact.id))];
      });
      setNextArtifactCursor(page.nextCursor);
    } catch (cause) {
      setArtifactPaginationError(cause instanceof Error ? cause.message : 'Halaman artefak berikutnya tidak dapat dimuat.');
    } finally {
      setLoadingMoreArtifacts(false);
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
          {loadError && <div className="p-3 rounded-xl border border-rose-200 bg-rose-50 text-rose-700 text-xs">{loadError}</div>}
          {filteredTasks.length === 0 ? (
            <div className="p-8 text-center bg-white rounded-3xl border border-slate-100 text-slate-500">
              <CheckCircle2 className="w-10 h-10 mx-auto text-slate-300 mb-2" />
              <p className="text-xs font-medium">Belum ada Agent Run tersimpan</p>
              <p className="text-[11px] mt-1">Mulai percakapan melalui Chat AI untuk membuat workflow backend.</p>
            </div>
          ) : (
            filteredTasks.map((task) => (
              <button
                type="button"
                key={task.id}
                onClick={() => {
                  const run = runs.find((item) => item.id === task.id);
                  if (run) void openRunDetails(run);
                }}
                aria-label={`Lihat detail Agent Run ${task.id.slice(0, 8)}`}
                className={`w-full text-left p-3.5 rounded-2xl border transition-all flex items-center gap-3 group ${
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
              </button>
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

      {/* Run-linked artifacts from the authenticated private Artifact API. */}
      {activeTab === 'artifacts' && (
        <div className="p-5 rounded-3xl bg-white border border-slate-100 shadow-xs space-y-3">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Artefak Agent Run</h2>
            <p className="text-xs text-slate-500 mt-1">Hasil kerja privat ditampilkan bersama hubungan Agent Run yang tercatat di backend.</p>
          </div>
          {loadError && <p className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">{loadError}</p>}
          {artifacts.length === 0 ? (
            <p className="rounded-xl bg-slate-50 p-4 text-xs text-slate-500">Belum ada artefak privat yang tersimpan untuk akun ini.</p>
          ) : (
            <div className="space-y-2">
              {artifacts.map((artifact) => {
                const run = artifact.run_id ? runs.find((item) => item.id === artifact.run_id) : undefined;
                const filename = typeof artifact.metadata?.filename === 'string' ? artifact.metadata.filename : artifact.storage_path.split('/').pop();
                const prompt = run?.input?.prompt;
                return (
                  <div key={artifact.id} className="rounded-2xl border border-slate-200 p-3 flex items-start gap-3">
                    <div className="w-9 h-9 shrink-0 rounded-xl bg-red-50 text-red-600 flex items-center justify-center"><FileText className="w-4 h-4" /></div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-xs font-semibold text-slate-900">{filename}</p>
                      <p className="mt-1 text-[10px] text-slate-500">{artifact.mime_type || 'File'} · {new Date(artifact.created_at).toLocaleString('id-ID')}</p>
                      <p className="mt-1 text-[10px] text-slate-500">{artifact.run_id ? 'Agent Run ' + artifact.run_id.slice(0, 8) + (typeof prompt === 'string' ? ' · ' + prompt.slice(0, 72) : '') : 'Belum ditautkan ke Agent Run'}</p>
                    </div>
                    <button type="button" onClick={() => void downloadArtifact(artifact.id)} disabled={downloadingArtifactId === artifact.id} className="inline-flex shrink-0 items-center gap-1 rounded-lg border border-slate-200 px-2.5 py-1.5 text-[10px] font-semibold text-slate-700 disabled:opacity-50">
                      {downloadingArtifactId === artifact.id ? <Loader2 className="h-3 w-3 animate-spin" /> : <Download className="h-3 w-3" />}
                      Unduh
                    </button>
                  </div>
                );
              })}
            </div>
          )}
          {artifactPaginationError && <p role="alert" className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">{artifactPaginationError}</p>}
          {nextArtifactCursor && (
            <button type="button" onClick={() => void handleLoadMoreArtifacts()} disabled={loadingMoreArtifacts}
              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-semibold text-slate-700 disabled:opacity-50">
              {loadingMoreArtifacts ? 'Memuat artefak…' : 'Muat artefak berikutnya'}
            </button>
          )}
          <button onClick={() => onOpenWorkspaceFiles?.()} className="w-full py-3 rounded-2xl bg-red-600 text-white text-xs font-bold">Buka Workspace File</button>
        </div>
      )}

      {/* Durable Agent Run detail: only owner-safe backend projections are rendered. */}
      {selectedRun && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
          <div className="w-full max-w-2xl max-h-[88vh] overflow-y-auto rounded-3xl bg-white p-5 shadow-2xl border border-slate-100 space-y-4">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <h3 className="text-base font-bold text-slate-900">Detail Agent Run</h3>
                <p className="text-[11px] text-slate-500 break-all">{selectedRun.id}</p>
                <p className="mt-1 text-xs font-semibold text-slate-700">Status backend: {agentRunStatusLabel(selectedRun.status)} · Attempt {selectedRun.attempt ?? '—'} / {selectedRun.max_attempts ?? '—'}</p>
              </div>
              <button type="button" onClick={() => setSelectedRun(null)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600">Tutup</button>
            </div>
            {runDetailError && <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">{runDetailError}</p>}
            {runDetailLoading ? <p className="text-xs text-slate-500">Memuat lifecycle dari FastAPI…</p> : (
              <>
                {typeof selectedRun.output?.text === 'string' && (
                  <section className="rounded-2xl border border-emerald-200 bg-emerald-50 p-3 space-y-1">
                    <h4 className="text-xs font-bold text-emerald-900">Output</h4>
                    <p className="whitespace-pre-wrap text-xs text-emerald-950">{selectedRun.output.text}</p>
                  </section>
                )}
                {selectedRun.last_checkpoint_key && (
                  <p className="rounded-xl bg-slate-50 px-3 py-2 text-[11px] text-slate-600">Checkpoint terakhir: <span className="font-semibold">{selectedRun.last_checkpoint_key}</span></p>
                )}
                {runProgress && (
                  <section className="space-y-2 rounded-xl border border-slate-200 bg-white p-3">
                    <div className="flex items-center justify-between gap-2">
                      <h4 className="text-xs font-bold text-slate-900">Progress eksekusi</h4>
                      <span className="text-xs font-bold tabular-nums text-slate-700">{runProgress.percentage}%</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                      <div className="h-full rounded-full bg-red-600 transition-all" style={{ width: `${Math.max(0, Math.min(100, runProgress.percentage))}%` }} />
                    </div>
                    <p className="text-[10px] text-slate-500">{runProgress.completed_steps} dari {runProgress.total_steps} langkah selesai{runProgress.current_step ? ' · Saat ini: ' + runProgress.current_step : ''}</p>
                  </section>
                )}
                <section className="space-y-2">
                  <h4 className="text-xs font-bold text-slate-900">Durable workflow steps ({runSteps.length})</h4>
                  {runSteps.length ? runSteps.map((step) => (
                    <div key={step.id} className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 p-2.5">
                      <div className="min-w-0"><p className="truncate text-xs font-semibold text-slate-800">{step.sequence}. {step.step_key}</p><p className="text-[10px] text-slate-500">{step.started_at ? new Date(step.started_at).toLocaleString('id-ID') : 'Belum dimulai'}</p><p className="text-[10px] text-slate-400">{step.dependencies.length ? 'Bergantung pada langkah ' + step.dependencies.map((dependency) => dependency + 1).join(', ') : 'Tanpa dependensi'}</p></div>
                      <span className="shrink-0 rounded-full bg-slate-100 px-2 py-1 text-[10px] font-semibold text-slate-700">{step.status}</span>
                    </div>
                  )) : <p className="text-[11px] text-slate-500">Belum ada step yang dipersist oleh worker.</p>}
                </section>
                <section className="space-y-2">
                  <h4 className="text-xs font-bold text-slate-900">Execution events ({runActivity.length})</h4>
                  {runActivity.length ? runActivity.map((event) => (
                    <div key={event.id} className="rounded-xl border border-slate-200 p-2.5">
                      <div className="flex items-center justify-between gap-2"><p className="text-xs font-semibold text-slate-800">#{event.sequence} · {event.message || event.event_type}</p><span className="text-[10px] text-slate-500">{event.level || 'INFO'}</span></div>
                      <p className="mt-1 text-[10px] text-slate-500">{new Date(event.timestamp).toLocaleString('id-ID')}{event.tool ? ' · Tool: ' + event.tool : ''}{event.phase ? ' · ' + event.phase : ''}{typeof event.progress === 'number' ? ' · ' + event.progress + '%' : ''}</p>
                    </div>
                  )) : <p className="text-[11px] text-slate-500">Belum ada event yang tersedia pada safe activity projection.</p>}
                </section>
              </>
            )}
            <div className="flex flex-wrap justify-end gap-2 border-t border-slate-100 pt-3">
              {!isTerminalAgentRunStatus(selectedRun.status) && (
                <button type="button" onClick={() => void cancelSelectedRun()} disabled={cancellingRun}
                  className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-2 text-xs font-semibold text-rose-700 disabled:opacity-50">
                  {cancellingRun ? 'Mengirim pembatalan…' : 'Batalkan Agent Run'}
                </button>
              )}
              {isTerminalAgentRunStatus(selectedRun.status) && ['failed', 'timed_out', 'expired'].includes(selectedRun.status) && (
                <button type="button" onClick={() => void retrySelectedRun()} disabled={retryingRun}
                  className="rounded-xl bg-red-600 px-4 py-2 text-xs font-semibold text-white disabled:opacity-50">
                  {retryingRun ? 'Menjadwalkan retry…' : 'Jalankan ulang (run baru)'}
                </button>
              )}
            </div>
          </div>
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
