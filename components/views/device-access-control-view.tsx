'use client';

import React, { useState } from 'react';
import { ArrowLeft, Shield, Smartphone, Laptop, Tv, Cpu, Pause, Play, Sliders, CheckCircle2 } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';

interface DeviceAccessControlViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

export const DeviceAccessControlView: React.FC<DeviceAccessControlViewProps> = ({
  onBack,
  onNavigateTab,
}) => {
  const { showToast } = useToast();

  const [devices, setDevices] = useState<Array<{ id: string; name: string; owner: string; type: string; priority: string; bandwidthLimit: string; status: string; parentalFilter: boolean }>>([]);

  const togglePause = (name: string, id: string) => {
    setDevices((prev) =>
      prev.map((d) =>
        d.id === id ? { ...d, status: d.status === 'active' ? 'paused' : 'active' } : d
      )
    );
    showToast(`Status akses internet untuk ${name} berhasil diubah.`, 'info');
  };

  const toggleParental = (name: string, id: string) => {
    setDevices((prev) =>
      prev.map((d) =>
        d.id === id ? { ...d, parentalFilter: !d.parentalFilter } : d
      )
    );
    showToast(`Safe Browsing & Filter Konten untuk ${name} diperbarui.`, 'success');
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
            Sheet 5 Screen 8
          </span>
          <h1 className="text-sm sm:text-base font-bold text-slate-900 leading-tight">
            Kontrol Akses &amp; Bandwidth
          </h1>
        </div>
        <div className="w-5" />
      </div>

      {/* Info Banner */}
      <div className="p-4 rounded-3xl bg-slate-900 text-white flex items-center justify-between shadow-xs">
        <div>
          <span className="text-[10px] uppercase font-bold text-slate-400">Router Firewall &amp; QoS</span>
          <h2 className="text-sm font-bold text-white mt-0.5">Prioritas Bandwidth MoreAI</h2>
          <p className="text-[11px] text-slate-300 mt-0.5">Kelola kuota perangkat, proteksi anak, &amp; jeda koneksi</p>
        </div>
        <div className="w-10 h-10 rounded-2xl bg-white/10 flex items-center justify-center text-emerald-400">
          <Sliders className="w-5 h-5" />
        </div>
      </div>

      {/* Device Cards */}
      <div className="space-y-3">
        {devices.length === 0 && (
          <div className="rounded-3xl border border-slate-200 bg-white p-5 text-center text-xs text-slate-500">
            Data perangkat belum tersedia dari integrasi gateway/partner. Kontrol jeda akses, bandwidth, dan filter konten dinonaktifkan sampai perangkat nyata dapat dibaca dan diotorisasi oleh backend.
          </div>
        )}
        {devices.map((dev) => (
          <div
            key={dev.id}
            className="p-4 rounded-3xl bg-white border border-slate-100 shadow-xs space-y-3 text-xs"
          >
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-bold text-slate-900 text-xs sm:text-sm">{dev.name}</h3>
                  <span
                    className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${
                      dev.status === 'active'
                        ? 'bg-emerald-50 text-emerald-600 border border-emerald-200'
                        : 'bg-amber-50 text-amber-600 border border-amber-200'
                    }`}
                  >
                    {dev.status === 'active' ? 'Online' : 'Dijeda'}
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 mt-0.5">{dev.owner}</p>
              </div>

              <button
                onClick={() => togglePause(dev.name, dev.id)}
                className={`p-2 rounded-xl transition font-bold flex items-center gap-1 ${
                  dev.status === 'active'
                    ? 'bg-red-50 text-red-600 hover:bg-red-100'
                    : 'bg-emerald-50 text-emerald-600 hover:bg-emerald-100'
                }`}
                title={dev.status === 'active' ? 'Jeda Akses Internet' : 'Lanjutkan Akses'}
              >
                {dev.status === 'active' ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 fill-current" />}
              </button>
            </div>

            <div className="p-2.5 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-between text-[11px]">
              <div>
                <span className="text-slate-400 block text-[9px] uppercase font-bold">Batas Bandwidth</span>
                <span className="font-bold text-slate-800">{dev.bandwidthLimit}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[9px] uppercase font-bold">Tingkat Prioritas</span>
                <span className="font-bold text-red-600">{dev.priority}</span>
              </div>
            </div>

            <div className="flex items-center justify-between pt-1">
              <span className="text-slate-600 text-[11px]">Filter Konten / Safe Browsing:</span>
              <button
                onClick={() => toggleParental(dev.name, dev.id)}
                className={`text-[10px] font-bold px-2.5 py-1 rounded-xl transition ${
                  dev.parentalFilter
                    ? 'bg-emerald-600 text-white'
                    : 'bg-slate-200 text-slate-600 hover:bg-slate-300'
                }`}
              >
                {dev.parentalFilter ? 'Aktif (Proteksi Anak)' : 'Nonaktif'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
