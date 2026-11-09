'use client';

import React, { useState } from 'react';
import { ArrowLeft, Key, Copy, Check, Webhook, RefreshCw, ShieldCheck } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';

interface PartnerApiSettingsViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

export const PartnerApiSettingsView: React.FC<PartnerApiSettingsViewProps> = ({
  onBack,
  onNavigateTab,
}) => {
  const { showToast } = useToast();
  const [apiKey, setApiKey] = useState('morkey_live_b2b_78a1f94c038e2197bbd9401');
  const [copiedKey, setCopiedKey] = useState(false);
  const [webhookUrl, setWebhookUrl] = useState('https://api.coffeehouse.id/v1/moreai/callback');

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(true);
    showToast('API Key telah disalin ke clipboard!', 'success');
    setTimeout(() => setCopiedKey(false), 2000);
  };

  const handleRegenerate = () => {
    const newKey = `morkey_live_b2b_${Math.random().toString(36).substring(2, 15)}${Math.random().toString(36).substring(2, 15)}`;
    setApiKey(newKey);
    showToast('API Key baru berhasil di-generate! Pastikan memperbarui gateway Anda.', 'success');
  };

  const handleSaveWebhook = () => {
    showToast('Webhook endpoint berhasil disimpan dan diverifikasi (Status: 200 OK).', 'success');
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
            Sheet 4 Screen 13
          </span>
          <h1 className="text-sm sm:text-base font-bold text-slate-900 leading-tight">
            API &amp; Webhook Gateway
          </h1>
        </div>
        <div className="w-5" />
      </div>

      {/* API Key Box */}
      <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-red-50 text-red-600 flex items-center justify-center">
              <Key className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-xs font-bold text-slate-900">Live API Key Mitra</h2>
              <p className="text-[10px] text-slate-400">Digunakan untuk otentikasi router &amp; captive portal</p>
            </div>
          </div>
          <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
            Aktif
          </span>
        </div>

        <div className="flex items-center gap-2 p-3 rounded-2xl bg-slate-50 border border-slate-200">
          <input
            type="text"
            readOnly
            value={apiKey}
            className="flex-1 bg-transparent font-mono text-xs text-slate-800 focus:outline-none"
          />
          <button
            onClick={() => copyToClipboard(apiKey)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition"
            title="Salin Kunci"
          >
            {copiedKey ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
          </button>
        </div>

        <button
          onClick={handleRegenerate}
          className="text-[11px] font-semibold text-red-600 hover:text-red-700 flex items-center gap-1.5 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Regenerate API Key Baru</span>
        </button>
      </div>

      {/* Webhook Endpoint */}
      <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-xs space-y-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
            <Webhook className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-xs font-bold text-slate-900">Webhook URL Event</h2>
            <p className="text-[10px] text-slate-400">Menerima payload realtime event sesi &amp; kuota tamu</p>
          </div>
        </div>

        <div>
          <label className="text-[11px] font-bold text-slate-700 block mb-1">
            Callback Endpoint
          </label>
          <input
            type="url"
            value={webhookUrl}
            onChange={(e) => setWebhookUrl(e.target.value)}
            className="w-full p-3 rounded-xl border border-slate-200 bg-slate-50 font-mono text-xs text-slate-800 focus:bg-white focus:outline-none"
          />
        </div>

        <div className="flex items-center justify-between text-xs text-slate-500 pt-1">
          <span className="flex items-center gap-1 text-emerald-600 font-semibold text-[11px]">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            Terverifikasi (200 OK • 42ms)
          </span>
          <button
            onClick={handleSaveWebhook}
            className="px-3.5 py-1.5 rounded-xl bg-slate-900 text-white font-bold text-xs hover:bg-slate-800 transition"
          >
            Uji &amp; Simpan
          </button>
        </div>
      </div>
    </div>
  );
};
