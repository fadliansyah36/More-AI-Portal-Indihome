'use client';

import React, { useSyncExternalStore } from 'react';
import { WifiOff } from 'lucide-react';

function subscribeOnline(callback: () => void) {
  window.addEventListener('online', callback);
  window.addEventListener('offline', callback);
  return () => {
    window.removeEventListener('online', callback);
    window.removeEventListener('offline', callback);
  };
}

function getOnlineSnapshot() {
  return navigator.onLine;
}

function getServerSnapshot() {
  return true;
}

export const OfflineIndicator: React.FC = () => {
  const isOnline = useSyncExternalStore(
    subscribeOnline,
    getOnlineSnapshot,
    getServerSnapshot
  );

  if (isOnline) return null;

  return (
    <div className="fixed top-2 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 rounded-full bg-slate-900/90 text-white px-3.5 py-1.5 text-xs font-medium shadow-lg backdrop-blur-xs border border-white/10 animate-bounce">
      <WifiOff className="w-3.5 h-3.5 text-amber-400" />
      <span>Mode Offline — Cache data MoreAI aktif</span>
    </div>
  );
};
