'use client';

import React, { useState } from 'react';
import { useToast } from '@/components/ui/toast-context';
import {
  Wifi,
  Smartphone,
  Laptop,
  Tablet,
  Tv,
  Cpu,
  Lock,
  Key,
  Calendar,
  Shield,
  Activity,
  ArrowRight,
  Eye,
  EyeOff,
  CheckCircle2,
  RefreshCw,
  Gauge,
  Sliders,
  Timer,
  ChevronRight,
} from 'lucide-react';
import { CONNECTED_DEVICES } from '@/lib/data';
import { ConnectedDevice, NavigationTab } from '@/types/moreai';

interface WifiManagementViewProps {
  onNavigateTab?: (tab: NavigationTab) => void;
}

export const WifiManagementView: React.FC<WifiManagementViewProps> = ({ onNavigateTab }) => {
  const { showToast } = useToast();
  const [showPassword, setShowPassword] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [devices, setDevices] = useState<ConnectedDevice[]>(CONNECTED_DEVICES);

  const getDeviceIcon = (type: ConnectedDevice['type']) => {
    switch (type) {
      case 'phone':
        return <Smartphone className="w-5 h-5 text-blue-600" />;
      case 'laptop':
        return <Laptop className="w-5 h-5 text-slate-700" />;
      case 'tablet':
        return <Tablet className="w-5 h-5 text-purple-600" />;
      case 'tv':
        return <Tv className="w-5 h-5 text-amber-600" />;
      case 'iot':
        return <Cpu className="w-5 h-5 text-emerald-600" />;
      default:
        return <Wifi className="w-5 h-5 text-red-600" />;
    }
  };

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      setIsRefreshing(false);
      showToast('Pemeriksaan sinyal Wi-Fi IndiHome selesai: Kondisi Sangat Baik (Latency 8ms).', 'success');
    }, 800);
  };

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Wi-Fi Management</h1>
          <p className="text-xs text-slate-500">Kelola jaringan Wi-Fi IndiHome rumah & perangkat terhubung</p>
        </div>
        <button
          onClick={handleRefresh}
          className="p-2 rounded-xl bg-white border border-slate-200 text-slate-600 hover:text-red-600 transition shadow-2xs"
          title="Segarkan Sinyal"
        >
          <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-red-600' : ''}`} />
        </button>
      </div>

      {/* Main Modem Status Card (Exact from Sheet 5) */}
      <div className="p-5 rounded-3xl bg-gradient-to-br from-red-600 to-rose-700 text-white shadow-md relative overflow-hidden">
        <div className="relative z-10 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-xl bg-white/20 backdrop-blur-xs flex items-center justify-center">
                <Wifi className="w-4 h-4 text-white" />
              </div>
              <div>
                <h3 className="text-sm font-black tracking-tight leading-none">IndiHome 100 Mbps</h3>
                <span className="text-[10px] text-red-100 font-medium">Jaringan Fiber Optik Terverifikasi</span>
              </div>
            </div>
            <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/90 text-white text-[10px] font-bold tracking-wide flex items-center gap-1 shadow-2xs">
              <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
              <span>Aktif</span>
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-white/20">
            <div>
              <span className="text-[10px] text-red-200 block">Status Koneksi</span>
              <span className="text-xs font-bold text-white">Terhubung</span>
            </div>
            <div>
              <span className="text-[10px] text-red-200 block">Kecepatan Internet</span>
              <span className="text-xs font-bold text-white">100 Mbps (Simetris)</span>
            </div>
            <div>
              <span className="text-[10px] text-red-200 block">IP Gateway</span>
              <span className="text-xs font-mono text-white">192.168.1.100</span>
            </div>
            <div>
              <span className="text-[10px] text-red-200 block">Penggunaan Kuota</span>
              <span className="text-xs font-bold text-white">12.4 GB / Unlimited</span>
            </div>
          </div>
        </div>

        {/* Ambient glow decoration */}
        <div className="absolute -right-10 -bottom-10 w-32 h-32 rounded-full bg-white/10 blur-xl pointer-events-none" />
      </div>

      {/* Network Configuration Details (Sheet 5) */}
      <div className="bg-white rounded-3xl p-4 border border-slate-100 shadow-xs space-y-3">
        <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
          Pengaturan Wi-Fi
        </h2>

        <div className="space-y-2 text-xs">
          <div className="flex items-center justify-between p-3 rounded-2xl bg-slate-50 border border-slate-100">
            <div>
              <span className="text-slate-400 block text-[10px]">Nama Jaringan (SSID)</span>
              <span className="font-bold text-slate-800">IndiHome_1234</span>
            </div>
            <button
              onClick={() => showToast('Pengaturan SSID: Anda dapat mengubah nama Wi-Fi di panel router.', 'info')}
              className="text-[11px] font-semibold text-red-600 hover:text-red-700"
            >
              Ubah
            </button>
          </div>

          <div className="flex items-center justify-between p-3 rounded-2xl bg-slate-50 border border-slate-100">
            <div>
              <span className="text-slate-400 block text-[10px]">Kata Sandi Wi-Fi</span>
              <span className="font-mono font-bold text-slate-800">
                {showPassword ? 'Telkom2026!Fast' : '••••••••••••'}
              </span>
            </div>
            <button
              onClick={() => setShowPassword(!showPassword)}
              className="p-1.5 text-slate-400 hover:text-slate-700 transition"
              title={showPassword ? 'Sembunyikan' : 'Tampilkan'}
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 pt-1">
          <button
            onClick={() => showToast('Jadwal Wi-Fi aktif: Pukul 06:00 - 23:00 WIB', 'info')}
            className="p-3 rounded-2xl bg-slate-50 hover:bg-slate-100/80 border border-slate-100 text-left transition"
          >
            <Calendar className="w-4 h-4 text-slate-600 mb-1" />
            <span className="text-xs font-bold text-slate-800 block">Atur Jadwal Wi-Fi</span>
            <span className="text-[10px] text-slate-400">Otomasi on/off malam</span>
          </button>

          <button
            onClick={() => showToast('Proteksi MoreAI Guard aktif memfilter ancaman siber.', 'success')}
            className="p-3 rounded-2xl bg-slate-50 hover:bg-slate-100/80 border border-slate-100 text-left transition"
          >
            <Shield className="w-4 h-4 text-emerald-600 mb-1" />
            <span className="text-xs font-bold text-slate-800 block">MoreAI Guard</span>
            <span className="text-[10px] text-emerald-600 font-medium">Proteksi Aktif</span>
          </button>
        </div>

        {/* Quick Diagnostic Links (Sheet 5 screens #5, #8, #10) */}
        {onNavigateTab && (
          <div className="pt-2 border-t border-slate-100 space-y-1.5">
            <button
              onClick={() => onNavigateTab('speedtest')}
              className="w-full p-2.5 rounded-xl bg-gradient-to-r from-red-50 to-rose-50/50 hover:from-red-100/70 border border-red-100 flex items-center justify-between text-left transition group"
            >
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-lg bg-red-600 text-white flex items-center justify-center">
                  <Gauge className="w-3.5 h-3.5" />
                </div>
                <div>
                  <span className="text-xs font-bold text-slate-900 block">Uji Kecepatan & Diagnostik Optik</span>
                  <span className="text-[10px] text-slate-500">Speedtest 104.2 Mbps, Latensi 9ms</span>
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-red-600 group-hover:translate-x-0.5 transition-transform" />
            </button>

            <button
              onClick={() => onNavigateTab('device_access_control')}
              className="w-full p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-100 flex items-center justify-between text-left transition group"
            >
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-lg bg-slate-900 text-white flex items-center justify-center">
                  <Sliders className="w-3.5 h-3.5" />
                </div>
                <div>
                  <span className="text-xs font-bold text-slate-900 block">Kontrol Akses Perangkat & Kuota</span>
                  <span className="text-[10px] text-slate-500">QoS Bandwidth & Safe Browsing</span>
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-400 group-hover:translate-x-0.5 transition-transform" />
            </button>

            <button
              onClick={() => onNavigateTab('wifi_session')}
              className="w-full p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-100 flex items-center justify-between text-left transition group"
            >
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center">
                  <Timer className="w-3.5 h-3.5" />
                </div>
                <div>
                  <span className="text-xs font-bold text-slate-900 block">Sesi Wi-Fi & Monitor Kuota</span>
                  <span className="text-[10px] text-slate-500">Masa aktif sesi tamu & perpanjangan</span>
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-400 group-hover:translate-x-0.5 transition-transform" />
            </button>
          </div>
        )}
      </div>

      {/* Perangkat Terhubung (5 perangkat) - Sheet 5 */}
      <div className="bg-white rounded-3xl p-4 border border-slate-100 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Perangkat Terhubung
            </h2>
            <span className="text-[10px] font-bold bg-slate-100 text-slate-700 px-2 py-0.5 rounded-full">
              {devices.length} Perangkat
            </span>
          </div>
          <span className="text-[10px] text-emerald-600 font-semibold flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            <span>Koneksi Stabil</span>
          </span>
        </div>

        <div className="space-y-2">
          {devices.map((dev) => (
            <div
              key={dev.id}
              className="p-3 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-white border border-slate-200 flex items-center justify-center shrink-0 shadow-2xs">
                  {getDeviceIcon(dev.type)}
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

              <div className="text-right">
                <span className="text-[11px] font-bold text-slate-800 block">{dev.bandwidth}</span>
                <span className="text-[9px] text-emerald-600 font-medium">Prioritas AI</span>
              </div>
            </div>
          ))}
        </div>

        <button
          onClick={() => showToast('Router gateway IndiHome tersinkronisasi sempurna.', 'success')}
          className="w-full py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold transition"
        >
          Kelola Jaringan Seluruhnya
        </button>
      </div>
    </div>
  );
};
