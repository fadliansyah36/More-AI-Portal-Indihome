import { createSupabaseBrowserClient } from '@/lib/supabase/client';

const API_BASE_URL = (process.env.NEXT_PUBLIC_MOREAI_API_URL || '').replace(/\/$/, '');

export async function moreAiApi<T>(path: string, init: RequestInit = {}): Promise<T> {
  if (!API_BASE_URL) {
    throw new Error('MoreAI API belum dikonfigurasi. Isi NEXT_PUBLIC_MOREAI_API_URL.');
  }
  const supabase = createSupabaseBrowserClient();
  const { data, error } = await supabase.auth.getSession();
  if (error || !data.session?.access_token) {
    throw new Error('Sesi login tidak ditemukan. Silakan masuk kembali.');
  }
  const headers = new Headers(init.headers);
  headers.set('Authorization', 'Bearer ' + data.session.access_token);
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  const response = await fetch(API_BASE_URL + path, {
    ...init,
    headers,
    cache: 'no-store',
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const message = payload?.detail || payload?.error?.message || ('MoreAI API error (' + response.status + ')');
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export type MoreAiStreamEvent = {
  event: string;
  data: Record<string, unknown>;
};

export async function moreAiApiStream(
  path: string,
  onEvent: (event: MoreAiStreamEvent) => void,
): Promise<void> {
  if (!API_BASE_URL) {
    throw new Error('MoreAI API belum dikonfigurasi. Isi NEXT_PUBLIC_MOREAI_API_URL.');
  }
  const supabase = createSupabaseBrowserClient();
  const { data, error } = await supabase.auth.getSession();
  if (error || !data.session?.access_token) {
    throw new Error('Sesi login tidak ditemukan. Silakan masuk kembali.');
  }
  const response = await fetch(API_BASE_URL + path, {
    headers: { Authorization: 'Bearer ' + data.session.access_token, Accept: 'text/event-stream' },
    cache: 'no-store',
  });
  if (!response.ok || !response.body) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail || ('MoreAI stream error (' + response.status + ')'));
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  const dispatch = (block: string) => {
    const lines = block.split(/\r?\n/);
    let event = 'message';
    const dataLines: string[] = [];
    for (const line of lines) {
      if (line.startsWith('event:')) event = line.slice(6).trim();
      if (line.startsWith('data:')) dataLines.push(line.slice(5).trim());
    }
    if (!dataLines.length) return;
    try {
      const parsed = JSON.parse(dataLines.join('\n'));
      if (parsed && typeof parsed === 'object') onEvent({ event, data: parsed as Record<string, unknown> });
    } catch {
      // Ignore malformed or partial provider events; the durable run endpoint remains authoritative.
    }
  };

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split(/\r?\n\r?\n/);
      buffer = blocks.pop() || '';
      for (const block of blocks) dispatch(block);
    }
    buffer += decoder.decode();
    if (buffer.trim()) dispatch(buffer);
  } finally {
    reader.releaseLock();
  }
}


export type CustomerConversation = {
  id: string;
  title: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type CustomerAgentRun = {
  id: string;
  conversation_id: string | null;
  status: string;
  output?: Record<string, unknown>;
  error?: Record<string, unknown>;
};

export type PartnerContext = {
  principal: { user_id: string; role: string };
  tenant: { id: string; display_name: string; legal_name: string; status: string };
  location_scope: string | null;
};

export type PartnerLocationRecord = {
  id: string;
  partner_id: string;
  name: string;
  address: unknown;
  status: string;
  created_at: string;
};

export const customerApi = {
  context: () => moreAiApi<{ principal: { user_id: string; role: string }; tenant: null }>('/api/v1/customer/context'),
  conversations: () => moreAiApi<CustomerConversation[]>('/api/v1/customer/conversations'),
  createConversation: (title: string) => moreAiApi<{ id: string }>('/api/v1/customer/conversations', {
    method: 'POST', body: JSON.stringify({ title }),
  }),
  sendMessage: (conversationId: string, content: string, idempotencyKey: string, agentKey: 'manus' | 'planning' = 'manus') =>
    moreAiApi<{ run: { id: string; status: string } }>(`/api/v1/customer/conversations/${conversationId}/messages`, {
      method: 'POST',
      headers: { 'Idempotency-Key': idempotencyKey },
      body: JSON.stringify({ content, agent_key: agentKey }),
    }),
  getRun: (runId: string) => moreAiApi<CustomerAgentRun>(`/api/v1/customer/agent-runs/${runId}`),
  streamRun: (runId: string) => `/api/v1/customer/agent-runs/${runId}/stream?wait_seconds=30`,
};

export const partnerApi = {
  context: (partnerId?: string) => moreAiApi<PartnerContext>(
    '/api/v1/partner/context' + (partnerId ? `?partner_id=${encodeURIComponent(partnerId)}` : ''),
  ),
  locations: (partnerId?: string) => moreAiApi<PartnerLocationRecord[]>(
    '/api/v1/partner/locations' + (partnerId ? `?partner_id=${encodeURIComponent(partnerId)}` : ''),
  ),
  members: (partnerId?: string) => moreAiApi<Array<Record<string, unknown>>>(
    '/api/v1/partner/members' + (partnerId ? `?partner_id=${encodeURIComponent(partnerId)}` : ''),
  ),
};
