'use client';

import React from 'react';
import { RefreshCw, Monitor, AlertCircle } from 'lucide-react';
import { useBrowserSessionPreview } from '@/hooks/use-browser-session-preview';

type Props = { sessionId: string; sessionStatus: string };

const statusLabels: Record<string, string> = {
  loading: 'Memulihkan status…',
  active: 'Aktif',
  close_requested: 'Menunggu penutupan',
  closed: 'Sudah ditutup',
  expired: 'Kedaluwarsa',
  unavailable: 'Status tidak tersedia',
};

export function BrowserSessionPreview({ sessionId, sessionStatus }: Props) {
  const { reconnectStatus, preview, refreshing, refresh, restore, renewSignedPreviewUrl } =
    useBrowserSessionPreview(sessionId);
  const effectiveStatus = reconnectStatus === 'loading' ? sessionStatus : reconnectStatus;
  const canRefresh = effectiveStatus === 'active' && !refreshing;

  return (
    <div className="mt-3 rounded-xl border border-slate-200 bg-white p-3 space-y-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <Monitor className="h-3.5 w-3.5 text-slate-500 shrink-0" />
          <span className="text-[10px] font-semibold text-slate-700">Preview Browser</span>
          <span className="text-[10px] text-slate-500">{statusLabels[effectiveStatus] || effectiveStatus}</span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button type="button" onClick={() => void restore()} className="text-[10px] font-semibold text-slate-500">
            Pulihkan
          </button>
          <button type="button" disabled={!canRefresh} onClick={() => void refresh()}
            className="inline-flex items-center gap-1 rounded-lg bg-red-600 px-2.5 py-1.5 text-[10px] font-bold text-white disabled:opacity-40">
            <RefreshCw className={`h-3 w-3 ${refreshing ? 'animate-spin' : ''}`} />
            {refreshing ? 'Memproses…' : 'Ambil screenshot'}
          </button>
        </div>
      </div>
      {preview.imageUrl ? (
        <img src={preview.imageUrl} alt="Preview layar sesi browser"
          onError={() => void renewSignedPreviewUrl()}
          className="block w-full rounded-lg border border-slate-200 bg-slate-50 object-contain max-h-[420px]" />
      ) : (
        <div className="flex min-h-20 items-center justify-center rounded-lg border border-dashed border-slate-200 bg-slate-50 px-3 py-5 text-center">
          <p className="text-[10px] text-slate-500">
            {preview.status === 'queued' || preview.status === 'processing'
              ? 'Permintaan screenshot tersimpan dan sedang diproses worker.'
              : preview.status === 'succeeded'
                ? 'Artifact screenshot tersedia; tautan preview perlu dipulihkan.'
                : effectiveStatus !== 'active'
                  ? 'Preview hanya tersedia selama sesi browser aktif.'
                  : 'Belum ada preview. Ambil screenshot untuk memperbarui tampilan.'}
          </p>
        </div>
      )}
      {preview.error && (
        <div className="flex items-start gap-1.5 text-[10px] text-rose-700">
          <AlertCircle className="h-3 w-3 mt-0.5 shrink-0" />
          <span>{preview.error}</span>
        </div>
      )}
      {preview.createdAt && (
        <p className="text-[9px] text-slate-400">Permintaan terakhir: {new Date(preview.createdAt).toLocaleString('id-ID')}</p>
      )}
    </div>
  );
}
