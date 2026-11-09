'use client';

import React, { useState } from 'react';
import { ArrowLeft, Users, Wifi, Sparkles, Smartphone, Laptop, RefreshCw, XCircle, ShieldCheck } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';

interface PartnerLiveSessionsViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

export const PartnerLiveSessionsView: React.FC<PartnerLiveSessionsViewProps> = ({
  onBack,
  onNavigateTab,
}) => {
  const { showToast } = useToast();
  const [isRefreshing, setIsRefreshing] = useState(false);

  const [activeSessions, setActiveSessions] = useState([
    {
      id: 'sess-1',
      device: 'iPhone 15 Pro Max',
      user: 'Budi S. (Tamu)',
      ip: '192.168.10.42',
      table: 'Meja 04',
      duration: '42 Menit',
      aiTool: 'Chat & Riset Pasar',
      bandwidth: '8.4 MB / 14.2 Mbps',
    },
    {
      id: 'sess-2',
      device: 'MacBook Air M2',
      user: 'Siti N. (Member)',
      ip: '192.168.10.55',
      table: 'Meja 08',
      duration: '1 Jam 15 Menit',
      aiTool: 'Generator Gambar AI',
      bandwidth: '24.1 MB / 22.8 Mbps',
    },
    {
      id: 'sess-3',
      device: 'Samsung Galaxy S24',
      user: 'Rian A. (Tamu)',
      ip: '192.168.10.61',
      table: 'Bar Area',
      duration: '18 Menit',
      aiTool: 'Ringkasan Dokumen PDF',
      bandwidth: '4.2 MB / 18.0 Mbps',
    },
    {
      id: 'sess-4',
      device: 'ASUS ZenBook',
      user: 'Dina K. (Member)',
      ip: '192.168.10.70',
      table: 'Meja 12',
      duration: '2 Jam 05 Menit',
      aiTool: 'Code Runner Python',
      bandwidth: '31.5 MB / 25.4 Mbps',
    },
  ]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      setIsRefreshing(false);
      showToast('Data pengunjung aktif diperbarui: 42 perangkat terhubung.', 'success');
    }, 700);
  };

  const handleDisconnect = (user: string, id: string) => {
    setActiveSessions((prev) => prev.filter((s) => s.id !== id));
    showToast(`Sesi perangkat ${user} telah diputuskan.`, 'info');
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
            Sheet 4 Screen 4
          </span>
          <h1 className="text-sm sm:text-base font-bold text-slate-900 leading-tight">
            Live Session Monitor
          </h1>
        </div>
        <button
          onClick={handleRefresh}
          className="p-1.5 rounded-lg text-slate-500 hover:text-red-600"
          title="Segarkan Data"
        >
          <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-red-600' : ''}`} />
        </button>
      </div>

      {/* Real-time KPI Card */}
      <div className="p-5 rounded-3xl bg-slate-900 text-white shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-[10px] uppercase font-bold text-slate-400">CoffeeHouse Semarang</span>
          <span className="flex items-center gap-1.5 text-xs text-emerald-400 font-bold bg-emerald-950/60 px-2.5 py-0.5 rounded-full border border-emerald-500/20">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Live Sync
          </span>
        </div>

        <div className="grid grid-cols-3 gap-2 pt-1 text-center">
          <div className="p-2.5 rounded-2xl bg-white/5 border border-white/10">
            <span className="text-[10px] text-slate-400 block">Total Hari Ini</span>
            <span className="text-lg font-black text-white">126</span>
          </div>
          <div className="p-2.5 rounded-2xl bg-red-600/30 border border-red-500/30">
            <span className="text-[10px] text-red-200 block">Aktif Sekarang</span>
            <span className="text-lg font-black text-white">42</span>
          </div>
          <div className="p-2.5 rounded-2xl bg-white/5 border border-white/10">
            <span className="text-[10px] text-slate-400 block">Run AI</span>
            <span className="text-lg font-black text-white">342</span>
          </div>
        </div>
      </div>

      {/* Active Guest List */}
      <div className="bg-white rounded-3xl p-4 sm:p-5 border border-slate-100 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            Daftar Sesi Pengunjung Aktif ({activeSessions.length})
          </h2>
          <span className="text-[10px] text-slate-400 font-semibold">Router Gateway: MikroTik 10G</span>
        </div>

        <div className="space-y-2.5">
          {activeSessions.map((sess) => (
            <div
              key={sess.id}
              className="p-3.5 rounded-2xl bg-slate-50 border border-slate-100 flex items-start justify-between gap-3 text-xs"
            >
              <div className="flex items-start gap-3 min-w-0">
                <div className="w-9 h-9 rounded-xl bg-white border border-slate-200 flex items-center justify-center shrink-0 text-red-600 shadow-2xs mt-0.5">
                  <Smartphone className="w-4 h-4" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="font-bold text-slate-900">{sess.user}</span>
                    <span className="text-[10px] bg-slate-200/80 text-slate-700 px-1.5 py-0.5 rounded">
                      {sess.table}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-0.5">{sess.device} · {sess.ip}</p>
                  <div className="flex items-center gap-2 text-[10px] text-slate-400 mt-1">
                    <span className="text-red-600 font-semibold flex items-center gap-1">
                      <Sparkles className="w-3 h-3" />
                      {sess.aiTool}
                    </span>
                    <span>•</span>
                    <span>{sess.duration}</span>
                  </div>
                </div>
              </div>

              <div className="text-right shrink-0">
                <span className="text-[10px] font-mono text-slate-500 block mb-1">
                  {sess.bandwidth}
                </span>
                <button
                  onClick={() => handleDisconnect(sess.user, sess.id)}
                  className="p-1 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition"
                  title="Putuskan Sesi"
                >
                  <XCircle className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
