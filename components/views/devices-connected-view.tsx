'use client';

import React, { useState } from 'react';
import { ArrowLeft, Smartphone, Laptop, Tablet, Tv, Cpu, Wifi, Shield, RefreshCw } from 'lucide-react';
import { CONNECTED_DEVICES } from '@/lib/data';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';

interface DevicesConnectedViewProps {
  onBack: () => void;
}

export const DevicesConnectedView: React.FC<DevicesConnectedViewProps> = ({ onBack }) => {
  const { showToast } = useToast();
  const [devices, setDevices] = useState(CONNECTED_DEVICES);

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
        <div className="text-center">
          <h1 className="text-base font-bold text-slate-900 leading-tight">Perangkat Terhubung</h1>
          <span className="text-[10px] text-slate-500 font-medium">5 perangkat aktif di jaringan</span>
        </div>
        <button
          onClick={() => showToast('Memindai perangkat aktif di router gateway... 5 perangkat terhubung optimal.', 'info')}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Overview Banner */}
      <div className="p-4 rounded-3xl bg-slate-900 text-white flex items-center justify-between">
        <div>
          <span className="text-[10px] uppercase font-bold text-slate-400">Jaringan Rumah</span>
          <h3 className="text-sm font-bold mt-0.5">Partner_WiFi_5G</h3>
          <p className="text-xs text-emerald-400 font-semibold mt-0.5">● Semua perangkat dalam kondisi aman</p>
        </div>
        <div className="w-10 h-10 rounded-2xl bg-white/10 flex items-center justify-center text-emerald-400">
          <Shield className="w-5 h-5" />
        </div>
      </div>

      {/* Devices List (Sheet 5 Screen 7) */}
      <div className="space-y-2.5">
        {devices.map((dev) => (
          <div
            key={dev.id}
            className="p-3.5 rounded-2xl bg-white border border-slate-100 shadow-2xs flex items-center justify-between"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-center shrink-0">
                {dev.type === 'phone' && <Smartphone className="w-5 h-5 text-blue-600" />}
                {dev.type === 'laptop' && <Laptop className="w-5 h-5 text-slate-700" />}
                {dev.type === 'tablet' && <Tablet className="w-5 h-5 text-purple-600" />}
                {dev.type === 'tv' && <Tv className="w-5 h-5 text-amber-600" />}
                {dev.type === 'iot' && <Cpu className="w-5 h-5 text-emerald-600" />}
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-900 leading-tight">{dev.name}</h4>
                <div className="flex items-center gap-2 text-[10px] text-slate-500 mt-0.5">
                  <span className="font-mono">{dev.ip}</span>
                  <span>·</span>
                  <span>{dev.connectedAt}</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <div className="text-right">
                <span className="text-[11px] font-bold text-slate-800 block">{dev.bandwidth}</span>
                <span className="text-[9px] text-emerald-600 font-medium">Optimal</span>
              </div>
              <Wifi className="w-4 h-4 text-emerald-500" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
