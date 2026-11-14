'use client';

import React, { useEffect, useState } from 'react';
import { ArrowLeft, CheckCircle2, Clock, Loader2, AlertCircle, Download } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { artifactApi, customerApi, customerToolApprovalApi, moreAiApiStream, type CustomerAgentRun, type CustomerAgentRunProgress, type CustomerToolApproval, type CustomerArtifact } from '@/lib/api/client';
import { agentRunStatusLabel, isActiveAgentRunStatus, isTerminalAgentRunStatus } from '@/lib/api/agent-run-status';

interface WorkflowProgressViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}



const runSummary = (run: CustomerAgentRun) => {
  const output = run.output || {};
  const error = run.error || {};
  if (typeof output.text === 'string' && output.text.trim()) return output.text;
  if (typeof output.content === 'string' && output.content.trim()) return output.content;
  if (typeof error.message === 'string' && error.message.trim()) return error.message;
  if (typeof error.code === 'string' && error.code.trim()) return error.code;
  return 'Belum ada ringkasan hasil yang disimpan untuk run ini.';
};

export const WorkflowProgressView: React.FC<WorkflowProgressViewProps> = ({
  onBack,
}) => {
  const [runs, setRuns] = useState<CustomerAgentRun[]>([]);
  const [artifacts, setArtifacts] = useState<CustomerArtifact[]>([]);
  const [downloadingArtifactId, setDownloadingArtifactId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [approvals, setApprovals] = useState<CustomerToolApproval[]>([]);
  const [approvalError, setApprovalError] = useState<string | null>(null);
  const [approvalActionId, setApprovalActionId] = useState<string | null>(null);
  const [nextRunCursor, setNextRunCursor] = useState<string | null>(null);
  const [loadingMoreRuns, setLoadingMoreRuns] = useState(false);
  const [runPaginationError, setRunPaginationError] = useState<string | null>(null);
  const [nextApprovalCursor, setNextApprovalCursor] = useState<string | null>(null);
  const [nextArtifactCursor, setNextArtifactCursor] = useState<string | null>(null);
  const [loadingMoreArtifacts, setLoadingMoreArtifacts] = useState(false);
  const [artifactPaginationError, setArtifactPaginationError] = useState<string | null>(null);
  const [loadingMoreApprovals, setLoadingMoreApprovals] = useState(false);
  const [expandedRunId, setExpandedRunId] = useState<string | null>(null);
  const [runSteps, setRunSteps] = useState<Record<string, Awaited<ReturnType<typeof customerApi.getRunSteps>>>>({});
  const [runActivity, setRunActivity] = useState<Record<string, Awaited<ReturnType<typeof customerApi.getRunActivity>>>>({});
  const [runProgress, setRunProgress] = useState<Record<string, CustomerAgentRunProgress>>({});
  const [runCheckpoints, setRunCheckpoints] = useState<Record<string, Array<{ sequence: number; event_type: string; created_at: string; checkpoint: Record<string, unknown> | null }>>>({});
  const [activityLoadingId, setActivityLoadingId] = useState<string | null>(null);
  const [stepLoadingId, setStepLoadingId] = useState<string | null>(null);
  const [runActionId, setRunActionId] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const loadRuns = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const [runsResult, approvalsResult, artifactsResult] = await Promise.allSettled([
          customerApi.agentRunsPage(50),
          customerToolApprovalApi.listPage(50),
          artifactApi.listPage(50),
        ]);
        if (active) {
          if (runsResult.status === 'fulfilled') {
            setRuns(runsResult.value.items);
            setNextRunCursor(runsResult.value.nextCursor);
          }
          else setError(runsResult.reason instanceof Error ? runsResult.reason.message : 'Workflow tidak dapat dimuat.');
          if (approvalsResult.status === 'fulfilled') {
            setApprovals(approvalsResult.value.items);
            setNextApprovalCursor(approvalsResult.value.nextCursor);
          }
          else setApprovalError(approvalsResult.reason instanceof Error ? approvalsResult.reason.message : 'Persetujuan tidak dapat dimuat.');
          if (artifactsResult.status === 'fulfilled') {
            setArtifacts(artifactsResult.value.items);
            setNextArtifactCursor(artifactsResult.value.nextCursor);
          }
          else setArtifactPaginationError(artifactsResult.reason instanceof Error ? artifactsResult.reason.message : 'Artefak workflow tidak dapat dimuat.');

        }
      } catch (cause) {
        if (active) setError(cause instanceof Error ? cause.message : 'Workflow tidak dapat dimuat.');
      } finally {
        if (active) setIsLoading(false);
      }
    };
    void loadRuns();
    return () => { active = false; };
  }, []);

  const decideApproval = async (approvalId: string, decision: 'approved' | 'denied') => {
    try {
      setApprovalActionId(approvalId);
      setApprovalError(null);
      const result = await customerToolApprovalApi.decide(approvalId, decision);
      setApprovals((current) => current.map((item) => item.id === approvalId
        ? { ...item, status: result.status, decided_at: result.decided_at }
        : item));
      // The decision RPC atomically re-queues a paused run. Keep the durable
      // approval decision visible even if the independent run-list refresh fails.
      try {
        const runPage = await customerApi.agentRunsPage(50);
        setRuns(runPage.items);
        setNextRunCursor(runPage.nextCursor);
        setRunPaginationError(null);
      } catch (refreshError) {
        setRunPaginationError(refreshError instanceof Error
          ? 'Keputusan tersimpan; status workflow belum dapat diperbarui: ' + refreshError.message
          : 'Keputusan tersimpan; status workflow belum dapat diperbarui.');
      }
    } catch (cause) {
      setApprovalError(cause instanceof Error ? cause.message : 'Keputusan persetujuan gagal disimpan.');
    } finally {
      setApprovalActionId(null);
    }
  };

  const loadMoreApprovals = async () => {
    if (!nextApprovalCursor || loadingMoreApprovals) return;
    setLoadingMoreApprovals(true);
    try {
      const page = await customerToolApprovalApi.listPage(50, nextApprovalCursor);
      setApprovals((current) => {
        const known = new Set(current.map((item) => item.id));
        return [...current, ...page.items.filter((item) => !known.has(item.id))];
      });
      setNextApprovalCursor(page.nextCursor);
    } catch (cause) {
      setApprovalError(cause instanceof Error ? cause.message : 'Riwayat persetujuan berikutnya tidak dapat dimuat.');
    } finally {
      setLoadingMoreApprovals(false);
    }
  };

  const loadMoreRuns = async () => {
    if (!nextRunCursor || loadingMoreRuns) return;
    setLoadingMoreRuns(true);
    setRunPaginationError(null);
    try {
      const page = await customerApi.agentRunsPage(50, nextRunCursor);
      setRuns((current) => {
        const known = new Set(current.map((run) => run.id));
        return [...current, ...page.items.filter((run) => !known.has(run.id))];
      });
      setNextRunCursor(page.nextCursor);
    } catch (cause) {
      setRunPaginationError(cause instanceof Error ? cause.message : 'Halaman workflow berikutnya tidak dapat dimuat.');
    } finally {
      setLoadingMoreRuns(false);
    }
  };

  const toggleRunDetails = async (runId: string) => {
    if (expandedRunId === runId) {
      setExpandedRunId(null);
      return;
    }
    setExpandedRunId(runId);
    if (runSteps[runId]) return;
    setStepLoadingId(runId);
    setActivityLoadingId(runId);
    try {
      const [steps, activity, progress, events] = await Promise.all([
        customerApi.getRunSteps(runId),
        customerApi.getRunActivity(runId, 0, 200),
        customerApi.getRunProgress(runId),
        customerApi.getRunEvents(runId, 0),
      ]);
      setRunSteps((current) => ({ ...current, [runId]: steps }));
      setRunActivity((current) => ({ ...current, [runId]: activity }));
      setRunProgress((current) => ({ ...current, [runId]: progress }));
      setRunCheckpoints((current) => ({
        ...current,
        [runId]: events
          .filter((event) => !!event.checkpoint)
          .map((event) => ({
            sequence: event.sequence,
            event_type: event.event_type,
            created_at: event.created_at,
            checkpoint: event.checkpoint,
          })),
      }));
    } catch (cause) {
      setRunPaginationError(cause instanceof Error ? cause.message : 'Tahapan atau aktivitas Agent Run tidak dapat dimuat.');
    } finally {
      setStepLoadingId(null);
      setActivityLoadingId(null);
    }
  };

  // Keep the expanded workflow synchronized with the same durable SSE event stream
  // used by the Task detail. Persisted run/step/activity reads remain authoritative.
  useEffect(() => {
    if (!expandedRunId) return;
    const controller = new AbortController();
    let active = true;
    const refreshSnapshot = async () => {
      const [runResult, stepsResult, activityResult, progressResult, eventsResult] = await Promise.allSettled([
        customerApi.getRun(expandedRunId),
        customerApi.getRunSteps(expandedRunId),
        customerApi.getRunActivity(expandedRunId, 0, 200),
        customerApi.getRunProgress(expandedRunId),
        customerApi.getRunEvents(expandedRunId, 0),
      ]);
      if (!active) return;
      if (runResult.status === 'fulfilled') {
        const fresh = runResult.value;
        setRuns((current) => current.map((run) => run.id === expandedRunId ? fresh : run));
        if (isTerminalAgentRunStatus(fresh.status)) controller.abort();
      }
      if (stepsResult.status === 'fulfilled') {
        setRunSteps((current) => ({ ...current, [expandedRunId]: stepsResult.value }));
      }
      if (activityResult.status === 'fulfilled') {
        setRunActivity((current) => ({ ...current, [expandedRunId]: activityResult.value }));
      }
      if (progressResult.status === 'fulfilled') {
        setRunProgress((current) => ({ ...current, [expandedRunId]: progressResult.value }));
      }
      if (eventsResult.status === 'fulfilled') {
        setRunCheckpoints((current) => ({
          ...current,
          [expandedRunId]: eventsResult.value
            .filter((event) => !!event.checkpoint)
            .map((event) => ({
              sequence: event.sequence,
              event_type: event.event_type,
              created_at: event.created_at,
              checkpoint: event.checkpoint,
            })),
        }));
      }
    };
    void moreAiApiStream(customerApi.streamRun(expandedRunId), ({ event }) => {
      if (
        event === 'run.started' || event === 'run.progress' || event === 'worker.checkpoint'
        || event.startsWith('planning.step.') || event.startsWith('tool.')
        || event.startsWith('approval.') || event === 'run.awaiting_approval'
        || event === 'run.resume_queued' || event.startsWith('run.')
      ) {
        void refreshSnapshot();
      }
    }, { signal: controller.signal, maxReconnects: 20 }).catch((cause) => {
      if (active && !(cause instanceof DOMException && cause.name === 'AbortError')) {
        setRunPaginationError(cause instanceof Error
          ? 'Live workflow stream terputus: ' + cause.message
          : 'Live workflow stream terputus. Status tersimpan tetap dapat dimuat ulang.');
      }
    });
    return () => {
      active = false;
      controller.abort();
    };
  }, [expandedRunId]);

  const cancelAgentRun = async (runId: string) => {
    if (runActionId) return;
    setRunActionId(runId);
    setRunPaginationError(null);
    try {
      const result = await customerApi.cancelRun(runId);
      setRuns((current) => current.map((run) => run.id === runId ? { ...run, status: result.status } : run));
    } catch (cause) {
      setRunPaginationError(cause instanceof Error ? cause.message : 'Permintaan pembatalan Agent Run gagal.');
    } finally {
      setRunActionId(null);
    }
  };

  // Manual retry is a new durable run, not an in-place checkpoint rewind.
  // Keep the UI allowlist aligned with FastAPI; backend replay-safety checks remain authoritative.
  const retryableRunStatuses = new Set(['failed', 'timed_out', 'expired']);
  const retryAgentRun = async (runId: string) => {
    if (runActionId) return;
    setRunActionId(runId);
    setRunPaginationError(null);
    try {
      await customerApi.retryRun(runId, crypto.randomUUID());
      const page = await customerApi.agentRunsPage(50);
      setRuns(page.items);
      setNextRunCursor(page.nextCursor);
      setExpandedRunId(null);
      setRunSteps((current) => { const next = { ...current }; delete next[runId]; return next; });
      setRunActivity((current) => { const next = { ...current }; delete next[runId]; return next; });
      setRunProgress((current) => { const next = { ...current }; delete next[runId]; return next; });
    } catch (cause) {
      setRunPaginationError(cause instanceof Error
        ? 'Retry tidak dapat dijalankan: ' + cause.message
        : 'Retry tidak dapat dijalankan. Periksa kelayakan replay pada backend.');
    } finally {
      setRunActionId(null);
    }
  };

  const loadMoreArtifacts = async () => {
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
      setArtifactPaginationError(cause instanceof Error ? cause.message : 'Halaman artefak workflow berikutnya tidak dapat dimuat.');
    } finally {
      setLoadingMoreArtifacts(false);
    }
  };

  const downloadRunArtifact = async (artifactId: string) => {
    if (downloadingArtifactId) return;
    setDownloadingArtifactId(artifactId);
    try {
      const result = await artifactApi.signedDownload(artifactId);
      window.open(result.url, '_blank', 'noopener,noreferrer');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Artefak run tidak dapat diunduh.');
    } finally {
      setDownloadingArtifactId(null);
    }
  };

  const activeCount = runs.filter((run) => isActiveAgentRunStatus(run.status)).length;
  // Terminal outcomes include failures/cancellations; only succeeded runs count as completed successfully.
  const completedCount = runs.filter((run) => run.status === 'succeeded').length;

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <button onClick={onBack} className="p-1 rounded-lg text-slate-400 hover:text-slate-700" aria-label="Kembali">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="text-center">
          <h1 className="text-base font-bold text-slate-900 leading-tight">Workflow & Agent Runs</h1>
          <span className="text-[10px] text-slate-500 font-medium">Status tersimpan dari OpenManus Worker</span>
        </div>
        <div className="w-5" />
      </div>

      {(approvals.length > 0 || approvalError || nextApprovalCursor) && (
        <section className="p-4 rounded-3xl bg-amber-50/70 border border-amber-200 space-y-3">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Persetujuan Tool Agent</h2>
            <p className="text-[11px] text-slate-600 mt-1">Worker akan melanjutkan eksekusi hanya setelah persetujuan untuk argumen yang sama dikonsumsi satu kali.</p>
          </div>
          {approvals.filter((item) => item.status === 'pending').map((item) => (
            <div key={item.id} className="p-3 rounded-2xl bg-white border border-amber-100 space-y-2">
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-bold text-slate-900">{item.tool_key}</span>
                <span className="text-[10px] text-amber-700 font-semibold">Menunggu keputusan</span>
              </div>
              <p className="text-[11px] text-slate-600">{item.summary}</p>
              <p className="text-[10px] text-slate-400">Berlaku sampai {new Date(item.expires_at).toLocaleString('id-ID')}</p>
              <div className="grid grid-cols-2 gap-2">
                <button disabled={approvalActionId === item.id} onClick={() => void decideApproval(item.id, 'denied')} className="py-2 rounded-xl border border-slate-200 text-slate-600 text-xs font-bold disabled:opacity-50">Tolak</button>
                <button disabled={approvalActionId === item.id} onClick={() => void decideApproval(item.id, 'approved')} className="py-2 rounded-xl bg-red-600 text-white text-xs font-bold disabled:opacity-50">Setujui</button>
              </div>
            </div>
          ))}
          {approvals.some((item) => item.status !== 'pending') && (
            <div className="space-y-2 border-t border-amber-200 pt-3">
              <h3 className="text-[11px] font-bold text-slate-700">Riwayat keputusan</h3>
              {approvals.filter((item) => item.status !== 'pending').map((item) => {
                const statusLabel = item.status === 'approved' ? 'Disetujui'
                  : item.status === 'denied' ? 'Ditolak'
                    : item.status === 'expired' ? 'Kedaluwarsa' : 'Sudah dikonsumsi worker';
                const statusClass = item.status === 'approved' ? 'bg-emerald-50 text-emerald-700'
                  : item.status === 'denied' ? 'bg-rose-50 text-rose-700'
                    : 'bg-slate-100 text-slate-600';
                const eventAt = item.consumed_at || item.decided_at || item.expires_at;
                return (
                  <div key={item.id} className="rounded-xl border border-slate-100 bg-white p-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="truncate text-xs font-semibold text-slate-800">{item.tool_key}</span>
                      <span className={`shrink-0 rounded-full px-2 py-1 text-[10px] font-semibold ${statusClass}`}>{statusLabel}</span>
                    </div>
                    <p className="mt-1 text-[11px] text-slate-600">{item.summary}</p>
                    <p className="mt-1 text-[10px] text-slate-400">{new Date(eventAt).toLocaleString('id-ID')}</p>
                  </div>
                );
              })}
            </div>
          )}
          {approvalError && <p className="text-xs text-rose-700">{approvalError}</p>}
          {nextApprovalCursor && (
            <button type="button" onClick={() => void loadMoreApprovals()} disabled={loadingMoreApprovals}
              className="w-full py-2 rounded-xl border border-amber-200 bg-white text-xs font-semibold text-amber-800 disabled:opacity-50">
              {loadingMoreApprovals ? 'Memuat persetujuan…' : 'Muat riwayat persetujuan'}
            </button>
          )}
        </section>
      )}

      <div className="p-5 rounded-3xl bg-white border border-slate-100 shadow-xs space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-2xl bg-slate-50 border border-slate-200 p-3">
            <p className="text-[10px] text-slate-500 font-medium">Run aktif</p>
            <p className="text-xl font-black text-slate-900">{isLoading ? '—' : activeCount}</p>
          </div>
          <div className="rounded-2xl bg-slate-50 border border-slate-200 p-3">
            <p className="text-[10px] text-slate-500 font-medium">Run selesai</p>
            <p className="text-xl font-black text-slate-900">{isLoading ? '—' : completedCount}</p>
          </div>
        </div>

        {isLoading && (
          <div className="py-10 flex items-center justify-center gap-2 text-sm text-slate-500">
            <Loader2 className="w-4 h-4 animate-spin" /> Memuat workflow dari server...
          </div>
        )}

        {!isLoading && error && (
          <div className="p-4 rounded-2xl border border-rose-200 bg-rose-50 text-rose-700 text-xs flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {!isLoading && !error && runs.length === 0 && (
          <div className="py-10 text-center text-slate-500">
            <Clock className="w-8 h-8 mx-auto mb-2 text-slate-300" />
            <p className="text-sm font-semibold">Belum ada workflow</p>
            <p className="text-xs mt-1">Run OpenManus yang dibuat akan muncul di sini setelah tersimpan di server.</p>
          </div>
        )}

        {!isLoading && !error && runs.length > 0 && (
          <div className="space-y-3">
            {runs.map((run) => {
              const terminal = isTerminalAgentRunStatus(run.status);
              const successful = run.status === 'succeeded';
              return (
                <div key={run.id} className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80 flex items-start gap-3">
                  <div className="mt-0.5 shrink-0">
                    {successful ? (
                      <div className="w-6 h-6 rounded-full bg-emerald-600 text-white flex items-center justify-center"><CheckCircle2 className="w-4 h-4" /></div>
                    ) : terminal ? (
                      <div className="w-6 h-6 rounded-full bg-rose-100 text-rose-700 flex items-center justify-center"><AlertCircle className="w-4 h-4" /></div>
                    ) : (
                      <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center"><Loader2 className="w-4 h-4 animate-spin" /></div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="text-xs font-bold text-slate-900 truncate">Agent Run · {run.id.slice(0, 8)}</h3>
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${successful ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : terminal ? 'bg-rose-50 text-rose-700 border border-rose-200' : 'bg-blue-50 text-blue-700 border border-blue-200'}`}>
                        {agentRunStatusLabel(run.status)}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 mt-1">Conversation: {run.conversation_id || 'Tidak terkait percakapan'}</p>
                    <p className="text-[11px] text-slate-700 mt-2 bg-white p-2.5 rounded-xl border border-slate-100 whitespace-pre-wrap break-words">{runSummary(run)}</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      <button type="button" onClick={() => void toggleRunDetails(run.id)} className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-[10px] font-semibold text-slate-700">
                        {expandedRunId === run.id ? 'Tutup tahapan' : 'Lihat tahapan & progress'}
                      </button>
                      {!terminal && (
                        <button type="button" onClick={() => void cancelAgentRun(run.id)} disabled={runActionId === run.id} className="rounded-lg border border-rose-200 bg-white px-2.5 py-1.5 text-[10px] font-semibold text-rose-700 disabled:opacity-50">
                          {runActionId === run.id ? 'Meminta pembatalan…' : 'Batalkan run'}
                        </button>
                      )}
                      {retryableRunStatuses.has(run.status) && (
                        <button type="button" onClick={() => void retryAgentRun(run.id)} disabled={runActionId === run.id} className="rounded-lg border border-blue-200 bg-white px-2.5 py-1.5 text-[10px] font-semibold text-blue-700 disabled:opacity-50">
                          {runActionId === run.id ? 'Mengirim retry…' : 'Retry sebagai run baru'}
                        </button>
                      )}
                    </div>
                    {expandedRunId === run.id && (() => {
                      const mediaArtifacts = artifacts.filter((artifact) =>
                        artifact.run_id === run.id
                        && ['image', 'video'].includes(String(artifact.metadata?.media_type || '').toLowerCase()),
                      );
                      const mediaActivities = (runActivity[run.id]?.items || []).filter((event) =>
                        ['image_generate', 'video_generate'].includes(String(event.tool || '').toLowerCase()),
                      );
                      if (mediaArtifacts.length === 0 && mediaActivities.length === 0) return null;
                      const mediaStatus = mediaArtifacts.length > 0
                        ? 'succeeded'
                        : isActiveAgentRunStatus(run.status) ? 'processing' : run.status === 'failed' ? 'failed' : 'unknown';
                      const mediaStatusLabel: Record<string, string> = {
                        succeeded: 'Artifact tersimpan',
                        processing: 'Agent Run sedang memproses media',
                        failed: 'Agent Run gagal',
                        unknown: 'Status hasil media belum dapat dipastikan',
                      };
                      return (
                        <section className="mt-3 rounded-xl border border-indigo-200 bg-indigo-50/50 p-3">
                          <div className="flex items-center justify-between gap-2">
                            <p className="text-[10px] font-bold uppercase tracking-wide text-indigo-900">Media job · OpenManus Agent Run</p>
                            <span className="rounded-full bg-white px-2 py-1 text-[9px] font-semibold text-indigo-700">{mediaStatusLabel[mediaStatus]}</span>
                          </div>
                          <p className="mt-1 text-[10px] leading-relaxed text-indigo-800">
                            Lifecycle media mengikuti run durable, checkpoint worker, accounting, dan artifact tersimpan. Status provider yang tidak dipublikasikan backend tidak ditebak oleh dashboard.
                          </p>
                          {mediaArtifacts.length > 0 ? (
                            <div className="mt-2 space-y-1.5">
                              {mediaArtifacts.map((artifact) => (
                                <div key={artifact.id} className="flex items-center justify-between gap-2 rounded-lg border border-indigo-100 bg-white p-2">
                                  <div className="min-w-0">
                                    <p className="truncate text-[10px] font-semibold text-slate-800">
                                      {String(artifact.metadata?.filename || artifact.storage_path.split('/').pop())}
                                    </p>
                                    <p className="text-[9px] text-slate-500">
                                      {String(artifact.metadata?.media_type)} · {artifact.mime_type || 'MIME tidak tersedia'} · {artifact.size_bytes === null ? 'Ukuran tidak tersedia' : (artifact.size_bytes / 1048576).toFixed(2) + ' MB'}
                                    </p>
                                  </div>
                                  <button type="button" onClick={() => void downloadRunArtifact(artifact.id)} disabled={downloadingArtifactId === artifact.id}
                                    className="inline-flex shrink-0 items-center gap-1 rounded-lg border border-indigo-200 px-2 py-1 text-[10px] font-semibold text-indigo-700 disabled:opacity-50">
                                    {downloadingArtifactId === artifact.id ? <Loader2 className="h-3 w-3 animate-spin" /> : <Download className="h-3 w-3" />}
                                    Unduh
                                  </button>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="mt-2 text-[10px] text-indigo-800">Tool media tercatat pada aktivitas run, tetapi artifact final belum tersedia. Periksa status run dan checkpoint untuk mengetahui hasil pemrosesan.</p>
                          )}
                        </section>
                      );
                    })()}
                    {expandedRunId === run.id && (
                      <div className="mt-2 rounded-xl border border-slate-200 bg-white p-3">
                        {runProgress[run.id] && (
                          <div className="mb-3 rounded-xl border border-slate-200 bg-slate-50 p-3">
                            <div className="flex items-center justify-between gap-2">
                              <p className="text-[10px] font-bold uppercase tracking-wide text-slate-500">Progress eksekusi</p>
                              <span className="text-xs font-bold tabular-nums text-slate-700">{runProgress[run.id].percentage}%</span>
                            </div>
                            <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
                              <div className="h-full rounded-full bg-red-600 transition-all" style={{ width: `${Math.max(0, Math.min(100, runProgress[run.id].percentage))}%` }} />
                            </div>
                            <p className="mt-1.5 text-[10px] text-slate-500">{runProgress[run.id].completed_steps} dari {runProgress[run.id].total_steps} langkah selesai{runProgress[run.id].current_step ? ' · Saat ini: ' + runProgress[run.id].current_step : ''}</p>
                          </div>
                        )}
                        <p className="text-[10px] font-bold uppercase tracking-wide text-slate-500">Durable workflow steps</p>
                        {stepLoadingId === run.id ? (
                          <p className="mt-2 text-[11px] text-slate-500">Memuat tahapan dari FastAPI…</p>
                        ) : (runSteps[run.id] || []).length === 0 ? (
                          <p className="mt-2 text-[11px] text-slate-500">Belum ada step yang dipublikasikan untuk run ini.</p>
                        ) : (
                          <ol className="mt-2 space-y-2">
                            {(runSteps[run.id] || []).map((step) => (
                              <li key={step.id} className="flex items-start justify-between gap-3 border-b border-slate-100 pb-2 last:border-0 last:pb-0">
                                <div className="min-w-0">
                                  <p className="text-[11px] font-semibold text-slate-800">{step.sequence}. {step.step_key}</p>
                                  <p className="mt-0.5 text-[10px] text-slate-400">{step.started_at ? new Date(step.started_at).toLocaleString('id-ID') : 'Belum dimulai'}{step.finished_at ? ' · selesai ' + new Date(step.finished_at).toLocaleString('id-ID') : ''}</p><p className="mt-0.5 text-[10px] text-slate-400">{step.dependencies.length ? 'Bergantung pada langkah ' + step.dependencies.map((dependency) => dependency + 1).join(', ') : 'Tanpa dependensi'}</p>
                                </div>
                                <span className="shrink-0 rounded-full bg-slate-100 px-2 py-1 text-[10px] font-semibold text-slate-600">{step.status}</span>
                              </li>
                            ))}
                          </ol>
                        )}
                        {(runCheckpoints[run.id] || []).length > 0 && (
                          <div className="mt-3 rounded-xl border border-cyan-200 bg-cyan-50/50 p-3">
                            <p className="text-[10px] font-bold uppercase tracking-wide text-cyan-900">Checkpoint tersimpan (safe projection)</p>
                            <p className="mt-1 text-[10px] text-cyan-800">Checkpoint berasal dari event durable backend. Data tool argument, credential, dan observation privat tidak ditampilkan.</p>
                            <ol className="mt-2 space-y-2">
                              {(runCheckpoints[run.id] || []).map((item) => (
                                <li key={item.sequence} className="rounded-lg border border-cyan-100 bg-white p-2">
                                  <div className="flex items-center justify-between gap-2">
                                    <span className="text-[10px] font-semibold text-slate-800">#{item.sequence} · {item.event_type}</span>
                                    <span className="text-[9px] text-slate-400">{new Date(item.created_at).toLocaleString('id-ID')}</span>
                                  </div>
                                  {item.checkpoint && Object.entries(item.checkpoint).map(([key, value]) => (
                                    <p key={key} className="mt-1 break-words text-[10px] text-slate-600">{key}: {typeof value === 'string' ? value : JSON.stringify(value)}</p>
                                  ))}
                                </li>
                              ))}
                            </ol>
                          </div>
                        )}
                        <div className="mt-3 border-t border-slate-100 pt-3">
                          <p className="text-[10px] font-bold uppercase tracking-wide text-slate-500">Event activity (safe backend projection)</p>
                          {activityLoadingId === run.id ? (
                            <p className="mt-2 text-[11px] text-slate-500">Memuat event…</p>
                          ) : (runActivity[run.id]?.items || []).length === 0 ? (
                            <p className="mt-2 text-[11px] text-slate-500">Belum ada aktivitas yang dipublikasikan.</p>
                          ) : (
                            <ol className="mt-2 space-y-2">
                              {(runActivity[run.id]?.items || []).map((event) => (
                                <li key={event.id} className="flex items-start gap-2">
                                  <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-400" />
                                  <div className="min-w-0 flex-1">
                                    <p className="text-[11px] font-medium text-slate-700">{event.message || event.event_type}{event.tool ? ' · ' + event.tool : ''}</p>
                                    <p className="text-[10px] text-slate-400">#{event.sequence} · {new Date(event.timestamp).toLocaleString('id-ID')}{event.progress !== undefined ? ' · ' + event.progress + '%' : ''}</p>
                                  </div>
                                  {event.level && <span className="text-[9px] font-semibold text-slate-500">{event.level}</span>}
                                </li>
                              ))}
                            </ol>
                          )}
                        </div>
                      </div>
                    )}
                    {artifacts.filter((artifact) => artifact.run_id === run.id).length > 0 && (
                      <div className="mt-2 rounded-xl border border-slate-200 bg-white p-2.5">
                        <p className="mb-1.5 text-[10px] font-semibold text-slate-600">Artefak hasil run</p>
                        <div className="space-y-1.5">
                          {artifacts.filter((artifact) => artifact.run_id === run.id).map((artifact) => (
                            <div key={artifact.id} className="flex items-center justify-between gap-2">
                              <span className="min-w-0 truncate text-[10px] text-slate-600">
                                {typeof artifact.metadata?.filename === 'string' ? artifact.metadata.filename : artifact.storage_path.split('/').pop()}
                              </span>
                              <button type="button" onClick={() => void downloadRunArtifact(artifact.id)} disabled={downloadingArtifactId === artifact.id} className="inline-flex shrink-0 items-center gap-1 rounded-lg border border-slate-200 px-2 py-1 text-[10px] font-semibold text-slate-700 disabled:opacity-50">
                                {downloadingArtifactId === artifact.id ? <Loader2 className="h-3 w-3 animate-spin" /> : <Download className="h-3 w-3" />}
                                Unduh
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
            {runPaginationError && <div role="alert" className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">{runPaginationError}</div>}
            {nextRunCursor && (
              <button type="button" onClick={() => void loadMoreRuns()} disabled={loadingMoreRuns}
                className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50">
                {loadingMoreRuns ? 'Memuat workflow…' : 'Muat workflow berikutnya'}
              </button>
            )}
            {artifactPaginationError && <div role="alert" className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">{artifactPaginationError}</div>}
            {nextArtifactCursor && (
              <button type="button" onClick={() => void loadMoreArtifacts()} disabled={loadingMoreArtifacts}
                className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50">
                {loadingMoreArtifacts ? 'Memuat artefak…' : 'Muat artefak berikutnya'}
              </button>
            )}
          </div>
        )}

        <button onClick={onBack} className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition shadow-xs">
          Kembali
        </button>
      </div>
    </div>
  );
};
