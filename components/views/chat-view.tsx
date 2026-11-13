'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { ArrowLeft, Bot, Copy, Loader2, Paperclip, Send, ShieldCheck, Sparkles, StopCircle, User } from 'lucide-react';
import { useToast } from '@/components/ui/toast-context';
import { NavigationTab } from '@/types/moreai';
import { customerApi, moreAiApiStream } from '@/lib/api/client';

interface ChatCitation {
  id: string;
  document_id: string;
  title: string;
  similarity?: number;
  source_page?: number | null;
  char_start?: number | null;
  char_end?: number | null;
  marker: string;
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  time: string;
  source?: string;
  citations?: ChatCitation[];
}

interface ChatViewProps {
  onBack: () => void;
  initialPrompt?: string;
  initialAgentKey?: 'manus' | 'planning';
  onNavigateTab?: (tab: NavigationTab) => void;
}

const timeLabel = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

export const ChatView: React.FC<ChatViewProps> = ({ onBack, initialPrompt = '', initialAgentKey = 'manus' }) => {
  const { showToast } = useToast();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [inputText, setInputText] = useState(initialPrompt);
  const [isLoading, setIsLoading] = useState(false);
  const [isRestoringConversation, setIsRestoringConversation] = useState(!initialPrompt.trim());
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [isCancelling, setIsCancelling] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const sentInitialPrompt = useRef(false);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (initialPrompt.trim()) {
      setIsRestoringConversation(false);
      return;
    }
    let active = true;
    const restoreLatestConversation = async () => {
      try {
        const conversations = await customerApi.conversations(50);
        const latest = conversations.find((item) => item.status === 'active');
        if (!latest || !active) return;
        const restored = await customerApi.getConversation(latest.id);
        if (!active) return;
        setConversationId(restored.conversation.id);
        setMessages(restored.messages
          .filter((message) => message.role === 'user' || message.role === 'assistant')
          .map((message) => ({
            id: message.id,
            sender: message.role as 'user' | 'assistant',
            text: message.content,
            time: new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            source: message.role === 'assistant' ? 'MoreAI Agent Runtime' : undefined,
          })));
      } catch {
        // Conversation history remains server-authoritative. A failed restore
        // leaves the composer available to create a fresh conversation.
      } finally {
        if (active) setIsRestoringConversation(false);
      }
    };
    void restoreLatestConversation();
    return () => { active = false; };
  }, [initialPrompt]);

  const handleSendMessage = useCallback(async (textToSend?: string) => {
    const text = (textToSend ?? inputText).trim();
    if (!text || isLoading || isRestoringConversation) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      sender: 'user',
      text,
      time: timeLabel(),
    };
    const assistantId = crypto.randomUUID();
    setMessages((previous) => [...previous, userMessage]);
    setInputText('');
    setIsLoading(true);

    let streamedText = '';
    let terminalStatus: string | null = null;
    let finalOutput: Record<string, unknown> | undefined;

    try {
      let activeConversationId = conversationId;
      if (!activeConversationId) {
        const created = await customerApi.createConversation(text.slice(0, 120));
        activeConversationId = created.id;
        setConversationId(created.id);
      }

      const queued = await customerApi.sendMessage(
        activeConversationId, text, crypto.randomUUID(), initialAgentKey,
      );
      setActiveRunId(queued.run.id);

      setMessages((previous) => [...previous, {
        id: assistantId,
        sender: 'assistant',
        text: '',
        time: timeLabel(),
        source: 'MoreAI Agent Runtime',
      }]);

      await moreAiApiStream(customerApi.streamRun(queued.run.id), ({ event, data }) => {
        // FastAPI streams the durable agent_run_events.event_type value. Worker
        // checkpoints are published as run.progress (not worker.checkpoint).
        if (event === 'run.progress' || event === 'worker.checkpoint') {
          const checkpoint = data.checkpoint as Record<string, unknown> | undefined;
          if (typeof checkpoint?.text === 'string') {
            // Checkpoint text is a persisted snapshot; replace rather than append
            // so Last-Event-ID replay cannot duplicate already-rendered content.
            streamedText = checkpoint.text;
            setMessages((previous) => previous.map((message) =>
              message.id === assistantId ? { ...message, text: streamedText } : message,
            ));
          }
        } else if (event === 'run.completed') {
          terminalStatus = 'succeeded';
          finalOutput = data.output as Record<string, unknown> | undefined;
        } else if (event === 'run.failed') {
          terminalStatus = 'failed';
          finalOutput = data.error as Record<string, unknown> | undefined;
        } else if (event === 'run.cancelled') {
          terminalStatus = 'cancelled';
        }
      });

      let finalRun: { status: string; output?: Record<string, unknown>; error?: Record<string, unknown> } | null = null;
      if (!terminalStatus) {
        for (let attempt = 0; attempt < 5; attempt += 1) {
          await new Promise((resolve) => window.setTimeout(resolve, 1200));
          finalRun = await customerApi.getRun(queued.run.id);
          if (['succeeded', 'failed', 'cancelled'].includes(finalRun.status)) break;
        }
        terminalStatus = finalRun?.status ?? queued.run.status;
        finalOutput = finalRun?.output ?? finalOutput;
      }

      const outputText = typeof finalOutput?.text === 'string'
        ? finalOutput.text
        : typeof finalOutput?.content === 'string'
          ? finalOutput.content
          : streamedText;

      if (terminalStatus === 'succeeded') {
        const citations = Array.isArray(finalOutput?.citations)
          ? finalOutput.citations.filter((item): item is ChatCitation =>
              !!item && typeof item === 'object'
              && typeof (item as ChatCitation).id === 'string'
              && typeof (item as ChatCitation).document_id === 'string'
              && typeof (item as ChatCitation).title === 'string'
              && typeof (item as ChatCitation).marker === 'string',
            )
          : [];
        setMessages((previous) => previous.map((message) =>
          message.id === assistantId ? { ...message, text: outputText, citations } : message,
        ));
      } else if (terminalStatus === 'cancelled') {
        setMessages((previous) => previous.map((message) =>
          message.id === assistantId ? { ...message, text: streamedText || 'Proses dihentikan sesuai permintaan.', source: 'Agent Runtime · cancelled' } : message,
        ));
      } else if (terminalStatus === 'failed') {
        throw new Error('Agent run failed. Silakan periksa riwayat tugas sebelum mencoba kembali.');
      } else {
        setMessages((previous) => previous.map((message) =>
          message.id === assistantId
            ? { ...message, text: streamedText || 'Run masih diproses. Periksa statusnya pada riwayat tugas.', source: `Agent Runtime · ${terminalStatus}` }
            : message,
        ));
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'MoreAI API tidak dapat memproses permintaan.';
      showToast(message, 'error');
      setMessages((previous) => [...previous, {
        id: assistantId,
        sender: 'assistant',
        text: message,
        time: timeLabel(),
        source: 'MoreAI API',
      }]);
    } finally {
      setActiveRunId(null);
      setIsCancelling(false);
      setIsLoading(false);
    }
  }, [inputText, isLoading, isRestoringConversation, conversationId, showToast, initialAgentKey]);

  const handleCancelRun = useCallback(async () => {
    if (!activeRunId || isCancelling) return;
    setIsCancelling(true);
    try {
      await customerApi.cancelRun(activeRunId);
      showToast('Permintaan penghentian dikirim ke worker. Proses akan berhenti setelah checkpoint aman.', 'success');
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Tidak dapat menghentikan agent run.', 'error');
      setIsCancelling(false);
    }
  }, [activeRunId, isCancelling, showToast]);

  useEffect(() => {
    if (initialPrompt.trim() && !sentInitialPrompt.current) {
      sentInitialPrompt.current = true;
      void handleSendMessage(initialPrompt);
    }
  }, [initialPrompt, handleSendMessage]);

  return (
    <section className="flex h-[calc(100dvh-5rem)] min-h-[32rem] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <header className="flex items-center gap-3 border-b border-slate-100 px-4 py-3">
        <button type="button" onClick={onBack} aria-label="Kembali" className="rounded-xl p-2 text-slate-600 transition hover:bg-slate-100">
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-red-50 text-red-600">
          <Bot className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <h1 className="text-sm font-bold text-slate-900">MoreAI Assistant</h1>
          <p className="text-xs text-slate-500">Agent Runtime · Percakapan tersimpan</p>
        </div>
        {activeRunId && (
          <button type="button" onClick={() => void handleCancelRun()} disabled={isCancelling} className="inline-flex items-center gap-1.5 rounded-xl border border-red-200 px-3 py-2 text-xs font-semibold text-red-600 transition hover:bg-red-50 disabled:opacity-60" aria-label="Hentikan proses agent">
            {isCancelling ? <Loader2 className="h-4 w-4 animate-spin" /> : <StopCircle className="h-4 w-4" />}
            {isCancelling ? 'Menghentikan…' : 'Hentikan'}
          </button>
        )}
        <ShieldCheck className="h-5 w-5 text-emerald-600" aria-label="Koneksi API terautentikasi" />
      </header>

      <div className="flex-1 space-y-4 overflow-y-auto bg-slate-50/70 px-4 py-5">
        {messages.length === 0 && (
          <div className="mx-auto flex max-w-md flex-col items-center py-12 text-center">
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-red-50 text-red-600">
              <Sparkles className="h-7 w-7" />
            </div>
            <h2 className="text-base font-semibold text-slate-900">Apa yang ingin Anda kerjakan?</h2>
            <p className="mt-1 text-sm text-slate-500">Permintaan akan dikirim ke MoreAI API dan diproses oleh agent runtime yang dikonfigurasi.</p>
          </div>
        )}
        {messages.map((message) => (
          <article key={message.id} className={`flex gap-2.5 ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            {message.sender === 'assistant' && (
              <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-red-50 text-red-600">
                <Bot className="h-4 w-4" />
              </div>
            )}
            <div className={`max-w-[85%] rounded-2xl px-4 py-3 shadow-xs ${message.sender === 'user' ? 'rounded-tr-sm bg-red-600 text-white' : 'rounded-tl-sm border border-slate-100 bg-white text-slate-800'}`}>
              <p className="whitespace-pre-wrap break-words text-sm leading-6">{message.text || 'Agent sedang memproses…'}</p>
              <div className={`mt-2 flex items-center justify-between gap-4 text-[10px] ${message.sender === 'user' ? 'text-red-100' : 'text-slate-400'}`}>
                <span>{message.source ?? (message.sender === 'user' ? 'Anda' : 'MoreAI')}</span>
                <span>{message.time}</span>
              </div>
              {message.sender === 'assistant' && message.citations && message.citations.length > 0 && (
                <div className="mt-3 border-t border-slate-100 pt-2">
                  <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-400">Sumber pengetahuan</p>
                  <ul className="space-y-1">
                    {message.citations.map((citation) => (
                      <li key={citation.id} className="text-xs text-slate-600">
                        <span className="font-medium">{citation.title}</span>
                        {citation.source_page ? <span className="ml-1 text-[10px] text-slate-500">hal. {citation.source_page}</span> : null}
                        <span className="ml-1 font-mono text-[10px] text-slate-400">{citation.marker}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {message.sender === 'assistant' && message.text && (
                <button type="button" onClick={() => navigator.clipboard.writeText(message.text)} className="mt-2 inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-800">
                  <Copy className="h-3 w-3" /> Salin
                </button>
              )}
            </div>
            {message.sender === 'user' && (
              <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-slate-200 text-slate-600">
                <User className="h-4 w-4" />
              </div>
            )}
          </article>
        ))}
        {(isLoading || isRestoringConversation) && (
          <div className="flex items-center gap-2 pl-10 text-xs text-slate-500">
            <Loader2 className="h-4 w-4 animate-spin" /> {isRestoringConversation ? 'Memulihkan percakapan tersimpan…' : 'Menghubungkan ke agent runtime…'}
          </div>
        )}
        <div ref={endRef} />
      </div>

      <form onSubmit={(event) => { event.preventDefault(); void handleSendMessage(); }} className="border-t border-slate-100 bg-white p-3">
        <div className="flex items-end gap-2 rounded-2xl border border-slate-200 bg-slate-50 p-2 focus-within:border-red-300">
          <button type="button" disabled aria-label="Lampiran belum tersedia" className="rounded-xl p-2 text-slate-300">
            <Paperclip className="h-5 w-5" />
          </button>
          <textarea
            value={inputText}
            onChange={(event) => setInputText(event.target.value)}
            onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); void handleSendMessage(); } }}
            placeholder="Tulis pesan untuk MoreAI…"
            rows={1}
            disabled={isLoading || isRestoringConversation}
            className="max-h-32 min-h-10 flex-1 resize-y bg-transparent px-2 py-2 text-sm text-slate-900 outline-none placeholder:text-slate-400 disabled:opacity-60"
          />
          <button type="submit" disabled={isLoading || isRestoringConversation || !inputText.trim()} aria-label="Kirim pesan" className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-red-600 text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:bg-slate-300">
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </button>
        </div>
        <p className="mt-2 text-center text-[10px] text-slate-400">Respons diproses melalui backend MoreAI. Ketersediaan bergantung pada konfigurasi agent dan provider.</p>
      </form>
    </section>
  );
};
