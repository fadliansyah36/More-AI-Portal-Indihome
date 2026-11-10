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
import { moreAiApi, moreAiApiStream } from '@/lib/api/client';

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
      id: 'welcome',
      sender: 'assistant',
      text: 'Halo! Silakan tulis kebutuhan Anda. Pesan akan diproses melalui MoreAI Agent Runtime.',
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      source: 'MoreAI',
    },
  ]);
  const [conversationId, setConversationId] = useState<string | null>(null);  const handleSendMessage = React.useCallback(async (textToSend?: string) => {
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

    const assistantId = `run-${Date.now()}`;
    let streamedText = '';
    let terminalStatus: string | null = null;
    let finalOutput: Record<string, unknown> | undefined;

    try {
      let activeConversationId = conversationId;
      if (!activeConversationId) {
        const created = await moreAiApi<{ id: string }>('/api/v1/conversations', {
          method: 'POST',
          body: JSON.stringify({ title: text.slice(0, 120) }),
        });
        activeConversationId = created.id;
        setConversationId(created.id);
      }

      const queued = await moreAiApi<{ run: { id: string; status: string } }>(
        `/api/v1/conversations/${activeConversationId}/messages`,
        {
          method: 'POST',
          headers: { 'Idempotency-Key': crypto.randomUUID() },
          body: JSON.stringify({ content: text, agent_key: 'manus' }),
        },
      );

      setMessages((prev) => [...prev, {
        id: assistantId,
        sender: 'assistant',
        text: '',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        source: 'MoreAI Agent Runtime',
      }]);

      await moreAiApiStream(
        `/api/v1/agent-runs/${queued.run.id}/stream?wait_seconds=30`,
        ({ event, data }) => {
          if (event === 'worker.checkpoint') {
            const checkpoint = data.checkpoint as Record<string, unknown> | undefined;
            if (typeof checkpoint?.text === 'string') {
              streamedText += checkpoint.text;
              setMessages((prev) => prev.map((message) =>
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
        },
      );

      let finalRun: { status: string; output?: Record<string, unknown>; error?: Record<string, unknown> } | null = null;
      if (!terminalStatus) {
        for (let attempt = 0; attempt < 5; attempt += 1) {
          await new Promise((resolve) => setTimeout(resolve, 1200));
          finalRun = await moreAiApi<typeof finalRun & {}>(`/api/v1/agent-runs/${queued.run.id}`);
          if (['succeeded', 'failed', 'cancelled'].includes(finalRun.status)) break;
        }
        terminalStatus = finalRun?.status || queued.run.status;
        finalOutput = finalRun?.output || finalOutput;
      }

      const outputText = typeof finalOutput?.text === 'string'
        ? finalOutput.text
        : typeof finalOutput?.content === 'string'
          ? finalOutput.content
          : streamedText;

      if (terminalStatus === 'succeeded') {
        setMessages((prev) => prev.map((message) =>
          message.id === assistantId ? { ...message, text: outputText || 'Agent selesai tanpa teks keluaran.' } : message,
        ));
      } else if (terminalStatus === 'failed' || terminalStatus === 'cancelled') {
        throw new Error(`Agent run ${terminalStatus}. Silakan coba kembali atau periksa riwayat tugas.`);
      } else {
        setMessages((prev) => prev.map((message) =>
          message.id === assistantId
            ? { ...message, text: streamedText || 'Permintaan sudah masuk antrean MoreAI. Status eksekusi dapat dipantau pada riwayat tugas.', source: `Agent Runtime · ${terminalStatus}` }
            : message,
        ));
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'MoreAI API tidak dapat memproses permintaan.';
      showToast(message, 'error');
      setMessages((prev) => {
        const existing = prev.some((item) => item.id === assistantId);
        if (!existing) {
          return [...prev, {
            id: assistantId,
            sender: 'assistant',
            text: message,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            source: 'MoreAI API',
          }];
        }
        return prev.map((item) => item.id === assistantId ? { ...item, text: message, source: 'MoreAI API' } : item);
      });
    } finally {
      setIsLoading(false);
    }
  }, [inputText, isLoading, conversationId, showToast]);
