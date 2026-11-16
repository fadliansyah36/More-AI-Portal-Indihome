'use client';

import React, { useEffect, useState } from 'react';
import { Hand, Send, RefreshCw, ShieldCheck, AlertCircle } from 'lucide-react';
import { browserSessionApi, type CustomerBrowserTakeoverCommand } from '@/lib/api/client';

type Props = { sessionId: string; sessionStatus: string };

const statusCopy: Record<string, string> = {
  queued: 'Perintah tersimpan; menunggu worker.',
  processing: 'Worker sedang meneruskan input ke sesi OpenFuse.',
  succeeded: 'Input diteruskan ke sesi browser.',
  failed: 'Perintah gagal diproses. Periksa kode error sebelum mencoba ulang.',
  expired: 'Grant atau antrean perintah telah kedaluwarsa.',
};

export function BrowserSessionTakeover({ sessionId, sessionStatus }: Props) {
  const [payload, setPayload] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [command, setCommand] = useState<CustomerBrowserTakeoverCommand | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [polling, setPolling] = useState(false);

  const refreshCommand = async (commandId: string) => {
    const latest = await browserSessionApi.takeoverCommand(commandId);
    setCommand(latest);
    setPolling(latest.status === 'queued' || latest.status === 'processing');
  };

  useEffect(() => {
    if (!command || (command.status !== 'queued' && command.status !== 'processing')) return;
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const poll = async () => {
      try {
        const latest = await browserSessionApi.takeoverCommand(command.command_id);
        if (!active) return;
        setCommand(latest);
        setPolling(latest.status === 'queued' || latest.status === 'processing');
        if (latest.status === 'queued' || latest.status === 'processing') {
          timer = setTimeout(() => { void poll(); }, 2000);
        }
      } catch (cause) {
        if (!active) return;
        setError(cause instanceof Error ? cause.message : 'Status perintah tidak dapat diperbarui.');
        setPolling(false);
      }
    };
    timer = setTimeout(() => { void poll(); }, 1200);
    return () => { active = false; if (timer) clearTimeout(timer); };
  }, [command?.command_id, command?.status]);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (sessionStatus !== 'active' || submitting) return;
    setError(null);
    let input: unknown;
    try {
      input = JSON.parse(payload);
    } catch {
      setError('Payload harus berupa JSON yang valid.');
      return;
    }
    if (!input || typeof input !== 'object' || Array.isArray(input)) {
      setError('Payload harus berupa object JSON sesuai kontrak input OpenFuse.');
      return;
    }
    setSubmitting(true);
    setCommand(null);
    try {
      // Grant is short-lived, one-time and held only in memory for this request.
      const grant = await browserSessionApi.createTakeoverGrant(sessionId, 90);
      const queued = await browserSessionApi.submitTakeoverInput(
        sessionId, grant.token, input as Record<string, unknown>,
      );
      await refreshCommand(queued.command_id);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Input browser gagal dikirim.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="mt-3 rounded-xl border border-slate-200 bg-white p-3 space-y-2.5">
      <div className="flex items-center gap-2">
        <Hand className="h-3.5 w-3.5 text-slate-500" />
        <span className="text-[10px] font-semibold text-slate-700">Human Takeover</span>
        <span className="ml-auto inline-flex items-center gap-1 text-[9px] text-slate-500">
          <ShieldCheck className="h-3 w-3" /> Grant sekali pakai · 90 detik
        </span>
      </div>
      <p className="text-[10px] leading-relaxed text-slate-500">
        Kirim payload JSON ke sesi browser yang sama. Format payload mengikuti kontrak input OpenFuse; token akses tidak disimpan di browser.
      </p>
      {sessionStatus === 'active' ? (
        <form onSubmit={(event) => void submit(event)} className="space-y-2">
          <textarea value={payload} onChange={(event) => setPayload(event.target.value)}
            rows={3} maxLength={16384} spellCheck={false} placeholder="{ \"field\": \"value\" }"
            aria-label="Payload input OpenFuse dalam JSON"
            className="w-full resize-y rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 font-mono text-[10px] text-slate-700 outline-none focus:border-red-500 focus:ring-2 focus:ring-red-500/10" />
          <div className="flex items-center justify-between gap-2">
            <span className="text-[9px] text-slate-400">Maksimum 16 KB · sesi aktif saja</span>
            <button type="submit" disabled={submitting || polling || !payload.trim()}
              className="inline-flex items-center gap-1.5 rounded-lg bg-red-600 px-3 py-2 text-[10px] font-bold text-white disabled:opacity-50">
              {submitting ? <RefreshCw className="h-3 w-3 animate-spin" /> : <Send className="h-3 w-3" />}
              {submitting ? 'Mengirim…' : 'Kirim input'}
            </button>
          </div>
        </form>
      ) : (
        <p className="text-[10px] text-slate-500">Human Takeover hanya tersedia untuk sesi browser aktif.</p>
      )}
      {command && (
        <div className="rounded-lg border border-slate-100 bg-slate-50 p-2 space-y-1">
          <div className="flex items-center justify-between gap-2">
            <span className="text-[10px] font-semibold text-slate-700">{statusCopy[command.status] || command.status}</span>
            <button type="button" onClick={() => void refreshCommand(command.command_id)}
              disabled={polling} className="text-[9px] font-semibold text-red-600 disabled:opacity-50">Perbarui</button>
          </div>
          <p className="text-[9px] text-slate-400 break-all">ID: {command.command_id}</p>
          {command.error_code && <p className="text-[10px] text-rose-700">{command.error_code}</p>}
        </div>
      )}
      {error && (
        <div className="flex items-start gap-1.5 text-[10px] text-rose-700">
          <AlertCircle className="h-3 w-3 mt-0.5 shrink-0" /><span>{error}</span>
        </div>
      )}
    </section>
  );
}
