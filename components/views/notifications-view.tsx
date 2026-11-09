'use client';

import React, { useState } from 'react';
import { ArrowLeft, Gift, Wifi, Sparkles, CheckCheck, Clock } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';

interface NotificationsViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

export const NotificationsView: React.FC<NotificationsViewProps> = ({
  onBack,
  onNavigateTab,
}) => {
  const { showToast } = useToast();
  const [filter, setFilter] = useState<'semua' | 'promo'>('semua');

  const notifications = [
    {
      id: 'notif-1',
      title: 'Promo AI Credit Spesial',
      desc: 'Dapatkan 2x poin credit hari ini saat terhubung ke Wi-Fi IndiHome di CoffeeHouse Semarang.',
      time: '10 menit lalu',
      type: 'promo',
      icon: Gift,
      color: 'bg-red-50 text-red-600',
      action: () => onNavigateTab('benefits'),
    },
    {
      id: 'notif-2',
      title: 'Update Layanan Wi-Fi',
      desc: 'Peningkatan kecepatan jaringan fiber optik 100 Mbps telah aktif di lokasi Anda.',
      time: '2 jam lalu',
      type: 'system',
      icon: Wifi,
      color: 'bg-emerald-50 text-emerald-600',
      action: () => onNavigateTab('wifi'),
    },
    {
      id: 'notif-3',
      title: 'Tips Produktivitas AI',
      desc: 'Gunakan Marketing Agent untuk menyusun 30 caption Instagram otomatis dalam 1 klik.',
      time: '1 hari lalu',
      type: 'tips',
      icon: Sparkles,
      color: 'bg-blue-50 text-blue-600',
      action: () => onNavigateTab('agents'),
    },
  ];

  const filtered = notifications.filter((n) =>
    filter === 'semua' ? true : n.type === 'promo'
  );

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <button
          onClick={onBack}
          className="p-1 rounded-lg text-slate-400 hover:text-slate-700"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-base font-bold text-slate-900 leading-tight">Notifikasi</h1>
        <button
          onClick={() => showToast('Semua notifikasi telah ditandai dibaca.', 'success')}
          className="text-xs text-red-600 font-semibold"
        >
          Tandai Dibaca
        </button>
      </div>

      {/* Tabs (Semua | Promo) Sheet 3 Screen 12 */}
      <div className="flex items-center gap-1 p-1 bg-white rounded-2xl border border-slate-200 shadow-2xs">
        <button
          onClick={() => setFilter('semua')}
          className={`flex-1 py-1.5 text-xs font-semibold rounded-xl transition ${
            filter === 'semua' ? 'bg-red-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          Semua
        </button>
        <button
          onClick={() => setFilter('promo')}
          className={`flex-1 py-1.5 text-xs font-semibold rounded-xl transition ${
            filter === 'promo' ? 'bg-red-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          Promo
        </button>
      </div>

      {/* List */}
      <div className="space-y-2.5">
        {filtered.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.id}
              onClick={item.action}
              className="cursor-pointer p-3.5 rounded-2xl bg-white border border-slate-100 hover:border-red-200 shadow-2xs hover:shadow-xs transition flex items-start gap-3.5 group"
            >
              <div
                className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 shadow-2xs group-hover:scale-105 transition-transform ${item.color}`}
              >
                <Icon className="w-5 h-5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-slate-900 group-hover:text-red-600 transition truncate">
                    {item.title}
                  </h3>
                  <span className="text-[10px] text-slate-400 shrink-0 ml-1">{item.time}</span>
                </div>
                <p className="text-[11px] text-slate-500 mt-1 line-clamp-2 leading-relaxed">
                  {item.desc}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
