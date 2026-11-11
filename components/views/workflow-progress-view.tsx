'use client';

import React, { useEffect, useState } from 'react';
import { ArrowLeft, CheckCircle2, Clock, Loader2, AlertCircle } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { customerApi, type CustomerAgentRun } from '@/lib/api/client';

interface WorkflowProgressViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

const statusLabel: Record<string, string> = {
  queued: 'Dalam antrean',
  pending: 'Menunggu worker',
  running: 'Sedang berjalan',
  awaiting_approval: 'Menunggu persetujuan',
  succeeded: 'Selesai',
  failed: 'Gagal',
  cancelled: 'Dibatalkan',
  expired: 'Kedaluwarsa',
};

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
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const loadRuns = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const result = await customerApi.agentRuns();
        if (active) setRuns(result);
      } catch (cause) {
        if (active) setError(cause instanceof Error ? cause.message : 'Workflow tidak dapat dimuat.');
      } finally {
        if (active) setIsLoading(false);
      }
    };
    void loadRuns();
    return () => { active = false; };
  }, []);

  const activeCount = runs.filter((run) => ['queued', 'pending', 'running', 'awaiting_approval'].includes(run.status)).length;
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
              const terminal = ['succeeded', 'failed', 'cancelled', 'expired'].includes(run.status);
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
                        {statusLabel[run.status] || run.status}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 mt-1">Conversation: {run.conversation_id || 'Tidak terkait percakapan'}</p>
                    <p className="text-[11px] text-slate-700 mt-2 bg-white p-2.5 rounded-xl border border-slate-100 whitespace-pre-wrap break-words">{runSummary(run)}</p>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <button onClick={onBack} className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition shadow-xs">
          Kembali
        </button>
      </div>
    </div>
  );
};
