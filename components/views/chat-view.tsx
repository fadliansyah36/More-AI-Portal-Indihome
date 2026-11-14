'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { ArrowLeft, Bot, Copy, Loader2, Paperclip, Send, ShieldCheck, Sparkles, StopCircle, User, X } from 'lucide-react';
import { useToast } from '@/components/ui/toast-context';
import { NavigationTab } from '@/types/moreai';
import { artifactApi, customerApi, moreAiApiStream, workspaceApi, type CustomerWorkspace } from '@/lib/api/client';

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

interface ChatRunActivity {
  id: string;
  sequence: number;
  event_type: string;
  label: string;
  timestamp?: string;
  tool?: string;
  phase?: string;
  status?: string;
  progress?: number;
  checkpoint_key?: string;
  agent_key?: string;
  step_index?: number;
  risk?: string;
  error_code?: string;
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  time: string;
  source?: string;
  citations?: ChatCitation[];
  activity?: ChatRunActivity[];
  runId?: string;
  runStatus?: string;
  attachments?: Array<{ id: string; filename: string; mime_type?: string | null; size_bytes?: number | null }>;
}

interface ChatViewProps {
  onBack: () => void;
  initialPrompt?: string;
  initialAgentKey?: 'manus' | 'planning' | 'toolcall';
  onNavigateTab?: (tab: NavigationTab) => void;
}

const timeLabel = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

const toChatCitations = (value: unknown): ChatCitation[] => Array.isArray(value)
  ? value.filter((item): item is ChatCitation =>
      !!item && typeof item === 'object'
      && typeof (item as ChatCitation).id === 'string'
      && typeof (item as ChatCitation).document_id === 'string'
      && typeof (item as ChatCitation).title === 'string'
      && typeof (item as ChatCitation).marker === 'string',
    )
  : [];

