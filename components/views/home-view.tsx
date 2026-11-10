'use client';

import React, { useState } from 'react';
import {
  MessageSquare,
  Search,
  Sparkles,
  FileSpreadsheet,
  Code2,
  ArrowRight,
  Wifi,
  ChevronRight,
  Bot,
  Zap,
  Gift,
  Clock,
  CheckCircle2,
  Send,
  Layers,
} from 'lucide-react';
import { NavigationTab } from '@/types/moreai';

interface HomeViewProps {
  onNavigate: (tab: NavigationTab) => void;
  onStartPrompt: (promptText: string) => void;
  userName?: string;
  avatarUrl?: string;
}

export const HomeView: React.FC<HomeViewProps> = ({
  onNavigate,
  onStartPrompt,
  userName = 'Andi Pratama',
}) => {
  const [promptInput, setPromptInput] = useState('');

  const handleSendPrompt = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!promptInput.trim()) return;
    onStartPrompt(promptInput.trim());
    setPromptInput('');
  };

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Top Greeting Section */}
      <div className="bg-gradient-to-b from-white to-slate-50/60 p-4 rounded-3xl border border-slate-100 shadow-xs">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-500">
              <span>Selamat Pagi,</span>
            </div>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-1.5">
              <span>{userName}</span>
              <span className="text-xl">👋</span>
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onNavigate('wifi')}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-medium hover:bg-emerald-100 transition"
              title="Status Koneksi Wi-Fi Global Partner ISP"
            >
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>Partner ISP 100M</span>
            </button>
          </div>
        </div>

        <p className="mt-1 text-xs text-slate-600 font-medium">
          Apa yang ingin kamu kerjakan hari ini?
        </p>

        {/* Big Search / Prompt Box */}
        <form onSubmit={handleSendPrompt} className="mt-3 relative">
          <textarea
            value={promptInput}
            onChange={(e) => setPromptInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendPrompt();
              }
            }}
            placeholder="Jelaskan pekerjaan yang ingin kamu selesaikan..."
            rows={2}
            className="w-full text-xs sm:text-sm rounded-2xl bg-white border border-slate-200 pl-3.5 pr-12 py-3 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500/30 focus:border-red-500 transition shadow-xs resize-none"
          />
          <button
            type="submit"
            disabled={!promptInput.trim()}
            className="absolute right-2.5 bottom-3 w-8 h-8 rounded-xl bg-red-600 hover:bg-red-700 disabled:opacity-40 text-white flex items-center justify-center transition shadow-xs active:scale-95"
            title="Kirim ke Chat AI"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>

        {/* 5 Quick Action Pill Buttons from the Reference Image */}
        <div className="grid grid-cols-5 gap-1.5 sm:gap-2 mt-3.5 pt-1">
          <button
            onClick={() => onNavigate('chat')}
            className="flex flex-col items-center justify-center p-2 rounded-2xl bg-slate-50 hover:bg-red-50/70 border border-slate-100 hover:border-red-200 group transition active:scale-95"
          >
            <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 group-hover:bg-red-600 group-hover:text-white flex items-center justify-center transition shadow-2xs">
              <MessageSquare className="w-4 h-4" />
            </div>
            <span className="mt-1.5 text-[11px] font-semibold text-slate-700 group-hover:text-red-600">
              Chat
            </span>
          </button>

          <button
            onClick={() => onNavigate('research')}
            className="flex flex-col items-center justify-center p-2 rounded-2xl bg-slate-50 hover:bg-red-50/70 border border-slate-100 hover:border-red-200 group transition active:scale-95"
          >
            <div className="w-9 h-9 rounded-xl bg-indigo-50 text-indigo-600 group-hover:bg-red-600 group-hover:text-white flex items-center justify-center transition shadow-2xs">
              <Search className="w-4 h-4" />
            </div>
            <span className="mt-1.5 text-[11px] font-semibold text-slate-700 group-hover:text-red-600">
              Research
            </span>
          </button>

          <button
            onClick={() => onNavigate('create')}
            className="flex flex-col items-center justify-center p-2 rounded-2xl bg-slate-50 hover:bg-red-50/70 border border-slate-100 hover:border-red-200 group transition active:scale-95"
          >
            <div className="w-9 h-9 rounded-xl bg-amber-50 text-amber-600 group-hover:bg-red-600 group-hover:text-white flex items-center justify-center transition shadow-2xs">
              <Sparkles className="w-4 h-4" />
            </div>
            <span className="mt-1.5 text-[11px] font-semibold text-slate-700 group-hover:text-red-600">
              Create
            </span>
          </button>

          <button
            onClick={() => onNavigate('analyse')}
            className="flex flex-col items-center justify-center p-2 rounded-2xl bg-slate-50 hover:bg-red-50/70 border border-slate-100 hover:border-red-200 group transition active:scale-95"
          >
            <div className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-600 group-hover:bg-red-600 group-hover:text-white flex items-center justify-center transition shadow-2xs">
              <FileSpreadsheet className="w-4 h-4" />
            </div>
            <span className="mt-1.5 text-[11px] font-semibold text-slate-700 group-hover:text-red-600">
              Analyse
            </span>
          </button>

          <button
            onClick={() => onNavigate('code')}
            className="flex flex-col items-center justify-center p-2 rounded-2xl bg-slate-50 hover:bg-red-50/70 border border-slate-100 hover:border-red-200 group transition active:scale-95"
          >
            <div className="w-9 h-9 rounded-xl bg-slate-100 text-slate-700 group-hover:bg-red-600 group-hover:text-white flex items-center justify-center transition shadow-2xs">
              <Code2 className="w-4 h-4" />
            </div>
            <span className="mt-1.5 text-[11px] font-semibold text-slate-700 group-hover:text-red-600">
              Code
            </span>
          </button>
        </div>
      </div>

      {/* Featured Banner: AI Credit Free dari Global Partner ISP */}
      <div
        onClick={() => onNavigate('benefits')}
        className="cursor-pointer relative overflow-hidden rounded-3xl bg-gradient-to-r from-red-600 via-rose-600 to-red-700 p-4 text-white shadow-md hover:shadow-lg transition group active:scale-[0.99]"
      >
        <div className="relative z-10 flex items-center justify-between">
          <div className="max-w-[70%]">
            <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-white/20 backdrop-blur-xs text-[10px] font-medium tracking-wide uppercase text-white mb-1.5">
              <Gift className="w-3 h-3 text-amber-300" />
              <span>Benefit Global Partner</span>
            </div>
            <h3 className="text-sm sm:text-base font-bold leading-tight">
              AI Credit Free dari Partner ISP
            </h3>
            <p className="mt-1 text-xs text-red-100 leading-snug">
              Nikmati akses AI lebih luas tanpa batas dengan koneksi Wi-Fi Global Partner ISP/Network.
            </p>
            <div className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white text-red-600 font-bold text-xs group-hover:bg-red-50 transition shadow-xs">
              <span>Cek Benefit</span>
              <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </div>
          </div>

          {/* Decorative graphic illustration / 3D badge mockup */}
          <div className="w-20 h-20 sm:w-24 sm:h-24 relative flex items-center justify-center">
            <div className="absolute inset-0 rounded-full bg-white/10 blur-md animate-pulse" />
            <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-white/15 border border-white/30 backdrop-blur-sm flex flex-col items-center justify-center p-2 text-center shadow-inner">
              <span className="text-[10px] font-bold text-amber-300 uppercase">Quota</span>
              <span className="text-base sm:text-lg font-black text-white leading-none">100K</span>
              <span className="text-[9px] text-white/80 font-medium mt-0.5">Poin AI</span>
            </div>
          </div>
        </div>

        {/* Ambient background circles */}
        <div className="absolute -right-8 -bottom-8 w-36 h-36 rounded-full bg-white/5 pointer-events-none" />
        <div className="absolute -left-8 -top-8 w-24 h-24 rounded-full bg-black/10 pointer-events-none" />
      </div>

      {/* Proyek Terbaru (Recent Tasks) from the Reference */}
      <div className="bg-white rounded-3xl p-4 border border-slate-100 shadow-xs">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
            <Clock className="w-4 h-4 text-slate-500" />
            <span>Proyek Terbaru</span>
          </h2>
          <button
            onClick={() => onNavigate('tasks')}
            className="text-xs font-semibold text-red-600 hover:text-red-700 flex items-center gap-0.5"
          >
            <span>Lihat Semua</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Task Card: Strategi Marketing Coffee Shop */}
        <div
          onClick={() => onNavigate('tasks')}
          className="cursor-pointer p-3.5 rounded-2xl bg-slate-50 hover:bg-slate-100/80 border border-slate-200/80 transition flex items-center gap-3 group"
        >
          <div className="w-11 h-11 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-600 flex items-center justify-center shrink-0">
            <Bot className="w-6 h-6" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-900 truncate group-hover:text-red-600 transition">
                Strategi Marketing Coffee Shop
              </h3>
              <span className="text-[10px] font-semibold text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
                Dalam Proses
              </span>
            </div>
            <div className="mt-1 flex items-center justify-between text-[11px] text-slate-500">
              <span>4 dari 6 langkah</span>
              <span className="font-semibold text-slate-700">67%</span>
            </div>
            <div className="mt-1.5 w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-gradient-to-r from-amber-500 to-red-500 h-1.5 rounded-full transition-all duration-500"
                style={{ width: '67%' }}
              />
            </div>
          </div>
          <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-slate-700 group-hover:translate-x-0.5 transition" />
        </div>
      </div>

      {/* Grid of Key Platforms & Portals (Complete ecosystem showcase) */}
      <div className="grid grid-cols-2 gap-2.5">
        <button
          onClick={() => onNavigate('agents')}
          className="p-3.5 rounded-2xl bg-white border border-slate-100 hover:border-red-200 text-left transition shadow-xs group"
        >
          <div className="w-8 h-8 rounded-xl bg-rose-50 text-red-600 flex items-center justify-center mb-2 group-hover:scale-105 transition-transform">
            <Layers className="w-4 h-4" />
          </div>
          <h4 className="text-xs font-bold text-slate-900 group-hover:text-red-600 transition">
            AI Agent Studio
          </h4>
          <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-2">
            5 Agent spesialis: Research, Marketing, Writer, Designer & Analyst.
          </p>
        </button>

        <button
          onClick={() => onNavigate('wifi')}
          className="p-3.5 rounded-2xl bg-white border border-slate-100 hover:border-red-200 text-left transition shadow-xs group"
        >
          <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-2 group-hover:scale-105 transition-transform">
            <Wifi className="w-4 h-4" />
          </div>
          <h4 className="text-xs font-bold text-slate-900 group-hover:text-emerald-600 transition">
            Wi-Fi Management
          </h4>
          <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-2">
            Kelola router Partner ISP 100 Mbps & 5 perangkat terhubung.
          </p>
        </button>

        <button
          onClick={() => onNavigate('captive')}
          className="p-3.5 rounded-2xl bg-white border border-slate-100 hover:border-red-200 text-left transition shadow-xs group"
        >
          <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center mb-2 group-hover:scale-105 transition-transform">
            <Zap className="w-4 h-4" />
          </div>
          <h4 className="text-xs font-bold text-slate-900 group-hover:text-blue-600 transition">
            Captive Portal
          </h4>
          <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-2">
            Simulasi login Wi-Fi venue & akses AI bersponsor (Sheet 3).
          </p>
        </button>

        <button
          onClick={() => onNavigate('partner')}
          className="p-3.5 rounded-2xl bg-white border border-slate-100 hover:border-red-200 text-left transition shadow-xs group"
        >
          <div className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center mb-2 group-hover:scale-105 transition-transform">
            <Bot className="w-4 h-4" />
          </div>
          <h4 className="text-xs font-bold text-slate-900 group-hover:text-purple-600 transition">
            Partner Portal B2B
          </h4>
          <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-2">
            Pendaftaran venue, QR akses, analitik & kelola paket (Sheet 4).
          </p>
        </button>
      </div>
    </div>
  );
};
