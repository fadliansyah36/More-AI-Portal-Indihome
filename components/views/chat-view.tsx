'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useToast } from '@/components/ui/toast-context';
import {
  Send,
  Sparkles,
  Paperclip,
  Mic,
  Copy,
  Check,
  RotateCcw,
  Bot,
  User,
  ArrowLeft,
  ChevronRight,
  ShieldCheck,
} from 'lucide-react';
import { NavigationTab } from '@/types/moreai';

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  time: string;
  source?: string;
}

interface ChatViewProps {
  onBack: () => void;
  initialPrompt?: string;
  onNavigateTab?: (tab: NavigationTab) => void;
}

export const ChatView: React.FC<ChatViewProps> = ({ onBack, initialPrompt = '', onNavigateTab }) => {
  const { showToast } = useToast();
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg-1',
      sender: 'assistant',
      text: 'Halo! Ada yang bisa saya bantu hari ini?',
      time: '09:41',
      source: 'MoreAI Knowledge Base',
    },
    {
      id: 'msg-2',
      sender: 'user',
      text: 'Buatkan ide konten untuk UMKM kopi',
      time: '09:42',
    },
    {
      id: 'msg-3',
      sender: 'assistant',
      text: `Berikut beberapa ide konten yang terbukti menarik untuk UMKM kopi:

✓ **Tips menyeduh kopi di rumah**
   - Panduan rasio kopi & air dengan alat manual brew sederhana (V60 / French Press).
✓ **Cerita di balik biji kopi lokal**
   - Mengangkat kearifan petani kopi lokal Nusantara (Temanggung, Gayo, Kintamani).
✓ **Promo spesial akhir pekan**
   - Diskon bundling kopi susu + pastry khusus pelanggan yang datang langsung.`,
      time: '09:42',
      source: 'MoreAI Knowledge Base & IndiHome Network',
    },
  ]);

  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const promptSuggestions = [
    'Rangkuman artikel',
    'Buat ide konten',
    'Terjemahkan teks',
    'Ringkas dokumen',
    'Analisis data',
  ];

  const handleSendMessage = React.useCallback(async (textToSend?: string) => {
    const text = textToSend || inputText.trim();
    if (!text || isLoading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/gemini/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });

      if (!response.ok) {
        throw new Error('Gagal mengambil respon dari server');
      }

      const data = await response.json();
      const botMsg: ChatMessage = {
        id: `bot-${Date.now()}`,
        sender: 'assistant',
        text: data.reply || 'Maaf, terjadi kesalahan saat memproses jawaban.',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        source: data.source || 'MoreAI Knowledge Base',
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch {
      // Offline / fallback reply
      const botMsg: ChatMessage = {
        id: `bot-${Date.now()}`,
        sender: 'assistant',
        text: `Terima kasih! Permintaan Anda mengenai "${text}" telah dicatat. MoreAI terintegrasi dengan jaringan IndiHome untuk memberikan jawaban akurat dan cepat.`,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        source: 'MoreAI Knowledge Base (Offline Mode)',
      };
      setMessages((prev) => [...prev, botMsg]);
    } finally {
      setIsLoading(false);
    }
  }, [inputText, isLoading]);

  const sentInitialRef = useRef(false);

  // If initialPrompt passed, send it
  useEffect(() => {
    if (initialPrompt && initialPrompt.trim() && !sentInitialRef.current) {
      sentInitialRef.current = true;
      const timer = setTimeout(() => {
        handleSendMessage(initialPrompt.trim());
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [initialPrompt, handleSendMessage]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const copyToClipboard = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] max-h-[800px] bg-slate-50 rounded-3xl border border-slate-100 overflow-hidden shadow-xs animate-fadeIn">
      {/* Top Chat Bar */}
      <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-slate-100 shrink-0">
        <div className="flex items-center gap-2.5">
          <button
            onClick={onBack}
            className="p-1.5 -ml-1 rounded-xl text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="w-8 h-8 rounded-xl bg-red-600 text-white flex items-center justify-center font-bold text-xs shadow-xs">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-xs sm:text-sm font-bold text-slate-900 leading-tight">
              MoreAI Assistant
            </h2>
            <div className="flex items-center gap-1.5 text-[10px] text-slate-500">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              <span>Koneksi Wi-Fi IndiHome 100 Mbps</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="text-[10px] font-semibold text-slate-600 bg-slate-100 px-2.5 py-1 rounded-full border border-slate-200">
            Quota: 100K Poin
          </span>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${
              msg.sender === 'user' ? 'items-end' : 'items-start'
            }`}
          >
            <div
              className={`max-w-[88%] sm:max-w-[80%] rounded-2xl px-3.5 py-2.5 text-xs sm:text-sm leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-red-600 text-white rounded-tr-xs shadow-xs'
                  : 'bg-white text-slate-800 rounded-tl-xs border border-slate-200/80 shadow-2xs'
              }`}
            >
              <div className="whitespace-pre-line">{msg.text}</div>

              {msg.source && (
                <div className="mt-2 pt-1.5 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400">
                  <span className="flex items-center gap-1">
                    <ShieldCheck className="w-3 h-3 text-red-500" />
                    <span>Sumber: {msg.source}</span>
                  </span>
                  <button
                    onClick={() => copyToClipboard(msg.id, msg.text)}
                    className="p-1 hover:text-slate-700 transition"
                    title="Salin Pesan"
                  >
                    {copiedId === msg.id ? (
                      <Check className="w-3 h-3 text-emerald-600" />
                    ) : (
                      <Copy className="w-3 h-3" />
                    )}
                  </button>
                </div>
              )}
            </div>
            <span className="text-[9px] text-slate-400 mt-1 px-1">
              {msg.time}
            </span>
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center gap-2 p-3 bg-white rounded-2xl border border-slate-100 max-w-[200px] text-xs text-slate-500 shadow-2xs">
            <Sparkles className="w-4 h-4 text-red-500 animate-spin" />
            <span>MoreAI sedang mengetik...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Prompt Chips */}
      <div className="px-3 pt-2 pb-1 bg-white border-t border-slate-100/80 shrink-0">
        <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar pb-1">
          {promptSuggestions.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handleSendMessage(prompt)}
              className="px-2.5 py-1 rounded-full bg-slate-50 hover:bg-red-50 text-slate-600 hover:text-red-600 border border-slate-200/80 hover:border-red-200 text-[11px] font-medium whitespace-nowrap transition active:scale-95 shrink-0"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* Message Input Bar */}
      <div className="p-3 bg-white shrink-0">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex items-center gap-1.5 rounded-2xl bg-slate-50 border border-slate-200 p-1.5 focus-within:ring-2 focus-within:ring-red-500/20 focus-within:border-red-500 transition"
        >
          <button
            type="button"
            onClick={() => onNavigateTab && onNavigateTab('files')}
            className="p-2 text-slate-400 hover:text-slate-600 rounded-xl hover:bg-slate-200/50 transition"
            title="Unggah Dokumen"
          >
            <Paperclip className="w-4 h-4" />
          </button>

          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Tulis pesan..."
            className="flex-1 bg-transparent text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none px-1"
          />

          <button
            type="button"
            onClick={() => showToast('Fitur Voice Input: Siap menerima input suara Anda.', 'info')}
            className="p-2 text-slate-400 hover:text-slate-600 rounded-xl hover:bg-slate-200/50 transition"
            title="Voice Input"
          >
            <Mic className="w-4 h-4" />
          </button>

          <button
            type="submit"
            disabled={!inputText.trim() || isLoading}
            className="w-8 h-8 rounded-xl bg-red-600 hover:bg-red-700 disabled:opacity-40 text-white flex items-center justify-center transition shadow-xs active:scale-95"
            title="Kirim"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
