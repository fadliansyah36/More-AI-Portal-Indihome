'use client';

import React, { useState } from 'react';
import { ArrowLeft, Wifi, Play, RefreshCw } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';
import { customerApi } from '@/lib/api/client';

interface SpeedtestViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

export const SpeedtestView: React.FC<SpeedtestViewProps> = ({ onBack }) => {
  const { showToast } = useToast();
  const [isRunning, setIsRunning] = useState(false);
  const [downloadSpeed, setDownloadSpeed] = useState<number | null>(null);
  const [uploadSpeed, setUploadSpeed] = useState<number | null>(null);
  const [ping, setPing] = useState<number | null>(null);
  const [jitter, setJitter] = useState<number | null>(null);
  const [testError, setTestError] = useState<string | null>(null);

  const runTest = async () => {
    setIsRunning(true);
    setTestError(null);
    setDownloadSpeed(null);
    setUploadSpeed(null);
    setPing(null);
    setJitter(null);
    try {
      const pingSamples: number[] = [];
      for (let index = 0; index < 5; index += 1) {
        const started = performance.now();
        await customerApi.networkSpeedtestPing();
        pingSamples.push(performance.now() - started);
      }
      const averagePing = pingSamples.reduce((sum, value) => sum + value, 0) / pingSamples.length;
      const averageJitter = pingSamples.slice(1).reduce((sum, value, index) => sum + Math.abs(value - pingSamples[index]), 0) / Math.max(1, pingSamples.length - 1);

      const downloadStarted = performance.now();
      const downloadResponse = await customerApi.networkSpeedtestDownload(4 * 1024 * 1024);
      const downloadBytes = await downloadResponse.arrayBuffer();
      const downloadElapsed = Math.max(1, performance.now() - downloadStarted);
      const measuredDownload = (downloadBytes.byteLength * 8) / downloadElapsed / 1000;

      const uploadBytes = new Uint8Array(4 * 1024 * 1024);
      for (let offset = 0; offset < uploadBytes.length; offset += 65536) {
        crypto.getRandomValues(uploadBytes.subarray(offset, Math.min(offset + 65536, uploadBytes.length)));
      }
      const uploadStarted = performance.now();
      const uploadResult = await customerApi.networkSpeedtestUpload(uploadBytes);
      const uploadElapsed = Math.max(1, performance.now() - uploadStarted);
      if (uploadResult.received_bytes !== uploadBytes.byteLength) {
        throw new Error('Server tidak menerima seluruh data pengujian upload.');
      }
      setPing(Number(averagePing.toFixed(1)));
      setJitter(Number(averageJitter.toFixed(1)));
      setDownloadSpeed(Number(measuredDownload.toFixed(2)));
      setUploadSpeed(Number(((uploadResult.received_bytes * 8) / uploadElapsed / 1000).toFixed(2)));
      showToast('Pengukuran jalur perangkat ke MoreAI API selesai.', 'success');
    } catch (cause) {
      setTestError(cause instanceof Error ? cause.message : 'Pengukuran jaringan gagal.');
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <button onClick={onBack} className="p-1 rounded-lg text-slate-400 hover:text-slate-700">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="text-center">
          <span className="text-[10px] font-bold text-red-600 uppercase tracking-wider block">
            Sheet 5 Screen 5
          </span>
          <h1 className="text-sm sm:text-base font-bold text-slate-900 leading-tight">
            Speedtest &amp; Status Jaringan
          </h1>
        </div>
        <div className="w-5" />
      </div>

      {/* Main Gauge Dial Card */}
      <div className="p-6 rounded-3xl bg-slate-900 text-white shadow-md text-center space-y-4 relative overflow-hidden">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span className="flex items-center gap-1.5">
            <Wifi className="w-4 h-4 text-blue-500" />
            Jalur perangkat ↔ MoreAI API
          </span>
          <span className="text-emerald-400 font-bold flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            {downloadSpeed === null ? 'Belum diuji' : 'Hasil pengukuran'}
          </span>
        </div>

        {/* Speed Dial Circle */}
        <div className="relative w-44 h-44 mx-auto flex flex-col items-center justify-center rounded-full border-8 border-slate-800 bg-slate-950/80 shadow-inner">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
            {isRunning ? 'Menguji Kecepatan...' : 'Kecepatan Download'}
          </span>
          <span className="text-4xl font-black font-mono text-white tracking-tight my-1">
            {downloadSpeed === null ? '—' : downloadSpeed}
          </span>
          <span className="text-xs font-bold text-red-500">Mbps · jalur API</span>
        </div>

        {/* Metrics Row: Ping, Jitter, Upload */}
        <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800 text-center">
          <div className="p-2 rounded-xl bg-slate-800/60">
            <span className="text-[10px] text-slate-400 block">Ping Latency</span>
            <span className="font-mono font-bold text-sm text-emerald-400">{ping === null ? '—' : ping + ' ms'}</span>
          </div>
          <div className="p-2 rounded-xl bg-slate-800/60">
            <span className="text-[10px] text-slate-400 block">Jitter</span>
            <span className="font-mono font-bold text-sm text-slate-200">{jitter === null ? '—' : jitter + ' ms'}</span>
          </div>
          <div className="p-2 rounded-xl bg-slate-800/60">
            <span className="text-[10px] text-slate-400 block">Upload Speed</span>
            <span className="font-mono font-bold text-sm text-blue-400">{uploadSpeed === null ? '—' : uploadSpeed + ' Mbps'}</span>
          </div>
        </div>

        <button
          onClick={runTest}
          disabled={isRunning}
          className="w-full py-3.5 rounded-2xl bg-red-600 hover:bg-red-700 active:scale-95 text-white font-bold text-xs transition shadow-xs flex items-center justify-center gap-2"
        >
          {isRunning ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Sedang Mengukur Jaringan...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" />
              <span>Mulai Uji Kecepatan</span>
            </>
          )}
        </button>
      </div>

      {testError && <div role="alert" className="rounded-2xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">{testError}</div>}
      <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-xs space-y-2 text-xs">
        <h3 className="font-bold text-slate-900 uppercase tracking-wider text-xs">Informasi Pengukuran</h3>
        <p className="text-slate-600">Pengujian mengukur round-trip latency, download, dan upload antara perangkat dan endpoint MoreAI API. Hasil ini bukan pembacaan ONT, optical Rx, SSID, atau gateway ISP.</p>
      </div>
    </div>
  );
};
