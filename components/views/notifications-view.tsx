'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { ArrowLeft, Gift, Wifi, Sparkles, CheckCheck, Bell, RefreshCw } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';
import { notificationApi, CustomerNotification } from '@/lib/api/client';

interface NotificationsViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

const relativeTime = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Waktu tidak tersedia';
  const minutes = Math.max(0, Math.floor((Date.now() - date.getTime()) / 60000));
  if (minutes < 1) return 'Baru saja';
  if (minutes < 60) return `${minutes} menit lalu`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} jam lalu`;
  const days = Math.floor(hours / 24);
  return `${days} hari lalu`;
};

const destinationFor = (item: CustomerNotification): NavigationTab | null => {
  const route = (item.action_url || '').toLowerCase();
  if (route.includes('benefit') || route.includes('wallet') || route.includes('credit')) return 'benefits';
  if (route.includes('wifi') || route.includes('network')) return 'wifi';
  if (route.includes('agent') || route.includes('workflow')) return 'agents';
  return null;
};

export const NotificationsView: React.FC<NotificationsViewProps> = ({ onBack, onNavigateTab }) => {
  const { showToast } = useToast();
  const [filter, setFilter] = useState<'semua' | 'promo'>('semua');
  const [items, setItems] = useState<CustomerNotification[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const result = await notificationApi.list(false, 100);
      setItems(result.items);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Notifikasi tidak dapat dimuat.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    void Promise.resolve().then(() => { if (active) void load(); });
    return () => { active = false; };
  }, [load]);

  const markAllRead = async () => {
    setBusy(true);
    try {
      await notificationApi.markAllRead();
      setItems((current) => current.map((item) => ({ ...item, read_at: item.read_at || new Date().toISOString() })));
      showToast('Notifikasi telah ditandai dibaca.', 'success');
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Gagal memperbarui notifikasi.', 'error');
    } finally {
      setBusy(false);
    }
  };

  const openNotification = async (item: CustomerNotification) => {
    if (!item.read_at) {
      try {
        await notificationApi.markRead(item.id);
        setItems((current) => current.map((entry) => entry.id === item.id ? { ...entry, read_at: new Date().toISOString() } : entry));
      } catch (err) {
        showToast(err instanceof Error ? err.message : 'Status notifikasi gagal diperbarui.', 'error');
        return;
      }
    }
    const target = destinationFor(item);
    if (target) onNavigateTab(target);
  };

  const filtered = items.filter((item) => filter === 'semua' || /promo|campaign|reward/i.test(item.notification_type));

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <button onClick={onBack} className="p-1 rounded-lg text-slate-400 hover:text-slate-700"><ArrowLeft className="w-5 h-5" /></button>
        <h1 className="text-base font-bold text-slate-900 leading-tight">Notifikasi</h1>
        <div className="flex items-center gap-2">
          <button onClick={() => { setLoading(true); setError(null); void load(); }} disabled={loading} className="p-1 text-slate-400 hover:text-slate-700" aria-label="Muat ulang"><RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /></button>
          <button onClick={() => void markAllRead()} disabled={busy || items.every((item) => item.read_at)} className="text-xs text-red-600 font-semibold disabled:opacity-40"><CheckCheck className="w-4 h-4 inline mr-1" />Baca semua</button>
        </div>
      </div>

      <div className="flex items-center gap-1 p-1 bg-white rounded-2xl border border-slate-200 shadow-2xs">
        <button onClick={() => setFilter('semua')} className={`flex-1 py-1.5 text-xs font-semibold rounded-xl transition ${filter === 'semua' ? 'bg-red-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'}`}>Semua</button>
        <button onClick={() => setFilter('promo')} className={`flex-1 py-1.5 text-xs font-semibold rounded-xl transition ${filter === 'promo' ? 'bg-red-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'}`}>Promo</button>
      </div>

      {error && <div className="p-3 rounded-xl border border-amber-200 bg-amber-50 text-xs text-amber-800"><p>{error}</p><button onClick={() => void load()} className="font-bold underline mt-1">Coba lagi</button></div>}
      {loading ? <div className="py-12 text-center text-xs text-slate-400">Memuat notifikasi akun…</div> :
        filtered.length === 0 ? <div className="py-12 text-center rounded-2xl bg-white border border-slate-100"><Bell className="w-7 h-7 mx-auto text-slate-300 mb-2" /><p className="text-xs text-slate-500">Belum ada notifikasi.</p></div> :
        <div className="space-y-2.5">
          {filtered.map((item) => {
            const promo = /promo|campaign|reward/i.test(item.notification_type);
            const network = /wifi|network|partner/i.test(item.notification_type);
            const Icon = promo ? Gift : network ? Wifi : Sparkles;
            const color = promo ? 'bg-red-50 text-red-600' : network ? 'bg-emerald-50 text-emerald-600' : 'bg-blue-50 text-blue-600';
            return (
              <button key={item.id} onClick={() => void openNotification(item)} className={`w-full text-left p-3.5 rounded-2xl bg-white border shadow-2xs hover:shadow-xs transition flex items-start gap-3.5 group ${item.read_at ? 'border-slate-100' : 'border-red-200'}`}>
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${color}`}><Icon className="w-5 h-5" /></div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2"><h3 className="text-xs font-bold text-slate-900 truncate">{item.title}</h3><span className="text-[10px] text-slate-400 shrink-0">{relativeTime(item.created_at)}</span></div>
                  <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">{item.body}</p>
                  {!item.read_at && <span className="inline-block mt-2 text-[10px] font-semibold text-red-600">Belum dibaca</span>}
                </div>
              </button>
            );
          })}
        </div>}
    </div>
  );
};
