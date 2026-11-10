'use client';

import React, { useState } from 'react';
import { ArrowLeft, Server, Wifi, Shield, Save, CheckCircle2, RotateCw } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';

interface PartnerGatewayConfigViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

export const PartnerGatewayConfigView: React.FC<PartnerGatewayConfigViewProps> = ({
  onBack,
  onNavigateTab,
}) => {
  const { showToast } = useToast();
  const [gatewayType, setGatewayType] = useState<'mikrotik' | 'unifi' | 'isp_fiber_ont'>('mikrotik');
  const [ssidName, setSsidName] = useState('CoffeeHouse_PartnerWiFi');
  const [radiusServer, setRadiusServer] = useState('10.200.1.1');
  const [hotspotPort, setHotspotPort] = useState('3990');
  const [walledGarden, setWalledGarden] = useState('*.moreai.id, *.partner-isp.net, *.partner-network.com');
  const [isTesting, setIsTesting] = useState(false);

  const handleTestConnection = () => {
    setIsTesting(true);
    setTimeout(() => {
      setIsTesting(false);
      showToast('Koneksi Gateway MikroTik / UniFi Berhasil! (Latency 4ms, Status: Siap Melayani Tamu)', 'success');
    }, 900);
  };

  const handleSave = () => {
    showToast('Konfigurasi gateway jaringan venue berhasil disimpan dan diterapkan.', 'success');
    onNavigateTab('partner');
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
            Sheet 4 Screen 5
          </span>
          <h1 className="text-sm sm:text-base font-bold text-slate-900 leading-tight">
            Konfigurasi Gateway &amp; SSID
          </h1>
        </div>
        <div className="w-5" />
      </div>

      {/* Gateway Hardware Selector */}
      <div className="bg-white rounded-3xl p-4 sm:p-5 border border-slate-100 shadow-xs space-y-3">
        <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
          Pilih Perangkat / Kontroler Gateway
        </h2>

        <div className="grid grid-cols-3 gap-2">
          <button
            onClick={() => setGatewayType('mikrotik')}
            className={`p-3 rounded-2xl border text-center transition ${
              gatewayType === 'mikrotik'
                ? 'border-red-500 bg-red-50/60 text-red-700 font-bold'
                : 'border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-100'
            }`}
          >
            <Server className="w-5 h-5 mx-auto mb-1" />
            <span className="text-[11px] block">MikroTik RouterOS</span>
          </button>

          <button
            onClick={() => setGatewayType('unifi')}
            className={`p-3 rounded-2xl border text-center transition ${
              gatewayType === 'unifi'
                ? 'border-red-500 bg-red-50/60 text-red-700 font-bold'
                : 'border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-100'
            }`}
          >
            <Wifi className="w-5 h-5 mx-auto mb-1" />
            <span className="text-[11px] block">UniFi OS Console</span>
          </button>

          <button
            onClick={() => setGatewayType('isp_fiber_ont')}
            className={`p-3 rounded-2xl border text-center transition ${
              gatewayType === 'isp_fiber_ont'
                ? 'border-red-500 bg-red-50/60 text-red-700 font-bold'
                : 'border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-100'
            }`}
          >
            <Shield className="w-5 h-5 mx-auto mb-1" />
            <span className="text-[11px] block">Global ISP Fiber ONT</span>
          </button>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="bg-white rounded-3xl p-4 sm:p-5 border border-slate-100 shadow-xs space-y-3 text-xs">
        <div>
          <label className="font-bold text-slate-700 block mb-1">Nama Jaringan SSID Venue</label>
          <input
            type="text"
            value={ssidName}
            onChange={(e) => setSsidName(e.target.value)}
            className="w-full p-3 rounded-xl border border-slate-200 bg-slate-50 font-bold text-slate-900 focus:bg-white focus:outline-none"
          />
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="font-bold text-slate-700 block mb-1">IP Radius Server</label>
            <input
              type="text"
              value={radiusServer}
              onChange={(e) => setRadiusServer(e.target.value)}
              className="w-full p-3 rounded-xl border border-slate-200 bg-slate-50 font-mono text-slate-900 focus:bg-white focus:outline-none"
            />
          </div>

          <div>
            <label className="font-bold text-slate-700 block mb-1">Port Hotspot</label>
            <input
              type="text"
              value={hotspotPort}
              onChange={(e) => setHotspotPort(e.target.value)}
              className="w-full p-3 rounded-xl border border-slate-200 bg-slate-50 font-mono text-slate-900 focus:bg-white focus:outline-none"
            />
          </div>
        </div>

        <div>
          <label className="font-bold text-slate-700 block mb-1">Walled Garden Domains (Bypass Captive)</label>
          <input
            type="text"
            value={walledGarden}
            onChange={(e) => setWalledGarden(e.target.value)}
            className="w-full p-3 rounded-xl border border-slate-200 bg-slate-50 font-mono text-xs text-slate-800 focus:bg-white focus:outline-none"
          />
        </div>

        <div className="pt-2 flex gap-2">
          <button
            type="button"
            onClick={handleTestConnection}
            disabled={isTesting}
            className="flex-1 py-3 rounded-2xl bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold transition flex items-center justify-center gap-1.5"
          >
            <RotateCw className={`w-3.5 h-3.5 ${isTesting ? 'animate-spin text-red-600' : ''}`} />
            <span>{isTesting ? 'Menguji...' : 'Uji Koneksi Gateway'}</span>
          </button>

          <button
            type="button"
            onClick={handleSave}
            className="flex-1 py-3 rounded-2xl bg-red-600 hover:bg-red-700 text-white font-bold transition flex items-center justify-center gap-1.5 shadow-xs"
          >
            <Save className="w-3.5 h-3.5" />
            <span>Simpan Konfigurasi</span>
          </button>
        </div>
      </div>
    </div>
  );
};
