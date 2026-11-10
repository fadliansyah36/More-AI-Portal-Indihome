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
import { moreAiApi } from '@/lib/api/client';

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

      let finalRun: { status: string; output?: Record<string, unknown>; error?: Record<string, unknown> } = queued.run;
      for (let attempt = 0; attempt < 5 && !['succeeded', 'failed', 'cancelled'].includes(finalRun.status); attempt += 1) {
        await new Promise((resolve) => setTimeout(resolve, 1200));
        finalRun = await moreAiApi<typeof finalRun>(`/api/v1/agent-runs/${queued.run.id}`);
      }

      const outputText = typeof finalRun.output?.text === 'string'
        ? finalRun.output.text
        : typeof finalRun.output?.content === 'string'
          ? finalRun.output.content
          : null;

      if (finalRun.status === 'succeeded' && outputText) {
        setMessages((prev) => [...prev, {
          id: `run-${queued.run.id}`,
          sender: 'assistant',
          text: outputText,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          source: 'MoreAI Agent Runtime',
        }]);
      } else if (finalRun.status === 'failed' || finalRun.status === 'cancelled') {
        throw new Error(`Agent run ${finalRun.status}. Silakan coba kembali atau periksa riwayat tugas.`);
      } else {
        setMessages((prev) => [...prev, {
          id: `run-${queued.run.id}`,
          sender: 'assistant',
          text: 'Permintaan berhasil masuk ke antrean MoreAI. Status eksekusi dapat dipantau pada riwayat tugas.',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          source: `Agent Runtime · ${finalRun.status}`,
        }]);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'MoreAI API tidak dapat memproses permintaan.';
      showToast(message, 'error');
      setMessages((prev) => [...prev, {
        id: `error-${Date.now()}`,
        sender: 'assistant',
        text: message,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        source: 'MoreAI API',
      }]);
    } finally {
      setIsLoading(false);
    }
  }, [inputText, isLoading, conversationId, showToast]);
