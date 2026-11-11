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


export type CustomerProfile = {
  id: string;
  display_name: string | null;
  avatar_path: string | null;
  locale: string;
  timezone: string;
};

export const profileApi = {
  get: () => moreAiApi<{ user: { id: string; email?: string }; profile: CustomerProfile | null }>('/api/v1/me'),
  update: (payload: Partial<Pick<CustomerProfile, 'display_name' | 'avatar_path' | 'locale' | 'timezone'>>) =>
    moreAiApi<{ user: { id: string; email?: string }; profile: CustomerProfile }>('/api/v1/me/profile', {
      method: 'PATCH', body: JSON.stringify(payload),
    }),
};

export type CustomerConversation = {
  id: string;
  title: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type CustomerWorkflowStep = {
  id: string;
  sequence: number;
  step_key: string;
  status: 'pending' | 'running' | 'waiting_approval' | 'succeeded' | 'failed' | 'skipped' | 'cancelled' | string;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
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

export type CustomerWallet = {
  id: string;
  currency: string;
  balance: string | number;
  status: string;
  created_at: string;
  updated_at: string;
};

export type CustomerLedgerEntry = {
  id: string;
  wallet_id: string;
  entry_type: string;
  amount: string | number;
  balance_after: string | number;
  reference_type: string | null;
  reference_id: string | null;
  description: string | null;
  created_at: string;
};

export type CustomerUsageRecord = {
  id: string;
  run_id: string | null;
  provider_key: string;
  model_key: string;
  input_tokens: number;
  output_tokens: number;
  estimated_cost: string | number;
  actual_cost: string | number | null;
  status: string;
  latency_ms: number | null;
  created_at: string;
};

export type CustomerEntitlement = {
  id: string;
  entitlement_key: string;
  source_type: string;
  status: string;
  starts_at: string;
  expires_at: string | null;
  metadata: Record<string, unknown>;
};

export type CustomerQuota = {
  id: string;
  metric_key: string;
  limit_value: string | number;
  window_seconds: number;
  usage: { used_value: string | number; window_start: string; updated_at: string } | null;
};


export type CustomerArtifact = {
  id: string;
  storage_path: string;
  mime_type: string | null;
  size_bytes: number | null;
  checksum_sha256: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
};

export const artifactApi = {
  list: () => moreAiApi<CustomerArtifact[]>('/api/v1/artifacts'),
  upload: (filename: string, content: Blob, mimeType = content.type || 'application/octet-stream') =>
    moreAiApi<CustomerArtifact>('/api/v1/artifacts', {
      method: 'POST',
      headers: { 'X-Filename': filename, 'Content-Type': mimeType },
      body: content,
    }),
  signedDownload: (artifactId: string) =>
    moreAiApi<{ artifact_id: string; url: string; expires_in: number }>(
      `/api/v1/artifacts/${artifactId}/signed-download`,
      { method: 'POST' },
    ),
};

export const customerApi = {
  context: () => moreAiCustomerApi<{ principal: { user_id: string; role: string }; tenant: null }>('/api/v1/customer/context'),
  conversations: () => moreAiCustomerApi<CustomerConversation[]>('/api/v1/customer/conversations'),
  getConversation: (conversationId: string) => moreAiCustomerApi<{
    conversation: CustomerConversation;
    messages: Array<{ id: string; role: string; content: string; model_key: string | null; run_id: string | null; created_at: string }>;
  }>(`/api/v1/customer/conversations/${conversationId}`),
  createConversation: (title: string) => moreAiCustomerApi<{ id: string }>('/api/v1/customer/conversations', {
    method: 'POST', body: JSON.stringify({ title }),
  }),
  sendMessage: (conversationId: string, content: string, idempotencyKey: string, agentKey: 'manus' | 'planning' = 'manus') =>
    moreAiCustomerApi<{ run: { id: string; status: string } }>(`/api/v1/customer/conversations/${conversationId}/messages`, {
      method: 'POST',
      headers: { 'Idempotency-Key': idempotencyKey },
      body: JSON.stringify({ content, agent_key: agentKey }),
    }),
  agentRuns: () => moreAiApi<CustomerAgentRun[]>('/api/v1/agent-runs'),
  getRun: (runId: string) => moreAiApi<CustomerAgentRun>(`/api/v1/agent-runs/${runId}`),
  cancelRun: (runId: string) => moreAiCustomerApi<{ run_id: string; status: string }>(`/api/v1/agent-runs/${runId}/cancel`, {
    method: 'POST',
  }),
  getRunSteps: (runId: string) => moreAiApi<CustomerWorkflowStep[]>(`/api/v1/agent-runs/${runId}/steps`),
  getRunEvents: (runId: string, after = 0) => moreAiApi<Array<{
    id: string; event_type: string; sequence: number; payload: Record<string, unknown>; created_at: string;
  }>>(`/api/v1/agent-runs/${runId}/events?after=${Math.max(0, after)}`),
  streamRun: (runId: string) => `/api/v1/agent-runs/${runId}/stream?wait_seconds=30`,
  wallets: () => moreAiCustomerApi<{ wallets: CustomerWallet[] }>('/api/v1/customer/wallet'),
  ledger: (limit = 50, before?: string) => moreAiCustomerApi<CustomerLedgerEntry[]>(`/api/v1/customer/wallet/ledger?limit=${limit}${before ? `&before=${encodeURIComponent(before)}` : ''}`),
  usage: (limit = 50, before?: string) => moreAiCustomerApi<CustomerUsageRecord[]>(`/api/v1/customer/usage?limit=${limit}${before ? `&before=${encodeURIComponent(before)}` : ''}`),
  entitlements: () => moreAiCustomerApi<CustomerEntitlement[]>('/api/v1/customer/entitlements'),
  quotas: () => moreAiCustomerApi<CustomerQuota[]>('/api/v1/customer/quotas'),
  redeemAccessCode: (code: string, networkId: string, verificationSessionId: string, idempotencyKey: string) =>
    moreAiCustomerApi<Record<string, unknown>>('/api/v1/customer/access-codes/redeem', { method: 'POST', headers: { 'Idempotency-Key': idempotencyKey }, body: JSON.stringify({ code, network_id: networkId, verification_session_id: verificationSessionId }) }),
};

export type PartnerCampaign = {
  id: string; partner_id: string; location_id: string | null; name: string; status: string;
  starts_at: string | null; ends_at: string | null; budget: number | string | null;
  config: Record<string, unknown>; created_at: string; updated_at: string;
};
export type PartnerMember = {
  id: string; partner_id: string; user_id: string; role_key: string;
  location_id: string | null; status: string; created_at: string;
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
  sessions: (partnerId?: string) => moreAiPartnerApi<Array<Record<string, unknown>>>(
    '/api/v1/partner/sessions' + (partnerId ? `?partner_id=${encodeURIComponent(partnerId)}` : ''),
  ),
  campaigns: (partnerId?: string) => moreAiPartnerApi<Array<Record<string, unknown>>>(
    '/api/v1/partner/campaigns' + (partnerId ? `?partner_id=${encodeURIComponent(partnerId)}` : ''),
  ),
  createLocation: (payload: { name: string; address?: Record<string, unknown>; latitude?: number; longitude?: number; timezone?: string }, partnerId?: string) =>
    moreAiPartnerApi<PartnerLocationRecord>('/api/v1/partner/locations' + (partnerId ? `?partner_id=${encodeURIComponent(partnerId)}` : ''), { method: 'POST', body: JSON.stringify(payload) }),
  createCampaign: (payload: { name: string; location_id?: string | null; starts_at?: string | null; ends_at?: string | null; budget?: number | null; config?: Record<string, unknown> }, partnerId?: string) =>
    moreAiPartnerApi<PartnerCampaign>('/api/v1/partner/campaigns' + (partnerId ? `?partner_id=${encodeURIComponent(partnerId)}` : ''), { method: 'POST', body: JSON.stringify(payload) }),
  updateCampaign: (campaignId: string, payload: Partial<Pick<PartnerCampaign, 'name' | 'status' | 'starts_at' | 'ends_at' | 'budget' | 'config'>>, partnerId?: string) =>
    moreAiPartnerApi<PartnerCampaign>(`/api/v1/partner/campaigns/${campaignId}` + (partnerId ? `?partner_id=${encodeURIComponent(partnerId)}` : ''), { method: 'PATCH', body: JSON.stringify(payload) }),
  inviteMember: (payload: { user_id: string; role_key: 'partner_admin' | 'location_manager' | 'partner_staff' | 'partner_analyst'; location_id?: string | null }, partnerId?: string) =>
    moreAiPartnerApi<PartnerMember>('/api/v1/partner/members' + (partnerId ? `?partner_id=${encodeURIComponent(partnerId)}` : ''), { method: 'POST', body: JSON.stringify(payload) }),
  accessCodes: (partnerId?: string) => moreAiPartnerApi<Array<Record<string, unknown>>>('/api/v1/partner/access-codes' + (partnerId ? `?partner_id=${encodeURIComponent(partnerId)}` : '')),
  accessCodeRedemptions: (partnerId?: string) => moreAiPartnerApi<Array<Record<string, unknown>>>('/api/v1/partner/access-code-redemptions' + (partnerId ? `?partner_id=${encodeURIComponent(partnerId)}` : '')),
  networks: (partnerId?: string) => moreAiPartnerApi<Array<Record<string, unknown>>>('/api/v1/partner/networks' + (partnerId ? `?partner_id=${encodeURIComponent(partnerId)}` : '')),
  createNetwork: (payload: { location_id: string; provider_id?: string | null; name: string; ssid_label?: string | null; gateway_type: string; gateway_network_ref?: string | null }, partnerId?: string) =>
    moreAiPartnerApi<Record<string, unknown>>('/api/v1/partner/networks' + (partnerId ? `?partner_id=${encodeURIComponent(partnerId)}` : ''), { method: 'POST', body: JSON.stringify(payload) }),
  verificationConfigs: (networkId: string, partnerId?: string) =>
    moreAiPartnerApi<Array<Record<string, unknown>>>(`/api/v1/partner/networks/${networkId}/verification-configs` + (partnerId ? `?partner_id=${encodeURIComponent(partnerId)}` : '')),
  configureVerification: (networkId: string, payload: { method_key: 'gps' | 'mikrotik_hotspot' | 'radius' | 'gateway' | 'isp_api'; config_public?: Record<string, unknown>; secret_reference?: string | null; policy?: Record<string, unknown>; enabled?: boolean }, partnerId?: string) =>
    moreAiPartnerApi<Record<string, unknown>>(`/api/v1/partner/networks/${networkId}/verification-configs` + (partnerId ? `?partner_id=${encodeURIComponent(partnerId)}` : ''), { method: 'POST', body: JSON.stringify(payload) }),
  createAccessCode: (payload: { location_id?: string | null; network_id?: string | null; campaign_id?: string | null; reward_id?: string | null; expires_at: string; max_redemptions?: number }, partnerId?: string) =>
    moreAiPartnerApi<{ access_code: string; record: Record<string, unknown>; notice: string }>('/api/v1/partner/access-codes' + (partnerId ? `?partner_id=${encodeURIComponent(partnerId)}` : ''), { method: 'POST', body: JSON.stringify(payload) }),
  revokeAccessCode: (accessCodeId: string, partnerId?: string) =>
    moreAiPartnerApi<{ id: string; status: string }>(`/api/v1/partner/access-codes/${accessCodeId}/revoke` + (partnerId ? `?partner_id=${encodeURIComponent(partnerId)}` : ''), { method: 'POST' }),
  campaignRewards: (campaignId: string, partnerId?: string) => moreAiPartnerApi<Array<Record<string, unknown>>>(
    `/api/v1/partner/campaigns/${campaignId}/rewards` + (partnerId ? `?partner_id=${encodeURIComponent(partnerId)}` : ''),
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


export type CustomerNotification = {
  id: string;
  notification_type: string;
  title: string;
  body: string;
  resource_type: string | null;
  resource_id: string | null;
  action_url: string | null;
  metadata: Record<string, unknown>;
  read_at: string | null;
  created_at: string;
};

export type CustomerNotificationPreferences = {
  in_app_enabled: boolean;
  email_enabled: boolean;
  category_settings: Record<string, boolean>;
  updated_at: string | null;
};

export const notificationApi = {
  list: (unreadOnly = false, limit = 30) =>
    moreAiApi<{ items: CustomerNotification[]; limit: number }>(
      `/api/v1/notifications?unread_only=${unreadOnly}&limit=${Math.min(100, Math.max(1, limit))}`,
    ),
  preferences: () => moreAiApi<CustomerNotificationPreferences>('/api/v1/notifications/preferences'),
  updatePreferences: (payload: Partial<Omit<CustomerNotificationPreferences, 'updated_at'>>) =>
    moreAiApi<CustomerNotificationPreferences>('/api/v1/notifications/preferences', {
      method: 'PUT', body: JSON.stringify(payload),
    }),
  markRead: (notificationId: string) =>
    moreAiApi<{ id: string; read_at: string }>(`/api/v1/notifications/${notificationId}/read`, { method: 'POST' }),
  markAllRead: () => moreAiApi<{ updated: number }>('/api/v1/notifications/read-all', { method: 'POST' }),
};


export const platformAdminApi = {
  updatePartnerStatus: (partnerId: string, status: 'pending' | 'active' | 'suspended' | 'rejected' | 'closed', idempotencyKey: string) =>
    moreAiApi<{ partner_id: string; status: string; previous_status: string; updated_at: string }>(
      `/api/v1/admin/partners/${partnerId}/status`,
      { method: 'PATCH', headers: { 'Idempotency-Key': idempotencyKey }, body: JSON.stringify({ status }) },
    ),
};
