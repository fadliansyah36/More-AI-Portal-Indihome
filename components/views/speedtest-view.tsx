'use client';

import React, { useState } from 'react';
import { ArrowLeft, Gauge, Wifi, Zap, Activity, Play, RefreshCw, CheckCircle2 } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';

interface SpeedtestViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

export const SpeedtestView: React.FC<SpeedtestViewProps> = ({
  onBack,
  onNavigateTab,
}) => {
  const { showToast } = useToast();
  const [isRunning, setIsRunning] = useState(false);
  const [downloadSpeed, setDownloadSpeed] = useState(104.2);
  const [uploadSpeed, setUploadSpeed] = useState(52.8);
  const [ping, setPing] = useState(9);
  const [jitter, setJitter] = useState(1.8);

  const runTest = () => {
    setIsRunning(true);
    setDownloadSpeed(0);
    setUploadSpeed(0);

    let progress = 0;
    const interval = setInterval(() => {
      progress += 10;
      setDownloadSpeed(Math.floor(Math.random() * 20 + 95));
      setUploadSpeed(Math.floor(Math.random() * 10 + 48));

      if (progress >= 100) {
        clearInterval(interval);
        setIsRunning(false);
        setDownloadSpeed(104.2);
        setUploadSpeed(52.8);
        setPing(8);
        setJitter(1.5);
        showToast('Speedtest selesai! Koneksi IndiHome Anda dalam kondisi Sempurna (104.2 Mbps).', 'success');
      }
    }, 200);
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
            <Wifi className="w-4 h-4 text-red-500" />
            IndiHome Fiber 100 Mbps
          </span>
          <span className="text-emerald-400 font-bold flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Sangat Baik
          </span>
        </div>

        {/* Speed Dial Circle */}
        <div className="relative w-44 h-44 mx-auto flex flex-col items-center justify-center rounded-full border-8 border-slate-800 bg-slate-950/80 shadow-inner">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
            {isRunning ? 'Menguji Kecepatan...' : 'Kecepatan Download'}
          </span>
          <span className="text-4xl font-black font-mono text-white tracking-tight my-1">
            {downloadSpeed}
          </span>
          <span className="text-xs font-bold text-red-500">Mbps (Simetris)</span>
        </div>

        {/* Metrics Row: Ping, Jitter, Upload */}
        <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800 text-center">
          <div className="p-2 rounded-xl bg-slate-800/60">
            <span className="text-[10px] text-slate-400 block">Ping Latency</span>
            <span className="font-mono font-bold text-sm text-emerald-400">{ping} ms</span>
          </div>
          <div className="p-2 rounded-xl bg-slate-800/60">
            <span className="text-[10px] text-slate-400 block">Jitter</span>
            <span className="font-mono font-bold text-sm text-slate-200">{jitter} ms</span>
          </div>
          <div className="p-2 rounded-xl bg-slate-800/60">
            <span className="text-[10px] text-slate-400 block">Upload Speed</span>
            <span className="font-mono font-bold text-sm text-blue-400">{uploadSpeed} Mbps</span>
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

      {/* Technical Diagnostics */}
      <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-xs space-y-3 text-xs">
        <h3 className="font-bold text-slate-900 uppercase tracking-wider text-xs">
          Diagnostik Perangkat &amp; Fiber
        </h3>

        <div className="space-y-2">
          <div className="flex justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-slate-500">Router ONT:</span>
            <span className="font-bold text-slate-800">ZTE F670L (Wi-Fi 6 Ready)</span>
          </div>
          <div className="flex justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-slate-500">IP Gateway:</span>
            <span className="font-mono font-bold text-slate-800">192.168.1.1</span>
          </div>
          <div className="flex justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-slate-500">Kualitas Sinyal Optik (Rx):</span>
            <span className="font-bold text-emerald-600">-18.4 dBm (Normal Optimal)</span>
          </div>
          <div className="flex justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-slate-500">Kesiapan AI Agent:</span>
            <span className="font-bold text-emerald-600">Ultra-Low Latency (Streaming Ready)</span>
          </div>
        </div>
      </div>
    </div>
  );
};