export const ChatView: React.FC<ChatViewProps> = ({ onBack, initialPrompt = '', initialAgentKey = 'manus' }) => {
  const { showToast } = useToast();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [workspaces, setWorkspaces] = useState<CustomerWorkspace[]>([]);
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState('');
  const [workspaceCursor, setWorkspaceCursor] = useState<string | null>(null);
  const [workspaceLoading, setWorkspaceLoading] = useState(true);
  const [workspaceLoadingMore, setWorkspaceLoadingMore] = useState(false);
  const [workspaceLoadError, setWorkspaceLoadError] = useState<string | null>(null);
  const [inputText, setInputText] = useState(initialPrompt);
  const [isLoading, setIsLoading] = useState(false);
  const [isRestoringConversation, setIsRestoringConversation] = useState(!initialPrompt.trim());
  const [olderMessagesCursor, setOlderMessagesCursor] = useState<string | null>(null);
  const [loadingOlderMessages, setLoadingOlderMessages] = useState(false);
  const [messageHistoryError, setMessageHistoryError] = useState<string | null>(null);
  const [pendingAttachments, setPendingAttachments] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [isCancelling, setIsCancelling] = useState(false);
  const [retryingRunId, setRetryingRunId] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const sentInitialPrompt = useRef(false);
  const suppressAutoScroll = useRef(false);

  useEffect(() => {
    if (suppressAutoScroll.current) {
      suppressAutoScroll.current = false;
      return;
    }
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    let active = true;
    workspaceApi.listPage(100)
      .then((page) => {
        if (!active) return;
        setWorkspaces(page.items);
        setWorkspaceCursor(page.nextCursor);
        setWorkspaceLoadError(null);
      })
      .catch((cause) => {
        if (active) setWorkspaceLoadError(cause instanceof Error ? cause.message : 'Daftar workspace tidak dapat dimuat.');
      })
      .finally(() => { if (active) setWorkspaceLoading(false); });
    return () => { active = false; };
  }, []);

  const loadMoreWorkspaces = async () => {
    if (!workspaceCursor || workspaceLoadingMore || conversationId) return;
    setWorkspaceLoadingMore(true);
    setWorkspaceLoadError(null);
    try {
      const page = await workspaceApi.listPage(100, workspaceCursor);
      setWorkspaces((current) => {
        const known = new Set(current.map((workspace) => workspace.id));
        return [...current, ...page.items.filter((workspace) => !known.has(workspace.id))];
      });
      setWorkspaceCursor(page.nextCursor);
    } catch (cause) {
      setWorkspaceLoadError(cause instanceof Error ? cause.message : 'Pilihan workspace berikutnya tidak dapat dimuat.');
    } finally {
      setWorkspaceLoadingMore(false);
    }
  };

  useEffect(() => {
    if (initialPrompt.trim()) {
      setIsRestoringConversation(false);
      return;
    }
    let active = true;
    const restoreLatestConversation = async () => {
      try {
        const conversations = await customerApi.conversationsPage(50);
        const latest = conversations.items.find((item) => item.status === 'active');
        if (!latest || !active) return;
        const restored = await customerApi.getConversation(latest.id);
        if (!active) return;
        setConversationId(restored.conversation.id);
        setSelectedWorkspaceId(restored.conversation.workspace_id || '');
        setOlderMessagesCursor(restored.nextCursor);
        setMessageHistoryError(null);
        const restoredMessages: ChatMessage[] = restored.messages
          .filter((message) => message.role === 'user' || message.role === 'assistant')
          .map((message) => ({
            id: message.id,
            sender: message.role as 'user' | 'assistant',
            text: message.content,
            time: new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            source: message.role === 'assistant' ? 'MoreAI Agent Runtime' : undefined,
            attachments: message.attachments ?? [],
            citations: message.citations ?? [],
          }));
        setMessages(restoredMessages);

        // A conversation can outlive the browser tab. Recover the latest durable
        // session and its event cursor before opening SSE so replay starts exactly
        // after the last persisted event rather than from sequence zero.
        const sessions = await customerApi.conversationSessions(restored.conversation.id, 50);
        if (!active) return;
        const resumable = sessions.items
          .filter((session) => ['queued', 'pending', 'running', 'awaiting_approval', 'waiting_approval', 'cancel_requested'].includes(session.status))
          .sort((left, right) => new Date(right.created_at).getTime() - new Date(left.created_at).getTime())[0];
        if (resumable) {
          const [session, eventPage, run] = await Promise.all([
            customerApi.conversationSession(restored.conversation.id, resumable.id),
            customerApi.conversationSessionEvents(restored.conversation.id, resumable.id, 0, 500),
            customerApi.getRun(resumable.id),
          ]);
          if (!active) return;
          const cursor = Math.max(
            eventPage.next_after || 0,
            ...eventPage.items.map((item) => item.sequence || 0),
          );
          const checkpointEvent = [...eventPage.items].reverse().find((item) => {
            const checkpoint = item.payload?.checkpoint as Record<string, unknown> | undefined;
            return typeof checkpoint?.text === 'string';
          });
          const checkpoint = checkpointEvent?.payload?.checkpoint as Record<string, unknown> | undefined;
          const existingAssistant = restored.messages.find((message) => message.role === 'assistant' && message.run_id === resumable.id);
          const assistantId = existingAssistant?.id || 'run:' + resumable.id;
          if (!existingAssistant) {
            setMessages((current) => [...current, {
              id: assistantId, sender: 'assistant',
              text: typeof checkpoint?.text === 'string' ? checkpoint.text : '',
              time: timeLabel(), source: 'MoreAI Agent Runtime · melanjutkan sesi',
            }]);
          } else if (typeof checkpoint?.text === 'string') {
            setMessages((current) => current.map((message) =>
              message.id === assistantId ? { ...message, text: checkpoint.text as string } : message,
            ));
          }
          const terminalStates = ['succeeded', 'failed', 'cancelled', 'timed_out', 'expired'];
          if (!terminalStates.includes(run.status) && !terminalStates.includes(session.status)) {
            setActiveRunId(resumable.id);
            setIsLoading(true);
            try {
              await moreAiApiStream(customerApi.streamRun(resumable.id, cursor), ({ event, data }) => {
                if (event === 'run.progress' || event === 'worker.checkpoint') {
                  const nextCheckpoint = data.checkpoint as Record<string, unknown> | undefined;
                  if (typeof nextCheckpoint?.text === 'string') {
                    setMessages((current) => current.map((message) =>
                      message.id === assistantId ? { ...message, text: nextCheckpoint.text as string } : message,
                    ));
                  }
                } else if (event === 'run.completed') {
                  const output = data.output as Record<string, unknown> | undefined;
                  const outputText = typeof output?.text === 'string' ? output.text : typeof output?.content === 'string' ? output.content : '';
                  setMessages((current) => current.map((message) =>
                    message.id === assistantId ? { ...message, text: outputText || message.text, citations: toChatCitations(output?.citations), source: 'MoreAI Agent Runtime · selesai' } : message,
                  ));
                } else if (event === 'run.failed' || event === 'run.cancelled' || event === 'run.timed_out' || event === 'run.expired') {
                  const labels: Record<string, string> = {
                    'run.failed': 'gagal', 'run.cancelled': 'dibatalkan',
                    'run.timed_out': 'melewati batas waktu', 'run.expired': 'kedaluwarsa',
                  };
                  setMessages((current) => current.map((message) =>
                    message.id === assistantId ? {
                      ...message,
                      text: message.text || 'Sesi Agent ' + labels[event] + '. Periksa riwayat tugas untuk detailnya.',
                      source: 'MoreAI Agent Runtime · ' + labels[event],
                    } : message,
                  ));
                }
              });
              const latestRun = await customerApi.getRun(resumable.id);
              if (['succeeded', 'failed', 'cancelled', 'timed_out', 'expired'].includes(latestRun.status)) {
                const output = latestRun.output as Record<string, unknown> | undefined;
                const outputText = typeof output?.text === 'string' ? output.text : typeof output?.content === 'string' ? output.content : '';
                setMessages((current) => current.map((message) =>
                  message.id === assistantId ? {
                    ...message,
                    text: outputText || message.text || ('Agent Run berstatus ' + latestRun.status + '.'),
                    citations: toChatCitations(output?.citations),
                    source: 'MoreAI Agent Runtime · ' + latestRun.status,
                  } : message,
                ));
              }
            } finally {
              if (active) {
                setActiveRunId(null);
                setIsLoading(false);
              }
            }
          }
        }
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

  const loadOlderMessages = async () => {
    if (!conversationId || !olderMessagesCursor || loadingOlderMessages) return;
    setLoadingOlderMessages(true);
    setMessageHistoryError(null);
    try {
      const page = await customerApi.conversationMessagesPage(conversationId, 50, olderMessagesCursor);
      const older = page.items
        .filter((message) => message.role === 'user' || message.role === 'assistant')
        .map((message) => ({
          id: message.id,
          sender: message.role as 'user' | 'assistant',
          text: message.content,
          time: new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          source: message.role === 'assistant' ? 'MoreAI Agent Runtime' : undefined,
          attachments: message.attachments ?? [],
          citations: message.citations ?? [],
        }));
      suppressAutoScroll.current = true;
      setMessages((current) => {
        const known = new Set(current.map((message) => message.id));
        return [...older.filter((message) => !known.has(message.id)), ...current];
      });
      setOlderMessagesCursor(page.nextCursor);
    } catch (cause) {
      setMessageHistoryError(cause instanceof Error ? cause.message : 'Riwayat percakapan sebelumnya tidak dapat dimuat.');
    } finally {
      setLoadingOlderMessages(false);
    }
  };

  const handleSendMessage = useCallback(async (textToSend?: string) => {
    const text = (textToSend ?? inputText).trim();
    const filesToUpload = textToSend === undefined ? [...pendingAttachments] : [];
    if ((!text && filesToUpload.length === 0) || isLoading || isRestoringConversation || workspaceLoading) return;
    const prompt = text || 'Tolong analisis file yang saya lampirkan dan jelaskan temuan pentingnya.';

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      sender: 'user',
      text: prompt,
      time: timeLabel(),
      attachments: filesToUpload.map((file) => ({
        id: file.name + ':' + file.size,
        filename: file.name,
        mime_type: file.type,
        size_bytes: file.size,
      })),
    };
    const assistantId = crypto.randomUUID();
    setMessages((previous) => [...previous, userMessage]);
    setInputText('');
    setIsLoading(true);

    let streamedText = '';
    let terminalStatus: string | null = null;
    let finalOutput: Record<string, unknown> | undefined;
    const lifecycleActivity: ChatRunActivity[] = [];

    try {
      let activeConversationId = conversationId;
      if (!activeConversationId) {
        const created = await customerApi.createConversation(prompt.slice(0, 120), selectedWorkspaceId || null);
        activeConversationId = created.id;
        setConversationId(created.id);
        setOlderMessagesCursor(null);
      }

      const uploadedAttachments = await Promise.all(
        filesToUpload.map((file) => artifactApi.uploadAttachment(activeConversationId as string, file)),
      );
      const queued = await customerApi.sendMessage(
        activeConversationId, prompt, crypto.randomUUID(), initialAgentKey,
        uploadedAttachments.map((attachment) => attachment.id),
      );
      if (filesToUpload.length > 0) setPendingAttachments([]);
      setActiveRunId(queued.run.id);

      setMessages((previous) => [...previous, {
        id: assistantId,
        sender: 'assistant',
        text: '',
        time: timeLabel(),
        source: 'MoreAI Agent Runtime',
        runId: queued.run.id,
        runStatus: queued.run.status,
      }]);

      await moreAiApiStream(customerApi.streamRun(queued.run.id), ({ event, data }) => {
        // The SSE envelope carries a durable event row. Only allowlisted lifecycle
        // metadata is copied into the customer UI; raw payload/tool arguments are never rendered.
        const payload = data.payload && typeof data.payload === 'object'
          ? data.payload as Record<string, unknown>
          : data;
        const sequence = typeof data.sequence === 'number' ? data.sequence : lifecycleActivity.length + 1;
        const tool = typeof payload.tool === 'string' ? payload.tool : undefined;
        const phase = typeof payload.phase === 'string' ? payload.phase : undefined;
        const status = typeof payload.status === 'string' ? payload.status : undefined;
        const progress = typeof payload.progress === 'number' ? payload.progress : undefined;
        const checkpointKey = typeof payload.checkpoint_key === 'string' ? payload.checkpoint_key : undefined;
        const agentKey = typeof payload.agent_key === 'string' ? payload.agent_key : undefined;
        const stepIndex = typeof payload.step_index === 'number' ? payload.step_index : undefined;
        const risk = typeof payload.risk === 'string' ? payload.risk : undefined;
        const errorCode = typeof payload.error_code === 'string' ? payload.error_code : undefined;
        if (!['run.completed', 'run.failed', 'run.cancelled', 'run.timed_out', 'run.expired', 'stream.timeout'].includes(event)) {
          const labels: Record<string, string> = {
            'agent.planning': 'Perencanaan agent',
            'planning.started': 'Perencanaan dimulai',
            'planning.completed': 'Perencanaan selesai',
            'planning.step.started': 'Langkah perencanaan dimulai',
            'planning.step.completed': 'Langkah perencanaan selesai',
            'planning.step.failed': 'Langkah perencanaan gagal',
            'planning.step.approval_required': 'Langkah perencanaan menunggu persetujuan',
            'planning.step.approval_resumed': 'Langkah perencanaan dilanjutkan',
            'agent.execution.started': 'Agent mulai bekerja',
            'agent.execution.completed': 'Agent menyelesaikan eksekusi',
            'agent.execution.failed': 'Eksekusi agent gagal',
            'agent.execution.cancelled': 'Eksekusi agent dibatalkan',
            'agent.execution.timed_out': 'Eksekusi agent melewati batas waktu',
            'tool.started': 'Tool mulai dijalankan',
            'tool.completed': 'Tool selesai dijalankan',
            'tool.failed': 'Tool gagal dijalankan',
            'tool.timed_out': 'Tool melewati batas waktu',
            'tool.cancelled': 'Tool dibatalkan',
            'tool.approval_requested': 'Persetujuan penggunaan tool diminta',
            'tool.approval_granted': 'Persetujuan tool diberikan',
            'tool.approval_denied': 'Persetujuan tool ditolak',
            'tool.approval_expired': 'Persetujuan tool kedaluwarsa',
            'tool.approval_consumed': 'Persetujuan tool digunakan',
            'run.resume_queued': 'Run dilanjutkan ke antrean worker',
            'run.progress': 'Progress eksekusi',
            'worker.checkpoint': 'Checkpoint tersimpan',
            'run.awaiting_approval': 'Menunggu persetujuan',
            'run.cancel_requested': 'Permintaan pembatalan diterima',
          };
          const activity: ChatRunActivity = {
            id: typeof data.id === 'string' ? data.id : queued.run.id + ':' + sequence,
            sequence,
            event_type: event,
            label: labels[event] || event.replace(/[._]/g, ' '),
            timestamp: typeof data.created_at === 'string' ? data.created_at : undefined,
            ...(tool ? { tool } : {}),
            ...(phase ? { phase } : {}),
            ...(status ? { status } : {}),
            ...(progress !== undefined ? { progress } : {}),
            ...(checkpointKey ? { checkpoint_key: checkpointKey } : {}),
            ...(agentKey ? { agent_key: agentKey } : {}),
            ...(stepIndex !== undefined ? { step_index: stepIndex } : {}),
            ...(risk ? { risk } : {}),
            ...(errorCode ? { error_code: errorCode } : {}),
          };
          lifecycleActivity.push(activity);
          setMessages((previous) => previous.map((message) =>
            message.id === assistantId ? { ...message, activity: [...lifecycleActivity] } : message,
          ));
        }
        // FastAPI streams durable agent_run_events. Checkpoint snapshots replace
        // text instead of appending, so replay cannot duplicate rendered output.
        if (event === 'run.progress' || event === 'worker.checkpoint') {
          const checkpoint = (data.checkpoint || payload.checkpoint) as Record<string, unknown> | undefined;
          if (typeof checkpoint?.text === 'string') {
            streamedText = checkpoint.text;
            setMessages((previous) => previous.map((message) =>
              message.id === assistantId ? { ...message, text: streamedText } : message,
            ));
          }
        } else if (event === 'run.awaiting_approval' || event === 'tool.approval_required') {
          setMessages((previous) => previous.map((message) =>
            message.id === assistantId ? { ...message, source: 'MoreAI Agent Runtime · menunggu persetujuan' } : message,
          ));
        } else if (event === 'run.completed') {
          terminalStatus = 'succeeded';
          finalOutput = data.output as Record<string, unknown> | undefined;
        } else if (event === 'run.failed') {
          terminalStatus = 'failed';
          finalOutput = data.error as Record<string, unknown> | undefined;
        } else if (event === 'run.cancelled') {
          terminalStatus = 'cancelled';
        } else if (event === 'run.timed_out') {
          terminalStatus = 'timed_out';
          finalOutput = data.error as Record<string, unknown> | undefined;
        } else if (event === 'run.expired') {
          terminalStatus = 'expired';
        }
      });

      let finalRun: { status: string; output?: Record<string, unknown>; error?: Record<string, unknown> } | null = null;
      if (!terminalStatus) {
        for (let attempt = 0; attempt < 5; attempt += 1) {
          await new Promise((resolve) => window.setTimeout(resolve, 1200));
          finalRun = await customerApi.getRun(queued.run.id);
          if (['succeeded', 'failed', 'cancelled', 'timed_out', 'expired'].includes(finalRun.status)) break;
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
          message.id === assistantId ? { ...message, text: outputText, citations, activity: [...lifecycleActivity], runStatus: 'succeeded' } : message,
        ));
      } else if (terminalStatus === 'cancelled') {
        setMessages((previous) => previous.map((message) =>
          message.id === assistantId ? { ...message, text: streamedText || 'Proses dihentikan sesuai permintaan.', source: 'Agent Runtime · cancelled', runStatus: 'cancelled' } : message,
        ));
      } else if (terminalStatus === 'failed') {
        setMessages((previous) => previous.map((message) =>
          message.id === assistantId ? { ...message, text: streamedText || 'Agent Run gagal. Anda dapat menjalankan ulang dari pesan ini.', source: 'Agent Runtime · failed', runStatus: 'failed' } : message,
        ));
      } else if (terminalStatus === 'timed_out') {
        setMessages((previous) => previous.map((message) =>
          message.id === assistantId
            ? { ...message, text: streamedText || 'Agent melewati batas waktu eksekusi. Anda dapat menjalankan ulang permintaan ini.', source: 'Agent Runtime · timed_out', runStatus: 'timed_out' }
            : message,
        ));
      } else if (terminalStatus === 'expired') {
        setMessages((previous) => previous.map((message) =>
          message.id === assistantId
            ? { ...message, text: streamedText || 'Sesi Agent telah kedaluwarsa. Anda dapat menjalankan ulang permintaan ini.', source: 'Agent Runtime · expired', runStatus: 'expired' }
            : message,
        ));
      } else {
        setMessages((previous) => previous.map((message) =>
          message.id === assistantId
            ? { ...message, text: streamedText || 'Run masih diproses. Periksa statusnya pada riwayat tugas.', source: `Agent Runtime · ${terminalStatus}`, runStatus: terminalStatus }
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
  }, [inputText, pendingAttachments, isLoading, isRestoringConversation, conversationId, showToast, initialAgentKey, selectedWorkspaceId, workspaceLoading]);

  const handleRetryRun = useCallback(async (sourceRunId: string) => {
    if (retryingRunId || isLoading) return;
    setRetryingRunId(sourceRunId);
    setIsLoading(true);
    let assistantId = crypto.randomUUID();
    try {
      const queued = await customerApi.retryRun(sourceRunId, crypto.randomUUID());
      const userText = typeof queued.message?.content === 'string' ? queued.message.content : 'Menjalankan ulang permintaan sebelumnya.';
      setMessages((previous) => [...previous,
        {
          id: queued.message?.id || crypto.randomUUID(),
          sender: 'user',
          text: userText,
          time: timeLabel(),
        },
        {
          id: assistantId,
          sender: 'assistant',
          text: '',
          time: timeLabel(),
          source: 'MoreAI Agent Runtime · retry',
          runId: queued.run.id,
          runStatus: queued.run.status,
        },
      ]);
      setActiveRunId(queued.run.id);
      let outputText = '';
      let terminalStatus = queued.run.status;
      await moreAiApiStream(customerApi.streamRun(queued.run.id), ({ event, data }) => {
        const payload = data.payload && typeof data.payload === 'object'
          ? data.payload as Record<string, unknown> : data;
        if (event === 'run.progress' || event === 'worker.checkpoint') {
          const checkpoint = (data.checkpoint || payload.checkpoint) as Record<string, unknown> | undefined;
          if (typeof checkpoint?.text === 'string') {
            outputText = checkpoint.text;
            setMessages((previous) => previous.map((message) =>
              message.id === assistantId ? { ...message, text: outputText } : message,
            ));
          }
        } else if (event === 'run.completed') {
          terminalStatus = 'succeeded';
          const output = data.output as Record<string, unknown> | undefined;
          outputText = typeof output?.text === 'string' ? output.text : typeof output?.content === 'string' ? output.content : outputText;
        } else if (['run.failed', 'run.cancelled', 'run.timed_out', 'run.expired'].includes(event)) {
          terminalStatus = event.replace('run.', '');
        }
      });
      const latest = await customerApi.getRun(queued.run.id);
      terminalStatus = latest.status || terminalStatus;
      const output = latest.output as Record<string, unknown> | undefined;
      outputText = typeof output?.text === 'string' ? output.text : typeof output?.content === 'string' ? output.content : outputText;
      setMessages((previous) => previous.map((message) => message.id === assistantId ? {
        ...message,
        text: outputText || (terminalStatus === 'succeeded' ? 'Agent menyelesaikan permintaan.' : 'Agent Run ' + terminalStatus + '.'),
        runStatus: terminalStatus,
        source: 'MoreAI Agent Runtime · ' + terminalStatus,
      } : message));
      showToast(terminalStatus === 'succeeded' ? 'Permintaan berhasil dijalankan ulang.' : 'Retry berakhir dengan status ' + terminalStatus + '.', terminalStatus === 'succeeded' ? 'success' : 'info');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Retry Agent Run gagal.';
      setMessages((previous) => [...previous, {
        id: assistantId, sender: 'assistant', text: message, time: timeLabel(),
        source: 'MoreAI API · retry gagal',
      }]);
      showToast(message, 'error');
    } finally {
      setActiveRunId(null);
      setRetryingRunId(null);
      setIsLoading(false);
    }
  }, [retryingRunId, isLoading, showToast]);

  const handleCancelRun = useCallback(async () => {
    if (!activeRunId || isCancelling) return;
    setIsCancelling(true);
    try {
      const result = await customerApi.cancelRun(activeRunId);
      if (result.status === 'cancelled') {
        showToast('Agent Run berhasil dibatalkan.', 'success');
      } else if (result.status === 'cancel_requested') {
        showToast('Permintaan penghentian diterima worker. Proses akan berhenti pada checkpoint aman.', 'success');
      } else {
        showToast('Agent Run sudah berstatus ' + result.status + '. Tidak ada permintaan penghentian baru.', 'info');
      }
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
        {olderMessagesCursor && (
          <div className="mx-auto max-w-sm space-y-2 text-center">
            <button type="button" onClick={() => void loadOlderMessages()} disabled={loadingOlderMessages}
              className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 disabled:opacity-50">
              {loadingOlderMessages ? 'Memuat pesan sebelumnya…' : 'Muat pesan sebelumnya'}
            </button>
            {messageHistoryError && <p role="alert" className="text-xs text-amber-800">{messageHistoryError}</p>}
          </div>
        )}
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
              {message.attachments && message.attachments.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {message.attachments.map((attachment) => (
                    <span key={attachment.id} className={`inline-flex max-w-full items-center gap-1 rounded-lg px-2 py-1 text-[10px] ${message.sender === 'user' ? 'bg-red-500 text-red-50' : 'bg-slate-100 text-slate-600'}`}>
                      <Paperclip className="h-3 w-3 shrink-0" />
                      <span className="max-w-40 truncate">{attachment.filename}</span>
                    </span>
                  ))}
                </div>
              )}
              <div className={`mt-2 flex items-center justify-between gap-4 text-[10px] ${message.sender === 'user' ? 'text-red-100' : 'text-slate-400'}`}>
                <span>{message.source ?? (message.sender === 'user' ? 'Anda' : 'MoreAI')}</span>
                <span>{message.time}</span>
              </div>
              {message.sender === 'assistant' && message.activity && message.activity.length > 0 && (
                <details className="mt-3 border-t border-slate-100 pt-2">
                  <summary className="cursor-pointer text-[10px] font-semibold uppercase tracking-wide text-slate-400">
                    Aktivitas Agent · {message.activity.length} event
                  </summary>
                  <ol className="mt-2 space-y-1.5">
                    {message.activity.map((activity) => (
                      <li key={activity.id} className="rounded-lg bg-slate-50 px-2.5 py-2">
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-[11px] font-medium text-slate-700">#{activity.sequence} · {activity.label}</span>
                          {activity.status && <span className="text-[10px] text-slate-500">{activity.status}</span>}
                        </div>
                        {(activity.tool || activity.phase || activity.progress !== undefined || activity.checkpoint_key) && (
                          <p className="mt-0.5 text-[10px] text-slate-500">
                            {[activity.tool ? 'Tool: ' + activity.tool : '', activity.phase, activity.progress !== undefined ? activity.progress + '%' : '', activity.checkpoint_key ? 'Checkpoint: ' + activity.checkpoint_key : ''].filter(Boolean).join(' · ')}
                          </p>
                        )}
                      </li>
                    ))}
                  </ol>
                </details>
              )}
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
              {message.sender === 'assistant' && message.runId && ['failed', 'cancelled', 'timed_out', 'expired'].includes(message.runStatus || '') && (
                <button type="button" onClick={() => void handleRetryRun(message.runId as string)}
                  disabled={isLoading || retryingRunId !== null}
                  className="mt-2 ml-3 inline-flex items-center gap-1 rounded-lg bg-red-50 px-2.5 py-1.5 text-xs font-semibold text-red-700 disabled:opacity-50">
                  <Sparkles className="h-3 w-3" /> {retryingRunId === message.runId ? 'Menjalankan ulang…' : 'Regenerate'}
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
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <label htmlFor="chat-workspace" className="text-[10px] font-semibold text-slate-500">Simpan percakapan di</label>
          <select
            id="chat-workspace"
            value={selectedWorkspaceId}
            onChange={(event) => setSelectedWorkspaceId(event.target.value)}
            disabled={!!conversationId || isLoading || isRestoringConversation || workspaceLoading}
            className="min-w-0 max-w-full rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-[11px] text-slate-700 disabled:bg-slate-50 disabled:opacity-70"
          >
            <option value="">Percakapan pribadi</option>
            {selectedWorkspaceId && !workspaces.some((workspace) => workspace.id === selectedWorkspaceId) && (
              <option value={selectedWorkspaceId}>Workspace percakapan tersimpan</option>
            )}
            {workspaces.map((workspace) => <option key={workspace.id} value={workspace.id}>{workspace.name}</option>)}
          </select>
          {workspaceCursor && !conversationId && (
            <button type="button" onClick={() => void loadMoreWorkspaces()} disabled={workspaceLoadingMore}
              className="text-[10px] font-semibold text-red-600 disabled:opacity-50">
              {workspaceLoadingMore ? 'Memuat…' : 'Muat lainnya'}
            </button>
          )}
        </div>
        {workspaceLoading && <p role="status" className="mb-2 text-[10px] text-slate-400">Memuat pilihan workspace…</p>}
        {workspaceLoadError && <p role="alert" className="mb-2 text-[10px] text-amber-700">Workspace tidak tersedia: {workspaceLoadError}. Percakapan baru tetap dapat disimpan sebagai percakapan pribadi.</p>}
        {pendingAttachments.length > 0 && (
          <div className="mb-2 flex flex-wrap gap-2">
            {pendingAttachments.map((file, index) => (
              <span key={file.name + ':' + file.size + ':' + index} className="inline-flex max-w-full items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs text-slate-700">
                <Paperclip className="h-3 w-3 shrink-0 text-slate-400" />
                <span className="max-w-48 truncate">{file.name}</span>
                <button type="button" onClick={() => setPendingAttachments((items) => items.filter((_, itemIndex) => itemIndex !== index))} disabled={isLoading} aria-label={'Hapus lampiran ' + file.name} className="rounded p-0.5 text-slate-400 hover:bg-slate-200 hover:text-slate-700">
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
          </div>
        )}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".txt,.md,.csv,.json,.pdf,.jpg,.jpeg,.png,.webp,text/plain,text/markdown,text/csv,application/json,application/pdf,image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={(event) => {
            const incoming = Array.from(event.target.files ?? []);
            event.currentTarget.value = '';
            const allowed = new Set(['text/plain', 'text/markdown', 'text/csv', 'application/json', 'application/pdf', 'image/jpeg', 'image/png', 'image/webp']);
            const accepted = incoming.filter((file) => {
              if (!allowed.has(file.type) || file.size < 1 || file.size > 2_000_000 || !/^[A-Za-z0-9][A-Za-z0-9._ -]{0,179}$/.test(file.name)) {
                showToast('Lampiran harus berupa TXT, MD, CSV, JSON, PDF, JPG, PNG, atau WebP dengan ukuran maksimal 2 MB.', 'error');
                return false;
              }
              return true;
            });
            setPendingAttachments((current) => {
              const combined = [...current, ...accepted];
              if (combined.length > 10 || combined.reduce((sum, file) => sum + file.size, 0) > 10_000_000) {
                showToast('Maksimal 10 lampiran dengan total ukuran 10 MB.', 'error');
                return current;
              }
              return combined;
            });
          }}
        />
        <div className="flex items-end gap-2 rounded-2xl border border-slate-200 bg-slate-50 p-2 focus-within:border-red-300">
          <button type="button" onClick={() => fileInputRef.current?.click()} disabled={isLoading || isRestoringConversation || pendingAttachments.length >= 10} aria-label="Tambah lampiran" className="rounded-xl p-2 text-slate-500 transition hover:bg-slate-200 disabled:opacity-40">
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
          <button type="submit" disabled={isLoading || isRestoringConversation || workspaceLoading || (!inputText.trim() && pendingAttachments.length === 0)} aria-label="Kirim pesan" className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-red-600 text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:bg-slate-300">
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </button>
        </div>
        <p className="mt-2 text-center text-[10px] text-slate-400">Respons diproses melalui backend MoreAI. Ketersediaan bergantung pada konfigurasi agent dan provider.</p>
      </form>
    </section>
  );
};
