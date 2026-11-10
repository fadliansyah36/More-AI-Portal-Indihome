'use client';

import React, { useState } from 'react';
import { Bot, Sparkles, Wifi, Shield, X, ArrowRight, Check } from 'lucide-react';
import { MoreAiLogo, GlobalPartnerLogo } from '@/components/branding/logos';

interface OnboardingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onStart: () => void;
}

export const OnboardingModal: React.FC<OnboardingModalProps> = ({
  isOpen,
  onClose,
  onStart,
}) => {
  const [slide, setSlide] = useState(0);

  if (!isOpen) return null;

  const slides = [
    {
      title: 'AI untuk Semua',
      subtitle: 'Lebih Dekat, Lebih Produktif',
      desc: 'Platform kecerdasan buatan terpadu yang membantu riset, penulisan konten, desain visual, coding, dan otomasi dokumen Anda.',
      badge: 'Solusi Produktivitas Nasional',
    },
    {
      title: 'Ekosistem Global Partner ISP & Network',
      subtitle: 'Koneksi Super Cepat & Kuota AI Free',
      desc: 'Nikmati bonus 100.000 Poin AI Credit setiap bulan saat terhubung ke jaringan Wi-Fi Global Partner ISP di rumah maupun venue publik.',
      badge: 'Koneksi Berkecepatan Tinggi',
    },
    {
      title: 'Tim AI Agent Spesialis',
      subtitle: 'Bekerja Bersama Agent Mandiri',
      desc: 'Gunakan Research Agent, Marketing Agent, Writing Agent, Design Agent, dan Data Analyst dalam satu workspace kolaboratif.',
      badge: 'Multi-Agent Autonomous Engine',
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-fadeIn">
      <div className="w-full max-w-sm rounded-3xl bg-white p-6 shadow-2xl border border-slate-100 text-center relative overflow-hidden">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-400 hover:text-slate-600 transition"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Brand Logos Header */}
        <div className="flex items-center justify-center gap-3 pt-2 pb-4">
          <MoreAiLogo />
          <span className="text-slate-300">|</span>
          <GlobalPartnerLogo />
        </div>

        {/* Illustration Avatar Circle */}
        <div className="w-24 h-24 rounded-3xl bg-gradient-to-tr from-red-600 via-rose-500 to-amber-500 p-1 mx-auto shadow-md">
          <div className="w-full h-full rounded-[22px] bg-white flex items-center justify-center">
            {slide === 0 && <Bot className="w-12 h-12 text-red-600 animate-bounce" />}
            {slide === 1 && <Wifi className="w-12 h-12 text-red-600 animate-pulse" />}
            {slide === 2 && <Sparkles className="w-12 h-12 text-amber-500 animate-spin" />}
          </div>
        </div>

        {/* Content Slides */}
        <div className="mt-4 space-y-1.5 min-h-[140px]">
          <span className="text-[10px] font-bold text-red-600 bg-red-50 px-2.5 py-0.5 rounded-full border border-red-200 uppercase tracking-wide">
            {slides[slide].badge}
          </span>
          <h2 className="text-lg font-black text-slate-900 tracking-tight leading-tight">
            {slides[slide].title}
          </h2>
          <h3 className="text-xs font-bold text-slate-700">
            {slides[slide].subtitle}
          </h3>
          <p className="text-xs text-slate-500 leading-relaxed pt-1 max-w-xs mx-auto">
            {slides[slide].desc}
          </p>
        </div>

        {/* Carousel Dots */}
        <div className="flex items-center justify-center gap-1.5 my-3">
          {slides.map((_, idx) => (
            <button
              key={idx}
              onClick={() => setSlide(idx)}
              className={`h-1.5 rounded-full transition-all ${
                slide === idx ? 'w-6 bg-red-600' : 'w-1.5 bg-slate-200'
              }`}
            />
          ))}
        </div>

        {/* Action Buttons */}
        <div className="space-y-2 pt-1">
          {slide < slides.length - 1 ? (
            <button
              onClick={() => setSlide(slide + 1)}
              className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition shadow-xs flex items-center justify-center gap-1.5 active:scale-98"
            >
              <span>Lanjutkan</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={() => {
                onClose();
                onStart();
              }}
              className="w-full py-3 rounded-2xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition shadow-xs flex items-center justify-center gap-1.5 active:scale-98"
            >
              <span>Mulai Sekarang</span>
              <Check className="w-4 h-4" />
            </button>
          )}

          <button
            onClick={onClose}
            className="w-full py-2 text-slate-400 hover:text-slate-600 text-xs font-semibold"
          >
            Lewati Onboarding
          </button>
        </div>
      </div>
    </div>
  );
};
