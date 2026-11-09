'use client';

import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

interface ToastItem {
  id: string;
  message: string;
  type?: 'success' | 'info' | 'error';
}

interface ToastContextType {
  showToast: (message: string, type?: 'success' | 'info' | 'error') => void;
}

const ToastContext = createContext<ToastContextType>({
  showToast: () => {},
});

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const showToast = useCallback((message: string, type: 'success' | 'info' | 'error' = 'info') => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3500);
  }, []);

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      {/* Toast Notification Container */}
      <div className="fixed bottom-16 sm:bottom-6 right-3 sm:right-6 z-50 flex flex-col gap-2 max-w-sm pointer-events-none">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`pointer-events-auto flex items-start gap-2.5 p-3.5 rounded-2xl shadow-xl border text-xs font-medium animate-fadeIn backdrop-blur-md transition-all ${
              toast.type === 'success'
                ? 'bg-white/95 dark:bg-slate-900/95 border-emerald-500/30 text-emerald-950 dark:text-emerald-200'
                : toast.type === 'error'
                ? 'bg-white/95 dark:bg-slate-900/95 border-red-500/30 text-red-950 dark:text-red-200'
                : 'bg-white/95 dark:bg-slate-900/95 border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100'
            }`}
          >
            {toast.type === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />}
            {toast.type === 'error' && <AlertCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />}
            {toast.type === 'info' && <Info className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />}
            <span className="flex-1 leading-relaxed">{toast.message}</span>
            <button
              onClick={() => removeToast(toast.id)}
              className="text-slate-400 hover:text-slate-600 p-0.5"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => useContext(ToastContext);
