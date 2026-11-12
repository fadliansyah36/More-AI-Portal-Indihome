'use client';

import React, { useState } from 'react';
import { Bot, Laptop, Sparkles, MessageSquare, Search, ArrowRight } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';

interface OnboardingScreenViewProps {
  onNavigate: (tab: NavigationTab) => void;
}

export const OnboardingScreenView: React.FC<OnboardingScreenViewProps> = ({ onNavigate }) => {
  const [activeSlide, setActiveSlide] = useState(0);

  const slides = [
    {
      title: 'Satu Platform untuk Semua Kebutuhan AI',
      desc: 'Bekerja, belajar, berkarya dengan mudah menggunakan teknologi AI mutakhir.',
      role: 'Pelajar & Mahasiswa',
      color: 'from-red-500 to-rose-600',
    },
    {
      title: 'Koneksi Super Cepat & Kuota AI Free',
      desc: 'Benefit AI sponsor hanya tersedia setelah jaringan partner diverifikasi dan entitlement aktif dikonfirmasi backend.',
      role: 'Pengguna Partner Network',
      color: 'from-rose-600 to-amber-600',
    },
    {
      title: 'Tim AI Agent Spesialis Bekerja Mandiri',
      desc: 'Delegasikan riset pasar, strategi marketing, penulisan copy, dan analisis data.',
      role: 'Profesional & Bisnis',
      color: 'from-amber-600 to-red-600',
    },
  ];

  return (
    <div className="min-h-[680px] flex flex-col justify-between py-6 px-4 bg-white rounded-3xl text-center animate-fadeIn">
      {/* Top Indicator */}
      <div className="flex items-center justify-between text-xs font-semibold text-slate-400 pt-2 px-2">
        <span className="text-red-600 font-bold">MoreAI Onboarding</span>
        <button onClick={() => onNavigate('login')} className="hover:text-slate-800">
          Lewati
        </button>
      </div>

      {/* Main Illustration Area: Young Creator with Laptop & floating icons */}
      <div className="my-auto py-4 flex flex-col items-center">
        <div className="relative w-64 h-64 flex items-center justify-center">
          {/* Circular glow backdrop */}
          <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-rose-100 to-red-100/70 scale-90" />

          {/* Central Stylized Avatar Container */}
          <div className="relative z-10 w-44 h-44 rounded-3xl bg-gradient-to-tr from-red-600 to-rose-500 p-1 shadow-xl flex items-center justify-center">
            <div className="w-full h-full rounded-[22px] bg-white flex flex-col items-center justify-center p-3 text-slate-800">
              <div className="w-16 h-16 rounded-2xl bg-red-50 text-red-600 flex items-center justify-center mb-1">
                <Laptop className="w-8 h-8" />
              </div>
              <span className="text-xs font-black text-slate-900 leading-tight">Pengguna MoreAI</span>
              <span className="text-[10px] text-red-600 font-bold">{slides[activeSlide].role}</span>
            </div>
          </div>

          {/* Floating AI Icons (matching Sheet 6 Screen 2) */}
          <div className="absolute top-2 left-4 p-2.5 rounded-2xl bg-white shadow-md border border-slate-100 text-blue-500 animate-bounce">
            <MessageSquare className="w-5 h-5" />
          </div>
          <div className="absolute top-4 right-4 p-2.5 rounded-2xl bg-white shadow-md border border-slate-100 text-amber-500 animate-pulse">
            <Sparkles className="w-5 h-5" />
          </div>
          <div className="absolute bottom-4 left-6 p-2.5 rounded-2xl bg-white shadow-md border border-slate-100 text-emerald-500">
            <Search className="w-5 h-5" />
          </div>
          <div className="absolute bottom-6 right-6 p-2.5 rounded-2xl bg-white shadow-md border border-slate-100 text-purple-500">
            <Bot className="w-5 h-5" />
          </div>
        </div>

        {/* Text Content */}
        <div className="mt-6 space-y-2 max-w-xs mx-auto">
          <h2 className="text-lg font-black text-slate-900 tracking-tight leading-snug">
            {slides[activeSlide].title}
          </h2>
          <p className="text-xs text-slate-500 font-medium leading-relaxed">
            {slides[activeSlide].desc}
          </p>
        </div>

        {/* 3 Pagination Dots */}
        <div className="flex items-center justify-center gap-1.5 mt-5">
          {slides.map((_, idx) => (
            <button
              key={idx}
              onClick={() => setActiveSlide(idx)}
              className={`h-1.5 rounded-full transition-all ${
                activeSlide === idx ? 'w-6 bg-red-600' : 'w-1.5 bg-slate-200'
              }`}
            />
          ))}
        </div>
      </div>

      {/* Buttons */}
      <div className="space-y-2 pb-2">
        {activeSlide < slides.length - 1 ? (
          <button
            onClick={() => setActiveSlide(activeSlide + 1)}
            className="w-full py-3.5 rounded-2xl bg-red-600 hover:bg-red-700 active:scale-95 text-white text-xs sm:text-sm font-bold transition shadow-xs flex items-center justify-center gap-1.5"
          >
            <span>Lanjutkan</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        ) : (
          <button
            onClick={() => onNavigate('login')}
            className="w-full py-3.5 rounded-2xl bg-red-600 hover:bg-red-700 active:scale-95 text-white text-xs sm:text-sm font-bold transition shadow-xs flex items-center justify-center gap-1.5"
          >
            <span>Mulai Sekarang</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        )}

        <button
          onClick={() => onNavigate('login')}
          className="w-full py-2.5 text-xs font-semibold text-slate-400 hover:text-slate-600"
        >
          Lewati
        </button>
      </div>
    </div>
  );
};
