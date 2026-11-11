import { createSupabaseBrowserClient } from '@/lib/supabase/client';

const API_BASE_URL = (process.env.NEXT_PUBLIC_MOREAI_API_URL || '').replace(/\/$/, '');
// Optional role-specific origins. When omitted, both role APIs share the FastAPI origin
// and remain isolated by their server-side /customer and /partner route namespaces.
const CUSTOMER_API_BASE_URL = (process.env.NEXT_PUBLIC_MOREAI_CUSTOMER_API_URL || API_BASE_URL).replace(/\/$/, '');
const PARTNER_API_BASE_URL = (process.env.NEXT_PUBLIC_MOREAI_PARTNER_API_URL || API_BASE_URL).replace(/\/$/, '');

async function moreAiApiAt<T>(baseUrl: string, path: string, init: RequestInit = {}): Promise<T> {
  if (!baseUrl) {
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
  const response = await fetch(baseUrl + path, {
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

export function moreAiApi<T>(path: string, init: RequestInit = {}): Promise<T> {
  return moreAiApiAt(API_BASE_URL, path, init);
}

export function moreAiCustomerApi<T>(path: string, init: RequestInit = {}): Promise<T> {
  return moreAiApiAt(CUSTOMER_API_BASE_URL, path, init);
}

export function moreAiPartnerApi<T>(path: string, init: RequestInit = {}): Promise<T> {
  return moreAiApiAt(PARTNER_API_BASE_URL, path, init);
}

export type MoreAiStreamEvent = {
  event: string;
  data: Record<string, unknown>;
};

export async function moreAiApiStream(
  path: string,
  onEvent: (event: MoreAiStreamEvent) => void,
): Promise<void> {
  if (!CUSTOMER_API_BASE_URL) {
    throw new Error('Customer API belum dikonfigurasi. Isi NEXT_PUBLIC_MOREAI_CUSTOMER_API_URL atau NEXT_PUBLIC_MOREAI_API_URL.');
  }
  const supabase = createSupabaseBrowserClient();
  const { data, error } = await supabase.auth.getSession();
  if (error || !data.session?.access_token) {
    throw new Error('Sesi login tidak ditemukan. Silakan masuk kembali.');
  }
  const response = await fetch(CUSTOMER_API_BASE_URL + path, {
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
  created_at?: string;
  input?: Record<string, unknown>;
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

export type PartnerTenantOption = {
  tenant: PartnerContext['tenant'];
  principal_role: string;
  location_scope: string | null;
};

export const customerApi = {
  context: () => moreAiCustomerApi<{ principal: { user_id: string; role: string }; tenant: null }>('/api/v1/customer/context'),
  conversations: () => moreAiCustomerApi<CustomerConversation[]>('/api/v1/customer/conversations'),
  createConversation: (title: string) => moreAiCustomerApi<{ id: string }>('/api/v1/customer/conversations', {
    method: 'POST', body: JSON.stringify({ title }),
  }),
  sendMessage: (conversationId: string, content: string, idempotencyKey: string, agentKey: 'manus' | 'planning' = 'manus') =>
    moreAiCustomerApi<{ run: { id: string; status: string } }>(`/api/v1/customer/conversations/${conversationId}/messages`, {
      method: 'POST',
      headers: { 'Idempotency-Key': idempotencyKey },
      body: JSON.stringify({ content, agent_key: agentKey }),
    }),
  agentRuns: () => moreAiCustomerApi<CustomerAgentRun[]>('/api/v1/customer/agent-runs'),
  getRun: (runId: string) => moreAiCustomerApi<CustomerAgentRun>(`/api/v1/customer/agent-runs/${runId}`),
  streamRun: (runId: string) => `/api/v1/customer/agent-runs/${runId}/stream?wait_seconds=30`,
};

export const partnerApi = {
  tenants: () => moreAiPartnerApi<PartnerTenantOption[]>('/api/v1/partner/tenants'),
  context: (partnerId?: string) => moreAiPartnerApi<PartnerContext>(
    '/api/v1/partner/context' + (partnerId ? `?partner_id=${encodeURIComponent(partnerId)}` : ''),
  ),
  locations: (partnerId?: string) => moreAiPartnerApi<PartnerLocationRecord[]>(
    '/api/v1/partner/locations' + (partnerId ? `?partner_id=${encodeURIComponent(partnerId)}` : ''),
  ),
  members: (partnerId?: string) => moreAiPartnerApi<Array<Record<string, unknown>>>(
    '/api/v1/partner/members' + (partnerId ? `?partner_id=${encodeURIComponent(partnerId)}` : ''),
  ),
};

export type CustomerToolApproval = {
  id: string;
  run_id: string;
  tool_key: string;
  summary: string;
  status: 'pending' | 'approved' | 'denied' | 'expired' | 'consumed';
  requested_at: string;
  expires_at: string;
  decided_at: string | null;
  consumed_at: string | null;
};

export const customerToolApprovalApi = {
  list: () => moreAiCustomerApi<CustomerToolApproval[]>('/api/v1/customer/tool-approvals'),
  request: (input: { run_id: string; tool_key: 'bash' | 'python_execute' | 'browser' | 'file_read' | 'file_write' | 'file_edit'; arguments_hash: string; summary: string }) =>
    moreAiCustomerApi<{ id: string; status: 'pending' }>('/api/v1/customer/tool-approvals', {
      method: 'POST', body: JSON.stringify(input),
    }),
  decide: (approvalId: string, decision: 'approved' | 'denied') =>
    moreAiCustomerApi<{ id: string; status: string }>(`/api/v1/customer/tool-approvals/${approvalId}/decision`, {
      method: 'POST', body: JSON.stringify({ decision }),
    }),
};
