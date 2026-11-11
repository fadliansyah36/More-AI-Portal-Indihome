'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { ArrowLeft, RefreshCw } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { partnerApi, PartnerContext } from '@/lib/api/client';

interface PartnerLiveSessionsViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

type PartnerNetworkSession = {
  id: string;
  network_id: string;
  status: string;
  started_at: string;
  last_heartbeat_at: string | null;
  expires_at: string;
};

export const PartnerLiveSessionsView: React.FC<PartnerLiveSessionsViewProps> = ({
  onBack,
  onNavigateTab,
}) => {
  void onNavigateTab;
  const [activeSessions, setActiveSessions] = useState<PartnerNetworkSession[]>([]);
  const [partnerContext, setPartnerContext] = useState<PartnerContext | null>(null);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSessions = useCallback(async () => {
    try {
      const [context, sessions] = await Promise.all([
        partnerApi.context(),
        partnerApi.sessions(),
      ]);
      setPartnerContext(context);
      setActiveSessions(sessions as PartnerNetworkSession[]);
      setError(null);
    } catch (err) {
      setActiveSessions([]);
      setError(err instanceof Error ? err.message : 'Data sesi mitra tidak dapat dimuat.');
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void loadSessions();
  }, [loadSessions]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    void loadSessions();
  };

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <button onClick={onBack} className="p-1 rounded-lg text-slate-400 hover:text-slate-700">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="text-center">
          <span className="text-[10px] font-bold text-red-600 uppercase tracking-wider block">
            Partner Network
          </span>
          <h1 className="text-sm sm:text-base font-bold text-slate-900 leading-tight">
            Live Session Monitor
          </h1>
        </div>
        <button
          onClick={handleRefresh}
          className="p-1.5 rounded-lg text-slate-500 hover:text-red-600"
          title="Segarkan Data"
          disabled={isRefreshing}
        >
          <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-red-600' : ''}`} />
        </button>
      </div>

      <div className="p-5 rounded-3xl bg-slate-900 text-white shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-[10px] uppercase font-bold text-slate-400">
            {partnerContext?.tenant.display_name || 'Partner Workspace'}
          </span>
          <span className="text-xs text-emerald-400 font-bold bg-emerald-950/60 px-2.5 py-0.5 rounded-full border border-emerald-500/20">
            {loading ? 'Memuat' : error ? 'Tidak Tersedia' : 'API Terhubung'}
          </span>
        </div>
        <div className="grid grid-cols-3 gap-2 pt-1 text-center">
          <div className="p-2.5 rounded-2xl bg-white/5 border border-white/10">
            <span className="text-[10px] text-slate-400 block">Sesi Aktif</span>
            <span className="text-lg font-black text-white">{loading ? '—' : activeSessions.length}</span>
          </div>
          <div className="p-2.5 rounded-2xl bg-red-600/30 border border-red-500/30">
            <span className="text-[10px] text-red-200 block">Status Tenant</span>
            <span className="text-sm font-black text-white">{partnerContext?.tenant.status || '—'}</span>
          </div>
          <div className="p-2.5 rounded-2xl bg-white/5 border border-white/10">
            <span className="text-[10px] text-slate-400 block">Scope</span>
            <span className="text-sm font-black text-white">{partnerContext?.location_scope ? 'Lokasi' : 'Tenant'}</span>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-3xl p-4 sm:p-5 border border-slate-100 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            Daftar Sesi Jaringan Aktif ({activeSessions.length})
          </h2>
          <span className="text-[10px] text-slate-400 font-semibold">Data FastAPI</span>
        </div>
        {error && <p className="text-xs text-rose-600">{error}</p>}
        {loading && <p className="text-xs text-slate-500">Memuat sesi dari backend…</p>}
        {!loading && !error && activeSessions.length === 0 && (
          <p className="text-xs text-slate-500 p-3 rounded-xl bg-slate-50">
            Belum ada sesi jaringan aktif pada tenant/lokasi yang dapat diakses.
          </p>
        )}
        <div className="space-y-2.5">
          {activeSessions.map((session) => (
            <div key={session.id} className="p-3.5 rounded-2xl bg-slate-50 border border-slate-100 flex items-start justify-between gap-3 text-xs">
              <div className="min-w-0">
                <span className="font-bold text-slate-900 block">Sesi {session.id.slice(0, 8)}</span>
                <p className="text-[11px] text-slate-500 mt-0.5">Network: {session.network_id}</p>
                <p className="text-[10px] text-slate-400 mt-1">
                  Mulai: {new Date(session.started_at).toLocaleString('id-ID')}
                </p>
                <p className="text-[10px] text-slate-400">
                  Heartbeat: {session.last_heartbeat_at ? new Date(session.last_heartbeat_at).toLocaleString('id-ID') : 'Belum tersedia'}
                </p>
              </div>
              <div className="text-right shrink-0">
                <span className="text-[10px] font-bold text-emerald-600 block">{session.status}</span>
                <span className="text-[10px] text-slate-400 block mt-1">
                  Berakhir: {new Date(session.expires_at).toLocaleString('id-ID')}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
