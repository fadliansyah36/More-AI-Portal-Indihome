import { createSupabaseBrowserClient } from '@/lib/supabase/client';

const API_BASE_URL = (process.env.NEXT_PUBLIC_MOREAI_API_URL || '').replace(/\/$/, '');
// Optional role-specific origins. When omitted, both role APIs share the FastAPI origin
// and remain isolated by their server-side /customer and /partner route namespaces.
const CUSTOMER_API_BASE_URL = (process.env.NEXT_PUBLIC_MOREAI_CUSTOMER_API_URL || API_BASE_URL).replace(/\/$/, '');
const PARTNER_API_BASE_URL = (process.env.NEXT_PUBLIC_MOREAI_PARTNER_API_URL || API_BASE_URL).replace(/\/$/, '');
const VERIFIED_API_FALLBACK_ORIGIN = 'https://more-ai-api.vercel.app';

/** Retry only safe reads on the verified production alias; never replay mutations. */
async function fetchMoreAiApi(
  baseUrl: string,
  path: string,
  init: RequestInit,
  headers: Headers,
  accessToken: string,
): Promise<Response> {
  const method = (init.method || 'GET').toUpperCase();
  const requestHeaders = new Headers(headers);
  requestHeaders.set('Authorization', 'Bearer ' + accessToken);
  const requestInit: RequestInit = { ...init, headers: requestHeaders, cache: 'no-store' };
  try {
    return await fetch(baseUrl + path, requestInit);
  } catch (error) {
    if (baseUrl !== 'https://more-ai-api-more-ai.vercel.app' || !['GET', 'HEAD'].includes(method)) {
      if (error instanceof TypeError) {
        throw new Error('Layanan API MoreAI tidak dapat dijangkau. Periksa koneksi, domain API, dan konfigurasi CORS.');
      }
      throw error;
    }
    try {
      return await fetch(VERIFIED_API_FALLBACK_ORIGIN + path, requestInit);
    } catch {
      throw new Error('Layanan API MoreAI tidak dapat dijangkau melalui domain utama maupun alias cadangan. Periksa koneksi dan deployment FastAPI.');
    }
  }
}


async function moreAiApiAt<T>(baseUrl: string, path: string, init: RequestInit = {}): Promise<T> {
  if (!baseUrl) {
    throw new Error('MoreAI API belum dikonfigurasi. Isi NEXT_PUBLIC_MOREAI_API_URL.');
  }
  const supabase = createSupabaseBrowserClient();
  const headers = new Headers(init.headers);
  if (init.body && !(init.body instanceof Blob) && !(init.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  // Supabase may return a locally cached token while its refresh is racing
  // an API request. Retry once after an API 401; never retry 403 or business
  // errors, so mutations cannot be duplicated by this recovery path.
  const sessionResult = await supabase.auth.getSession();
  if (sessionResult.error || !sessionResult.data.session?.access_token) {
    throw new Error('Sesi login tidak ditemukan. Silakan masuk kembali.');
  }
  let accessToken = sessionResult.data.session.access_token;
  const send = () => fetchMoreAiApi(baseUrl, path, init, headers, accessToken);

  let response = await send();
  if (response.status === 401) {
    const refreshed = await supabase.auth.refreshSession();
    if (refreshed.error || !refreshed.data.session?.access_token) {
      await supabase.auth.signOut({ scope: 'local' });
      throw new Error('Sesi login telah berakhir. Silakan masuk kembali.');
    }
    accessToken = refreshed.data.session.access_token;
    response = await send();
  }
  if (response.status === 401) {
    await supabase.auth.signOut({ scope: 'local' });
    throw new Error('Sesi login tidak valid. Silakan masuk kembali.');
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const detail = payload?.detail;
    const message = (typeof detail === 'string' ? detail : detail?.message)
      || payload?.error?.message
      || ('MoreAI API error (' + response.status + ')');
    const code = typeof detail === 'object' ? detail?.code : payload?.error?.code;
    const correlationId = payload?.error?.correlation_id;
    const error = new Error(message);
    if (typeof code === 'string') Object.assign(error, { code });
    if (typeof correlationId === 'string') Object.assign(error, { correlationId });
    throw error;
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

/** Authenticated raw response for binary transfer and streaming contracts. */
export async function moreAiCustomerFetch(path: string, init: RequestInit = {}): Promise<Response> {
  if (!CUSTOMER_API_BASE_URL) {
    throw new Error('Customer API belum dikonfigurasi. Isi NEXT_PUBLIC_MOREAI_CUSTOMER_API_URL atau NEXT_PUBLIC_MOREAI_API_URL.');
  }
  const supabase = createSupabaseBrowserClient();
  const headers = new Headers(init.headers);
  const session = await supabase.auth.getSession();
  if (session.error || !session.data.session?.access_token) {
    throw new Error('Sesi login tidak ditemukan. Silakan masuk kembali.');
  }
  let token = session.data.session.access_token;
  const send = () => fetchMoreAiApi(CUSTOMER_API_BASE_URL, path, init, headers, token);
  let response = await send();
  if (response.status === 401) {
    const refreshed = await supabase.auth.refreshSession();
    if (refreshed.error || !refreshed.data.session?.access_token) {
      await supabase.auth.signOut({ scope: 'local' });
      throw new Error('Sesi login telah berakhir. Silakan masuk kembali.');
    }
    token = refreshed.data.session.access_token;
    response = await send();
  }
  if (response.status === 401) {
    await supabase.auth.signOut({ scope: 'local' });
    throw new Error('Sesi login tidak valid. Silakan masuk kembali.');
  }
  if (!response.ok) {
    const payload = await response.clone().json().catch(() => null);
    throw new Error(payload?.error?.message || payload?.detail || ('MoreAI API error (' + response.status + ')'));
  }
  return response;
}

export type MoreAiStreamEvent = {
  id?: string;
  event: string;
  data: Record<string, unknown>;
};

export type MoreAiStreamOptions = {
  /** Last durably processed event sequence; used when opening or recovering a stream. */
  after?: number;
  /** Abort the active request and any reconnect delay. */
  signal?: AbortSignal;
  /** Maximum reconnect attempts after a clean timeout or transient transport failure. */
  maxReconnects?: number;
  /** Initial reconnect delay; exponential backoff is capped at 8 seconds. */
  reconnectDelayMs?: number;
};

export async function moreAiApiStream(
  path: string,
  onEvent: (event: MoreAiStreamEvent) => void,
  options: MoreAiStreamOptions = {},
): Promise<void> {
  if (!CUSTOMER_API_BASE_URL) {
    throw new Error('Customer API belum dikonfigurasi. Isi NEXT_PUBLIC_MOREAI_CUSTOMER_API_URL atau NEXT_PUBLIC_MOREAI_API_URL.');
  }

  const maxReconnects = Math.max(0, Math.min(20, options.maxReconnects ?? 5));
  const initialDelay = Math.max(100, Math.min(8000, options.reconnectDelayMs ?? 500));
  let cursor = Number.isSafeInteger(options.after) && (options.after ?? 0) >= 0 ? options.after ?? 0 : 0;
  let reconnects = 0;
  let terminal = false;

  const waitForRetry = async (delay: number) => {
    if (options.signal?.aborted) throw new DOMException('Stream aborted', 'AbortError');
    await new Promise<void>((resolve, reject) => {
      const timer = setTimeout(() => {
        options.signal?.removeEventListener('abort', abort);
        resolve();
      }, delay);
      const abort = () => {
        clearTimeout(timer);
        options.signal?.removeEventListener('abort', abort);
        reject(new DOMException('Stream aborted', 'AbortError'));
      };
      options.signal?.addEventListener('abort', abort, { once: true });
    });
  };

  while (!terminal) {
    if (options.signal?.aborted) throw new DOMException('Stream aborted', 'AbortError');

    // Refresh the Supabase Auth session on every reconnect. Never persist or expose
    // the bearer token in the stream cursor or event payload.
    const supabase = createSupabaseBrowserClient();
    const { data, error } = await supabase.auth.getSession();
    if (error || !data.session?.access_token) {
      throw new Error('Sesi login tidak ditemukan. Silakan masuk kembali.');
    }

    let accessToken = data.session.access_token;
    const buildHeaders = () => {
      const headers = new Headers({
        Authorization: 'Bearer ' + accessToken,
        Accept: 'text/event-stream',
      });
      if (cursor > 0) headers.set('Last-Event-ID', String(cursor));
      return headers;
    };

    let response: Response;
    let authenticationFailed = false;
    try {
      response = await fetch(CUSTOMER_API_BASE_URL + path, {
        headers: buildHeaders(),
        cache: 'no-store',
        signal: options.signal,
      });
      if (response.status === 401) {
        const refreshed = await supabase.auth.refreshSession();
        if (refreshed.error || !refreshed.data.session?.access_token) {
          authenticationFailed = true;
          await supabase.auth.signOut({ scope: 'local' });
          throw new Error('Sesi login telah berakhir. Silakan masuk kembali.');
        }
        accessToken = refreshed.data.session.access_token;
        response = await fetch(CUSTOMER_API_BASE_URL + path, {
          headers: buildHeaders(),
          cache: 'no-store',
          signal: options.signal,
        });
      }
    } catch (error) {
      // Authentication failures are terminal; reconnecting cannot repair a
      // rejected refresh token and would only generate repeated unauthorized traffic.
      if (authenticationFailed || options.signal?.aborted) throw error;
      if (reconnects >= maxReconnects) throw error;
      reconnects += 1;
      await waitForRetry(Math.min(8000, initialDelay * (2 ** (reconnects - 1))));
      continue;
    }

    if (!response.ok || !response.body) {
      const payload = await response.json().catch(() => null);
      // Authentication/authorization and contract errors are not transient.
      if ([400, 401, 403, 404, 422].includes(response.status)) {
        if (response.status === 401) await supabase.auth.signOut({ scope: 'local' });
        throw new Error(payload?.detail || ('MoreAI stream error (' + response.status + ')'));
      }
      if (reconnects >= maxReconnects) {
        throw new Error(payload?.detail || ('MoreAI stream error (' + response.status + ')'));
      }
      reconnects += 1;
      await waitForRetry(Math.min(8000, initialDelay * (2 ** (reconnects - 1))));
      continue;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let receivedEvent = false;

    const dispatch = (block: string) => {
      const lines = block.split(/\r?\n/);
      let event = 'message';
      let id: string | undefined;
      const dataLines: string[] = [];
      for (const line of lines) {
        if (line.startsWith('event:')) event = line.slice(6).trim();
        else if (line.startsWith('id:')) id = line.slice(3).trim();
        else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim());
      }
      if (!dataLines.length) return;
      try {
        const parsed = JSON.parse(dataLines.join('\n'));
        if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return;
        if (id && /^\d+$/.test(id)) {
          const sequence = Number(id);
          if (Number.isSafeInteger(sequence) && sequence >= cursor) cursor = sequence;
        }
        receivedEvent = true;
        onEvent({ id, event, data: parsed as Record<string, unknown> });
        if (['run.completed', 'run.failed', 'run.cancelled', 'run.timed_out', 'run.expired'].includes(event)) terminal = true;
      } catch {
        // Malformed frames are ignored; durable run/event retrieval remains authoritative.
      }
    };

    try {
      while (!terminal) {
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

    if (terminal) return;
    // A server-side stream.timeout is a normal long-poll boundary. Reconnect
    // from the last delivered event ID so a disconnect cannot skip durable events.
    if (reconnects >= maxReconnects) return;
    reconnects += 1;
    const delay = receivedEvent ? initialDelay : Math.min(8000, initialDelay * (2 ** (reconnects - 1)));
    await waitForRetry(delay);
  }
}


export type CustomerProfile = {
  id: string;
  display_name: string | null;
  avatar_path: string | null;
  locale: string;
  timezone: string;
};

export type CustomerToolCatalogItem = {
  key: string;
  version: string;
  description: string;
  input_schema: Record<string, unknown>;
  capability_tags: string[];
  permission_scope: string;
  risk: string;
  approval_mode: string;
  execution_environment: string;
  timeout_seconds: number;
  enabled_by_default: boolean;
  available_by_default: string[];
  registered: boolean;
  active_workers: number;
  availability_reason: string | null;
};

export type CustomerModelCapability = {
  provider_key: string;
  provider_name: string;
  model_key: string;
  model_name: string;
  capabilities: string[];
  max_input_tokens: number | null;
  max_output_tokens: number | null;
};

export const platformCatalogApi = {
  tools: () => moreAiCustomerApi<CustomerToolCatalogItem[]>('/api/v1/tools'),
  mediaCapabilities: () => moreAiCustomerApi<{
    image_generation: { available: boolean; worker_count: number; provider: string | null; reason: string | null };
    video_generation: { available: boolean; worker_count: number; provider: string | null; reason: string | null };
    file_generation: { available: boolean; worker_count: number; provider: string | null; reason: string | null };
  }>('/api/v1/media/capabilities'),
  modelCapabilities: () => moreAiCustomerApi<{ items: CustomerModelCapability[]; count: number; source: string }>('/api/v1/models/capabilities'),
};

export const profileApi = {
  get: () => moreAiCustomerApi<{ user: { id: string; email: string | null; display_name: string | null }; profile: CustomerProfile | null }>('/api/v1/me'),
  update: (payload: Partial<Pick<CustomerProfile, 'display_name' | 'avatar_path' | 'locale' | 'timezone'>>) =>
    moreAiCustomerApi<{ user: { id: string; email: string | null; display_name: string | null }; profile: CustomerProfile | null }>('/api/v1/me/profile', {
      method: 'PATCH', body: JSON.stringify(payload),
    }),
};

export type CustomerConversation = {
  id: string;
  workspace_id: string | null;
  title: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type CustomerConversationMessage = {
  id: string;
  role: string;
  content: string;
  model_key: string | null;
  run_id: string | null;
  created_at: string;
  attachments?: Array<{ id: string; filename: string; mime_type: string | null; size_bytes: number | null }>;
  citations?: Array<{ id: string; document_id: string; title: string; similarity?: number; source_page?: number | null; char_start?: number | null; char_end?: number | null; marker: string }>;
};

export type CustomerConversationSession = {
  id: string;
  conversation_id: string;
  status: string;
  attempt: number;
  max_attempts: number;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  available_at?: string | null;
  heartbeat_at?: string | null;
  cancel_requested_at?: string | null;
  last_checkpoint_key: string | null;
};

export type CustomerConversationSessionEvent = {
  id: string;
  event_type: string;
  sequence: number;
  created_at: string;
  payload: Record<string, unknown>;
};

export type CustomerAgentRunActivity = {
  id: string;
  sequence: number;
  timestamp: string;
  event_type: string;
  tool?: string | null;
  round?: number | null;
  index?: number | null;
  status?: string | null;
  phase?: string | null;
  progress?: number | null;
  tool_count?: number | null;
  next_round?: number | null;
  timeout_seconds?: number | null;
  checkpoint_key?: string | null;
  level?: string | null;
  message?: string | null;
};

export type CustomerWorkflowStep = {
  id: string;
  sequence: number;
  step_key: string;
  status: 'pending' | 'running' | 'waiting_approval' | 'succeeded' | 'failed' | 'skipped' | 'cancelled' | string;
  /** Zero-based indexes of prerequisite steps, projected from validated durable step input. */
  dependencies: number[];
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
};

export type CustomerAgentRunCancellationStatus =
  | 'cancel_requested' | 'cancelled' | 'succeeded' | 'failed' | 'timed_out' | 'expired';

export type CustomerAgentRunProgress = {
  status: string;
  current_step: string | null;
  total_steps: number;
  completed_steps: number;
  percentage: number;
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

export type CustomerChatEnqueueResponse = {
  run: CustomerAgentRun;
  message: {
    id: string; role: string; content: string; model_key?: string | null;
    run_id: string | null; created_at: string;
    attachments?: Array<{ id: string; filename: string; mime_type: string | null; size_bytes: number | null }>;
  } | null;
  replayed: boolean;
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
  scope_type: 'platform' | 'global' | 'user';
  scope_id: string | null;
  metric_key: string;
  limit_value: string | number;
  window_seconds: number;
  usage: { used_value: string | number; window_start: string; updated_at: string } | null;
};


export type CustomerNetworkSession = {
  id: string;
  network_id: string;
  status: string;
  started_at: string;
  last_heartbeat_at: string | null;
  expires_at: string;
  ended_at: string | null;
  end_reason: string | null;
  network: {
    id: string;
    name: string;
    ssid_label: string | null;
    gateway_type: string;
    status: string;
    location: { id: string; name: string; address: Record<string, unknown> } | null;
  } | null;
};

export type CustomerArtifact = {
  id: string;
  run_id: string | null;
  storage_path: string;
  mime_type: string | null;
  size_bytes: number | null;
  checksum_sha256: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
};

export const artifactApi = {
  list: () => moreAiCustomerApi<CustomerArtifact[]>('/api/v1/artifacts?limit=100'),
  listPage: (limit = 50, cursor?: string) => moreAiCustomerApiPage<CustomerArtifact>(
    `/api/v1/artifacts?limit=${Math.max(1, Math.min(100, limit))}${cursor ? '&cursor=' + encodeURIComponent(cursor) : ''}`,
  ),
  upload: (filename: string, content: Blob, mimeType = content.type || 'application/octet-stream', runId?: string) =>
    moreAiCustomerApi<CustomerArtifact>('/api/v1/artifacts', {
      method: 'POST',
      headers: {
        'X-Filename': filename,
        'Content-Type': mimeType,
        ...(runId ? { 'X-Agent-Run-Id': runId } : {}),
      },
      body: content,
    }),
  uploadAttachment: (conversationId: string, file: File) =>
    moreAiCustomerApi<CustomerArtifact>('/api/v1/artifacts', {
      method: 'POST',
      headers: {
        'X-Filename': file.name,
        'Content-Type': file.type || 'application/octet-stream',
        'X-Artifact-Purpose': 'chat_attachment',
        'X-Conversation-Id': conversationId,
      },
      body: file,
    }),
  signedDownload: (artifactId: string) =>
    moreAiCustomerApi<{ artifact_id: string; url: string; expires_in: number }>(
      `/api/v1/artifacts/${artifactId}/signed-download`,
      { method: 'POST' },
    ),
};

export type CustomerAccessCodeRedeemResponse = {
  redemption_id: string;
  replayed: boolean;
  redeemed_at: string;
  reward_id?: string | null;
  partner_entitlement_activated?: boolean | null;
  message?: string | null;
};

export type CustomerUsageAnalytics = {
  summary: {
    total_requests: number;
    total_tokens: number;
    successful_requests: number;
    failed_requests: number;
    total_cost: number | string;
    average_latency_ms: number;
  };
  by_model: Array<{
    model_key: string;
    provider_key: string;
    requests: number;
    tokens: number;
    successful_requests: number;
    cost: number | string;
  }>;
  by_day: Array<{ day: string; requests: number; tokens: number; cost: number | string }>;
  period: { since: string; until: string };
};

export type CustomerToolCatalogItem = {
  key: string;
  version: string;
  description: string;
  capability_tags: string[];
  permission_scope: string;
  risk: string;
  approval_mode: string;
  execution_environment: string;
  timeout_seconds: number;
  idempotency: string;
  available_by_default: string[];
  enabled_by_default: boolean;
};

export type CustomerAgentCatalogItem = {
  id: string;
  key: string;
  name: string;
  description: string;
  version: string;
  enabled: boolean;
  capability_tags: string[];
  tool_keys: string[];
  runtime_available: boolean;
  active_workers: number;
  live_tool_keys: string[];
  last_seen_at: string | null;
};


export type CustomerAgentConfiguration = {
  id: string;
  runtime_key: 'manus' | 'toolcall';
  name: string;
  description: string;
  system_prompt: string;
  tool_keys: string[];
  enabled: boolean;
  version: number;
  created_at: string;
  updated_at: string;
};

export type CustomerPersonalMemoryItem = {
  id: string;
  title: string;
  content: string;
  source_type: 'user_created';
  scope: 'personal';
  expires_at: string;
  created_at: string;
  updated_at: string;
};

export type CustomerPersonalMemoryState = {
  enabled: boolean;
  consent_version: string | null;
  consented_at: string | null;
  disabled_at: string | null;
  items: CustomerPersonalMemoryItem[];
};

export const customerApi = {
  tools: () => moreAiCustomerApi<CustomerToolCatalogItem[]>('/api/v1/tools'),
  modelCapabilities: () => moreAiCustomerApi<{
    items: Array<{
      provider_key: string; provider_name: string; model_key: string; model_name: string;
      capabilities: string[]; max_input_tokens: number | null; max_output_tokens: number | null;
    }>;
    count: number; source: string;
  }>('/api/v1/models/capabilities'),

  personalMemory: () => moreAiCustomerApi<CustomerPersonalMemoryState>('/api/v1/customer/memory'),
  setPersonalMemoryConsent: (enabled: boolean) => moreAiCustomerApi<{
    enabled: boolean; consent_version: string; consented_at: string | null;
    disabled_at: string | null; updated_at: string;
  }>('/api/v1/customer/memory/consent', {
    method: 'PUT', body: JSON.stringify({ enabled, consent_version: '2026-11-14.v1' }),
  }),
  createPersonalMemory: (payload: { title: string; content: string; retention_days: 30 | 90 | 180 | 365 }) =>
    moreAiCustomerApi<CustomerPersonalMemoryItem>('/api/v1/customer/memory', {
      method: 'POST', body: JSON.stringify(payload),
    }),
  updatePersonalMemory: (memoryId: string, payload: Partial<{
    title: string; content: string; retention_days: 30 | 90 | 180 | 365;
  }>) => moreAiCustomerApi<CustomerPersonalMemoryItem>(
    '/api/v1/customer/memory/' + encodeURIComponent(memoryId),
    { method: 'PATCH', body: JSON.stringify(payload) },
  ),
  deletePersonalMemory: (memoryId: string) => moreAiCustomerFetch(
    '/api/v1/customer/memory/' + encodeURIComponent(memoryId), { method: 'DELETE' },
  ).then(() => undefined),

  agentConfigurations: () => moreAiCustomerApi<CustomerAgentConfiguration[]>('/api/v1/customer/agents/configurations'),
  createAgentConfiguration: (payload: Pick<CustomerAgentConfiguration, 'runtime_key' | 'name' | 'description' | 'system_prompt' | 'tool_keys'>) =>
    moreAiCustomerApi<CustomerAgentConfiguration>('/api/v1/customer/agents/configurations', {
      method: 'POST', body: JSON.stringify(payload),
    }),
  updateAgentConfiguration: (id: string, payload: Partial<Pick<CustomerAgentConfiguration, 'name' | 'description' | 'system_prompt' | 'tool_keys' | 'enabled'>>) =>
    moreAiCustomerApi<CustomerAgentConfiguration>('/api/v1/customer/agents/configurations/' + encodeURIComponent(id), {
      method: 'PATCH', body: JSON.stringify(payload),
    }),
  deleteAgentConfiguration: (id: string) => moreAiCustomerFetch(
    '/api/v1/customer/agents/configurations/' + encodeURIComponent(id), { method: 'DELETE' },
  ).then(() => undefined),
  agents: () => moreAiCustomerApi<CustomerAgentCatalogItem[]>('/api/v1/agents'),
  context: () => moreAiCustomerApi<{ principal: { user_id: string; role: string }; tenant: null }>('/api/v1/customer/context'),
  conversations: (limit = 50, before?: string) => moreAiCustomerApi<CustomerConversation[]>(`/api/v1/customer/conversations?limit=${Math.max(1, Math.min(100, limit))}${before ? '&before=' + encodeURIComponent(before) : ''}`),
  conversationsPage: (limit = 50, cursor?: string) => moreAiCustomerApiPage<CustomerConversation>(
    `/api/v1/customer/conversations?limit=${Math.max(1, Math.min(100, limit))}${cursor ? '&cursor=' + encodeURIComponent(cursor) : ''}`,
  ),
  getConversation: async (conversationId: string) => {
    const response = await moreAiCustomerFetch('/api/v1/customer/conversations/' + encodeURIComponent(conversationId));
    const payload = await response.json() as { conversation: CustomerConversation; messages: CustomerConversationMessage[] };
    return { ...payload, nextCursor: response.headers.get('X-Next-Cursor') };
  },
  conversationMessagesPage: (conversationId: string, limit = 50, cursor?: string) =>
    moreAiCustomerApiPage<CustomerConversationMessage>(
      '/api/v1/customer/conversations/' + encodeURIComponent(conversationId) + '/messages?limit='
        + Math.max(1, Math.min(100, limit))
        + (cursor ? '&cursor=' + encodeURIComponent(cursor) : ''),
    ),
  createConversation: (title: string, workspaceId?: string | null) => moreAiCustomerApi<{ id: string; workspace_id: string | null }>('/api/v1/customer/conversations', {
    method: 'POST', body: JSON.stringify({ title, workspace_id: workspaceId || null }),
  }),
  clearPersonalMemory: () => moreAiCustomerFetch('/api/v1/customer/memory', { method: 'DELETE' }).then(() => undefined),
  sendMessage: (
    conversationId: string, content: string, idempotencyKey: string,
    agentKey: 'manus' | 'planning' | 'toolcall' = 'manus', attachmentIds: string[] = [],
    agentConfigurationId?: string | null, skillIds: string[] = [],
  ) => moreAiCustomerApi<CustomerChatEnqueueResponse>(`/api/v1/customer/conversations/${conversationId}/messages`, {
    method: 'POST',
    headers: { 'Idempotency-Key': idempotencyKey },
    body: JSON.stringify({ content, agent_key: agentKey, attachment_ids: attachmentIds, agent_configuration_id: agentConfigurationId || null, skill_ids: skillIds }),
  }),
  agentRuns: (limit = 50, before?: string) => moreAiCustomerApi<CustomerAgentRun[]>(`/api/v1/customer/agent-runs?limit=${Math.max(1, Math.min(100, limit))}${before ? '&before=' + encodeURIComponent(before) : ''}`),
  agentRunsPage: (limit = 50, cursor?: string) => moreAiCustomerApiPage<CustomerAgentRun>(
    `/api/v1/customer/agent-runs?limit=${Math.max(1, Math.min(100, limit))}${cursor ? '&cursor=' + encodeURIComponent(cursor) : ''}`,
  ),
  conversationSession: (conversationId: string, runId: string) => moreAiCustomerApi<{
    id: string; conversation_id: string; status: string; attempt: number;
    max_attempts: number; created_at: string; started_at: string | null;
    finished_at: string | null; last_checkpoint_key: string | null;
  }>(
    '/api/v1/conversations/' + encodeURIComponent(conversationId) + '/sessions/' + encodeURIComponent(runId),
  ),
  conversationSessions: async (conversationId: string, limit = 50, cursor?: string) => {
    const response = await moreAiCustomerFetch(
      '/api/v1/conversations/' + encodeURIComponent(conversationId) + '/sessions?limit='
        + Math.max(1, Math.min(100, limit))
        + (cursor ? '&cursor=' + encodeURIComponent(cursor) : ''),
    );
    const payload = await response.json() as { items: CustomerConversationSession[]; count: number };
    return { ...payload, nextCursor: response.headers.get('X-Next-Cursor') };
  },
  updateConversation: (conversationId: string, payload: { title?: string | null; status?: 'active' | 'archived' }) =>
    moreAiCustomerApi<CustomerConversation>(
      '/api/v1/conversations/' + encodeURIComponent(conversationId),
      { method: 'PATCH', body: JSON.stringify(payload) },
    ),
  archiveConversation: (conversationId: string) =>
    moreAiCustomerApi<{ id: string; status: 'archived' }>(
      '/api/v1/conversations/' + encodeURIComponent(conversationId),
      { method: 'DELETE' },
    ),
  cancelConversationSession: (conversationId: string, runId: string) =>
    moreAiCustomerApi<{ run_id: string; status: CustomerAgentRunCancellationStatus }>(
      '/api/v1/conversations/' + encodeURIComponent(conversationId) + '/sessions/' + encodeURIComponent(runId) + '/cancel',
      { method: 'POST' },
    ),
  conversationSessionEvents: (conversationId: string, runId: string, after = 0, limit = 200) =>
    moreAiCustomerApi<{ items: CustomerConversationSessionEvent[]; count: number; next_after: number }>(
      '/api/v1/conversations/' + encodeURIComponent(conversationId) + '/sessions/' + encodeURIComponent(runId)
        + '/events?after=' + Math.max(0, after) + '&limit=' + Math.max(1, Math.min(500, limit)),
    ),
  getRun: (runId: string) => moreAiCustomerApi<CustomerAgentRun>(`/api/v1/customer/agent-runs/${runId}`),
  retryRun: (runId: string, idempotencyKey: string) =>
    moreAiCustomerApi<CustomerChatEnqueueResponse>(`/api/v1/customer/agent-runs/${encodeURIComponent(runId)}/retry`, {
      method: 'POST', headers: { 'Idempotency-Key': idempotencyKey },
    }),
  cancelRun: (runId: string) => moreAiCustomerApi<{ run_id: string; status: CustomerAgentRunCancellationStatus }>(`/api/v1/customer/agent-runs/${runId}/cancel`, {
    method: 'POST',
  }),
  getRunSteps: (runId: string) => moreAiCustomerApi<CustomerWorkflowStep[]>(`/api/v1/customer/agent-runs/${runId}/steps`),
  getRunProgress: (runId: string) => moreAiCustomerApi<CustomerAgentRunProgress>(
    `/api/v1/agent-runs/${encodeURIComponent(runId)}/progress`,
  ),
  getRunActivity: (runId: string, after = 0, limit = 200) =>
    moreAiCustomerApi<{ items: CustomerAgentRunActivity[]; count: number; next_after: number }>(
      `/api/v1/agent-runs/${encodeURIComponent(runId)}/logs?after=${Math.max(0, after)}&limit=${Math.max(1, Math.min(500, limit))}`,
    ),
  getRunEvents: (runId: string, after = 0) => moreAiCustomerApi<Array<{
    id: string; event_type: string; sequence: number; payload: Record<string, unknown>;
    created_at: string; checkpoint: Record<string, unknown> | null;
  }>>(
    `/api/v1/agent-runs/${encodeURIComponent(runId)}/events?after=${Math.max(0, after)}`,
  ),
  streamRun: (runId: string, after = 0) => `/api/v1/customer/agent-runs/${runId}/stream?after=${Math.max(0, after)}&wait_seconds=30`,
  networkSessions: (limit = 50) => moreAiCustomerApi<CustomerNetworkSession[]>(
    `/api/v1/customer/network-sessions?limit=${Math.min(100, Math.max(1, limit))}`,
  ),
  networkSessionsPage: (limit = 50, cursor?: string) => moreAiCustomerApiPage<CustomerNetworkSession>(
    `/api/v1/customer/network-sessions?limit=${Math.min(100, Math.max(1, limit))}${cursor ? '&cursor=' + encodeURIComponent(cursor) : ''}`,
  ),
  networkSpeedtestPing: () => moreAiCustomerApi<{ status: 'ok'; service: 'moreai-api'; timestamp: string }>(
    '/api/v1/customer/network/speedtest/ping',
  ),
  networkSpeedtestDownload: (sizeBytes = 4 * 1024 * 1024) =>
    moreAiCustomerFetch('/api/v1/customer/network/speedtest/download?size_bytes=' + Math.max(65536, Math.min(8 * 1024 * 1024, sizeBytes))),
  networkSpeedtestUpload: (payload: BodyInit) =>
    moreAiCustomerApi<{ status: 'ok'; received_bytes: number; server_receive_ms: number }>(
      '/api/v1/customer/network/speedtest/upload',
      { method: 'POST', headers: { 'Content-Type': 'application/octet-stream' }, body: payload },
    ),
  wallets: () => moreAiCustomerApi<{ wallets: CustomerWallet[] }>('/api/v1/customer/wallet'),
  ledger: (limit = 50, before?: string) => moreAiCustomerApi<CustomerLedgerEntry[]>(`/api/v1/customer/wallet/ledger?limit=${limit}${before ? `&before=${encodeURIComponent(before)}` : ''}`),
  ledgerPage: (limit = 50, cursor?: string, walletId?: string) => moreAiCustomerApiPage<CustomerLedgerEntry>(
    `/api/v1/customer/wallet/ledger?limit=${Math.max(1, Math.min(100, limit))}${cursor ? '&cursor=' + encodeURIComponent(cursor) : ''}${walletId ? '&wallet_id=' + encodeURIComponent(walletId) : ''}`,
  ),
  usage: (limit = 50, before?: string) => moreAiCustomerApi<CustomerUsageRecord[]>(`/api/v1/customer/usage?limit=${limit}${before ? `&before=${encodeURIComponent(before)}` : ''}`),
  usagePage: (limit = 50, cursor?: string) => moreAiCustomerApiPage<CustomerUsageRecord>(
    `/api/v1/customer/usage?limit=${Math.max(1, Math.min(100, limit))}${cursor ? '&cursor=' + encodeURIComponent(cursor) : ''}`,
  ),
  usageAnalytics: (days = 30) => moreAiCustomerApi<CustomerUsageAnalytics>(`/api/v1/customer/usage/analytics?days=${Math.max(1, Math.min(365, days))}`),
  entitlements: () => moreAiCustomerApi<CustomerEntitlement[]>('/api/v1/customer/entitlements'),
  quotas: () => moreAiCustomerApi<CustomerQuota[]>('/api/v1/customer/quotas'),
  redeemAccessCode: (code: string, networkId: string, verificationSessionId: string, idempotencyKey: string) =>
    moreAiCustomerApi<CustomerAccessCodeRedeemResponse>('/api/v1/customer/access-codes/redeem', { method: 'POST', headers: { 'Idempotency-Key': idempotencyKey }, body: JSON.stringify({ code, network_id: networkId, verification_session_id: verificationSessionId }) }),
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

export type CustomerToolApprovalDecision = {
  id: string;
  run_id: string;
  tool_key: string;
  status: 'approved' | 'denied' | 'expired' | 'consumed';
  decided_at: string | null;
  expires_at: string;
  resumed: boolean;
};

export const customerToolApprovalApi = {
  list: () => moreAiCustomerApi<CustomerToolApproval[]>('/api/v1/customer/tool-approvals'),
  listPage: (limit = 30, cursor?: string) => moreAiCustomerApiPage<CustomerToolApproval>(
    `/api/v1/customer/tool-approvals?limit=${Math.max(1, Math.min(100, limit))}${cursor ? '&cursor=' + encodeURIComponent(cursor) : ''}`,
  ),
  request: (input: { run_id: string; tool_key: 'bash' | 'python_execute' | 'browser_use' | 'planning_step' | 'browser' | 'file_read' | 'file_write' | 'file_edit' | 'workspace_restore_version'; arguments_hash: string; summary: string }) =>
    moreAiCustomerApi<CustomerToolApproval>('/api/v1/customer/tool-approvals', {
      method: 'POST', body: JSON.stringify(input),
    }),
  decide: (approvalId: string, decision: 'approved' | 'denied') =>
    moreAiCustomerApi<CustomerToolApprovalDecision>(`/api/v1/customer/tool-approvals/${approvalId}/decision`, {
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
    moreAiCustomerApi<{ items: CustomerNotification[]; limit: number; next_cursor?: string | null }>(
      `/api/v1/notifications?unread_only=${unreadOnly}&limit=${Math.min(100, Math.max(1, limit))}`,
    ),
  listPage: (unreadOnly = false, limit = 30, cursor?: string) => moreAiCustomerApiPage<CustomerNotification>(
    `/api/v1/notifications?unread_only=${unreadOnly}&limit=${Math.min(100, Math.max(1, limit))}${cursor ? '&cursor=' + encodeURIComponent(cursor) : ''}`,
  ),
  preferences: () => moreAiCustomerApi<CustomerNotificationPreferences>('/api/v1/notifications/preferences'),
  updatePreferences: (payload: Partial<Omit<CustomerNotificationPreferences, 'updated_at'>>) =>
    moreAiCustomerApi<CustomerNotificationPreferences>('/api/v1/notifications/preferences', {
      method: 'PUT', body: JSON.stringify(payload),
    }),
  markRead: (notificationId: string) =>
    moreAiCustomerApi<{ id: string; read_at: string }>(`/api/v1/notifications/${notificationId}/read`, { method: 'POST' }),
  markAllRead: () => moreAiCustomerApi<{ updated: number }>('/api/v1/notifications/read-all', { method: 'POST' }),
};


export const platformAdminApi = {
  updatePartnerStatus: (partnerId: string, status: 'pending' | 'active' | 'suspended' | 'rejected' | 'closed', idempotencyKey: string) =>
    moreAiApi<{ partner_id: string; status: string; previous_status: string; updated_at: string }>(
      `/api/v1/admin/partners/${partnerId}/status`,
      { method: 'PATCH', headers: { 'Idempotency-Key': idempotencyKey }, body: JSON.stringify({ status }) },
    ),
};


export type CustomerWorkspace = {
  id: string;
  name: string;
  slug: string;
  owner_user_id: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type CustomerWorkspaceFile = {
  id: string;
  path: string;
  version: number;
  storage_path: string | null;
  sha256: string | null;
  size_bytes: number | null;
  updated_at: string;
  deleted_at?: string | null;
};

export type CustomerWorkspaceFileLifecycleResult = {
  id: string; workspace_id: string; path: string; version: number;
  deleted_at: string | null; status: 'deleted' | 'restored';
};

export type CustomerWorkspaceFileVersion = {
  id: string;
  path: string;
  version: number;
  storage_path: string;
  sha256: string;
  size_bytes: number;
  committed_at: string;
  current?: boolean;
};

export type CustomerWorkspaceUploadResult = {
  workspace_id: string;
  file_id: string;
  path: string;
  version: number;
  storage_path: string;
  sha256: string;
  size_bytes: number;
  updated_at: string;
  replayed: boolean;
};

export type CustomerWorkspaceMember = {
  id: string; workspace_id: string; user_id: string; role_id: string | null;
  status: string; invited_by: string | null; joined_at: string | null; created_at: string;
};

export const workspaceApi = {
  list: () => moreAiCustomerApi<{ items: CustomerWorkspace[]; count: number }>('/api/v1/customer/workspaces?limit=100'),
  listPage: (limit = 50, cursor?: string) => moreAiCustomerApiPage<CustomerWorkspace>(
    '/api/v1/customer/workspaces?limit=' + Math.max(1, Math.min(100, limit)) + (cursor ? '&cursor=' + encodeURIComponent(cursor) : ''),
  ),
  create: (name: string) => moreAiCustomerApi<CustomerWorkspace>('/api/v1/customer/workspaces', {
    method: 'POST', body: JSON.stringify({ name }),
  }),
  files: (workspaceId: string) => moreAiCustomerApi<{ items: CustomerWorkspaceFile[]; count: number }>(
    '/api/v1/customer/workspaces/' + encodeURIComponent(workspaceId) + '/files?limit=100',
  ),
  filesPage: (workspaceId: string, limit = 50, cursor?: string, includeDeleted = false) => moreAiCustomerApiPage<CustomerWorkspaceFile>(
    '/api/v1/customer/workspaces/' + encodeURIComponent(workspaceId) + '/files?limit=' + Math.max(1, Math.min(100, limit))
      + (cursor ? '&cursor=' + encodeURIComponent(cursor) : '')
      + (includeDeleted ? '&include_deleted=true' : ''),
  ),
  fileByPath: (workspaceId: string, path: string) => moreAiCustomerApiPage<CustomerWorkspaceFile>(
    '/api/v1/customer/workspaces/' + encodeURIComponent(workspaceId) + '/files?limit=1&include_deleted=true&path=' + encodeURIComponent(path),
  ),
  deleteFile: (workspaceId: string, fileId: string, expectedVersion: number) =>
    moreAiCustomerApi<CustomerWorkspaceFileLifecycleResult>(
      '/api/v1/customer/workspaces/' + encodeURIComponent(workspaceId) + '/files/' + encodeURIComponent(fileId)
        + '/delete?expected_version=' + encodeURIComponent(String(expectedVersion)),
      { method: 'POST' },
    ),
  restoreFile: (workspaceId: string, fileId: string, expectedVersion: number) =>
    moreAiCustomerApi<CustomerWorkspaceFileLifecycleResult>(
      '/api/v1/customer/workspaces/' + encodeURIComponent(workspaceId) + '/files/' + encodeURIComponent(fileId)
        + '/restore?expected_version=' + encodeURIComponent(String(expectedVersion)),
      { method: 'POST' },
    ),
  uploadFile: (workspaceId: string, path: string, expectedVersion: number, file: Blob, idempotencyKey: string) =>
    moreAiCustomerApi<CustomerWorkspaceUploadResult>(
      '/api/v1/customer/workspaces/' + encodeURIComponent(workspaceId) + '/files',
      {
        method: 'POST',
        headers: {
          'Content-Type': file.type || 'application/octet-stream',
          'X-Workspace-Path': path,
          'If-Match': String(expectedVersion),
          'Idempotency-Key': idempotencyKey,
        },
        body: file,
      },
    ),
  runs: (workspaceId: string, limit = 50) => moreAiCustomerApi<{ items: Array<{
    id: string; conversation_id: string | null; status: string; attempt: number;
    max_attempts: number; created_at: string; started_at: string | null;
    finished_at: string | null; available_at: string | null; heartbeat_at: string | null;
    cancel_requested_at: string | null; last_checkpoint_key: string | null;
  }>; count: number }>(
    '/api/v1/customer/workspaces/' + encodeURIComponent(workspaceId) + '/runs?limit=' + encodeURIComponent(String(limit)),
  ),
  runsPage: (workspaceId: string, limit = 50, cursor?: string) => moreAiCustomerApiPage<{
    id: string; conversation_id: string | null; status: string; attempt: number;
    max_attempts: number; created_at: string; started_at: string | null;
    finished_at: string | null; available_at: string | null; heartbeat_at: string | null;
    cancel_requested_at: string | null; last_checkpoint_key: string | null;
  }>(
    '/api/v1/customer/workspaces/' + encodeURIComponent(workspaceId) + '/runs?limit=' + Math.max(1, Math.min(100, limit)) + (cursor ? '&cursor=' + encodeURIComponent(cursor) : ''),
  ),
  versions: (workspaceId: string, fileId: string) => moreAiCustomerApi<{
    items: CustomerWorkspaceFileVersion[]; count: number; current_version: number;
  }>('/api/v1/customer/workspaces/' + encodeURIComponent(workspaceId) + '/files/' + encodeURIComponent(fileId) + '/versions'),
  membersPage: (workspaceId: string, limit = 50, cursor?: string) => moreAiCustomerApiPage<CustomerWorkspaceMember>(
    '/api/v1/customer/workspaces/' + encodeURIComponent(workspaceId) + '/members?limit=' + Math.max(1, Math.min(100, limit)) + (cursor ? '&cursor=' + encodeURIComponent(cursor) : ''),
  ),
  signedDownload: (workspaceId: string, fileId: string, version?: number) => moreAiCustomerApi<{
    file_id: string; version: number; url: string; expires_in: number;
  }>('/api/v1/customer/workspaces/' + encodeURIComponent(workspaceId) + '/files/' + encodeURIComponent(fileId) + '/signed-download' + (version === undefined ? '' : '?version=' + version), {
    method: 'POST',
  }),
};



export const customerWorkspaceApi = {
  list: () => moreAiCustomerApi<{ items: CustomerWorkspace[]; count: number }>('/api/v1/customer/workspaces?limit=100'),
  listPage: (limit = 50, cursor?: string) => moreAiCustomerApiPage<CustomerWorkspace>(
    '/api/v1/customer/workspaces?limit=' + Math.max(1, Math.min(100, limit)) + (cursor ? '&cursor=' + encodeURIComponent(cursor) : ''),
  ),
  create: (name: string) => moreAiCustomerApi<CustomerWorkspace>('/api/v1/customer/workspaces', {
    method: 'POST', body: JSON.stringify({ name }),
  }),
  rename: (workspaceId: string, name: string) => moreAiCustomerApi<CustomerWorkspace>(
    '/api/v1/customer/workspaces/' + encodeURIComponent(workspaceId),
    { method: 'PATCH', body: JSON.stringify({ name }) },
  ),
  archive: (workspaceId: string) => moreAiCustomerApi<{ workspace: CustomerWorkspace; archived: boolean }>(
    '/api/v1/customer/workspaces/' + encodeURIComponent(workspaceId) + '/archive',
    { method: 'POST' },
  ),
  members: (workspaceId: string) => moreAiCustomerApi<{ items: Array<{
    id: string; workspace_id: string; user_id: string; role_id: string | null;
    status: string; invited_by: string | null; joined_at: string | null; created_at: string;
  }>; count: number }>(
    '/api/v1/customer/workspaces/' + encodeURIComponent(workspaceId) + '/members?limit=100',
  ),
  membersPage: (workspaceId: string, limit = 50, cursor?: string) => moreAiCustomerApiPage<CustomerWorkspaceMember>(
    '/api/v1/customer/workspaces/' + encodeURIComponent(workspaceId) + '/members?limit=' + Math.max(1, Math.min(100, limit)) + (cursor ? '&cursor=' + encodeURIComponent(cursor) : ''),
  ),
  removeMember: (workspaceId: string, memberId: string) => moreAiCustomerApi<{
    member_id: string; status: 'removed';
  }>(
    '/api/v1/customer/workspaces/' + encodeURIComponent(workspaceId) + '/members/' + encodeURIComponent(memberId),
    { method: 'DELETE' },
  ),
};

export type CustomerLearningProgress = {
  id: string;
  module_key: string;
  lesson_key: string;
  completed_at: string;
  updated_at: string;
};

export type CustomerLearningPathSummary = {
  id: string;
  title: string;
  description: string;
  education_level: string;
  learning_goal: string;
  status: 'draft' | 'active' | 'completed' | 'archived';
  created_by_run_id: string;
  created_at: string;
  updated_at: string;
  enrollment: { id: string; status: string; enrolled_at: string } | null;
  progress: { lessons_started: number; lessons_completed: number; lessons_total: number; average_percent: number };
};

export type CustomerLearningPathDetail = {
  path: CustomerLearningPathSummary;
  modules: Array<{
    id: string; module_index: number; title: string; summary: string; estimated_minutes: number;
    lessons: Array<{
      id: string; lesson_index: number; title: string; content_md: string;
      objectives: string[]; content_version: number; status: string;
      progress: { status: string; progress_percent: number; completed_at: string | null } | null;
      quizzes: Array<{ id: string; title: string; questions: unknown[]; pass_score: number; attempts: Array<{ id: string; score: number; passed: boolean; feedback: Record<string, unknown>; submitted_at: string }> }>;
    }>;
  }>;
  enrollment: { id: string; status: string; enrolled_at: string } | null;
  assessments: Array<{ id: string; module_id: string | null; lesson_id: string | null; quiz_id: string | null; run_id: string; assessment_type: string; score: number | null; rubric: unknown[]; feedback: Record<string, unknown>; created_at: string }>;
};

export const learningApi = {
  paths: (limit = 20) => moreAiCustomerApi<{ items: CustomerLearningPathSummary[]; count: number }>(
    '/api/v1/customer/learning/paths?limit=' + Math.max(1, Math.min(100, limit)),
  ),
  pathsPage: (limit = 20, cursor?: string) => moreAiCustomerApiPage<CustomerLearningPathSummary>(
    '/api/v1/customer/learning/paths?limit=' + Math.max(1, Math.min(100, limit))
      + (cursor ? '&cursor=' + encodeURIComponent(cursor) : ''),
  ),
  path: (pathId: string) => moreAiCustomerApi<CustomerLearningPathDetail>(
    '/api/v1/customer/learning/paths/' + encodeURIComponent(pathId),
  ),
  lessonVersions: (pathId: string, lessonId: string) => moreAiCustomerApi<{ items: Array<{
    id: string; version: number; content_md: string; objectives: string[]; source_run_id: string | null; created_at: string;
  }>; count: number }>(
    '/api/v1/customer/learning/paths/' + encodeURIComponent(pathId) + '/lessons/' + encodeURIComponent(lessonId) + '/versions',
  ),
  progressDetail: (limit = 100) => moreAiCustomerApi<{ items: Array<{
    id: string; path_id: string; module_id: string; lesson_id: string; status: string;
    progress_percent: number; last_run_id: string | null; started_at: string | null;
    completed_at: string | null; updated_at: string;
  }>; count: number }>(
    '/api/v1/customer/learning/progress/detail?limit=' + Math.max(1, Math.min(500, limit)),
  ),
  runArtifacts: (runId: string) => moreAiCustomerApi<{ items: Array<{
    id: string; artifact_type: string; resource_id: string; payload: Record<string, unknown>; created_at: string;
  }>; count: number }>(
    '/api/v1/customer/learning/runs/' + encodeURIComponent(runId) + '/artifacts',
  ),
  progress: () => moreAiCustomerApi<{ items: CustomerLearningProgress[]; count: number; total_count: number }>(
    '/api/v1/customer/learning/progress?limit=100',
  ),
  progressPage: (limit = 50, cursor?: string, moduleKey?: string) => moreAiCustomerApiPage<CustomerLearningProgress>(
    '/api/v1/customer/learning/progress?limit=' + Math.max(1, Math.min(100, limit))
      + (cursor ? '&cursor=' + encodeURIComponent(cursor) : '')
      + (moduleKey ? '&module_key=' + encodeURIComponent(moduleKey) : ''),
  ),
  setProgress: (moduleKey: string, lessonKey: string, completed: boolean) => moreAiCustomerApi<{
    module_key: string; lesson_key: string; completed: boolean; completed_at: string | null;
  }>('/api/v1/customer/learning/progress', {
    method: 'PUT',
    body: JSON.stringify({ module_key: moduleKey, lesson_key: lessonKey, completed }),
  }),
};


/** Cursor-page reader for both array and { items, ... } Customer API responses. */
export async function moreAiCustomerApiPage<T>(
  path: string,
  init: RequestInit = {},
): Promise<{ items: T[]; nextCursor: string | null }> {
  const response = await moreAiCustomerFetch(path, init);
  const payload: unknown = await response.json();
  const items = Array.isArray(payload)
    ? payload
    : payload && typeof payload === 'object' && Array.isArray((payload as { items?: unknown }).items)
      ? (payload as { items: unknown[] }).items
      : null;
  if (!items) {
    throw new Error('MoreAI API pagination response does not contain an items collection.');
  }
  return {
    items: items as T[],
    nextCursor: response.headers.get('X-Next-Cursor'),
  };
}

export type CustomerSkillPackage = {
  id: string; slug: string; name: string; description: string;
  source_repository: string; source_ref: string; source_commit: string; source_path: string;
  source_blob_sha: string; content_sha256: string; version: string; license_id: string;
  license_url: string | null; license_status: string; manifest: Record<string, unknown>;
  requested_permissions: string[]; validation_status: string;
  validation_report: { findings?: string[]; scope?: string; checked_at?: string };
  publication_status: string; created_at: string; updated_at: string;
  installation: {
    id: string; status: string; execution_enabled: boolean;
    permission_request: string[]; permission_status: string;
  } | null;
};

export const customerSkillApi = {
  list: () => moreAiCustomerApi<{ items: CustomerSkillPackage[]; count: number }>('/api/v1/customer/skills'),
  import: (payload: {
    slug: string; name: string; description?: string; source_repository: string;
    source_ref: string; source_commit: string; source_path: string; source_blob_sha: string;
    content_sha256: string; version: string; license_id: string; license_url?: string;
    license_evidence?: string; manifest?: Record<string, unknown>; requested_permissions?: string[];
  }) => moreAiCustomerApi<CustomerSkillPackage>('/api/v1/customer/skills', {
    method: 'POST', body: JSON.stringify(payload),
  }),

  ingest: (skillId: string) => moreAiCustomerApi<{
    skill_id: string; source_commit: string; file_count: number;
    total_bytes: number; integrity: string; execution_enabled: boolean;
  }>(`/api/v1/customer/skills/${encodeURIComponent(skillId)}/ingest`, { method: 'POST' }),
  validate: (skillId: string) => moreAiCustomerApi<{
    skill_id: string; validation_status: string; license_status: string; findings: string[];
  }>(`/api/v1/customer/skills/${encodeURIComponent(skillId)}/validate`, { method: 'POST' }),
  install: (skillId: string) => moreAiCustomerApi<Record<string, unknown>>(
    `/api/v1/customer/skills/${encodeURIComponent(skillId)}/install`, { method: 'POST' },
  ),
  requestPermissions: (skillId: string, permissions: string[]) => moreAiCustomerApi<Record<string, unknown>>(
    `/api/v1/customer/skills/${encodeURIComponent(skillId)}/permissions`,
    { method: 'POST', body: JSON.stringify({ permissions }) },
  ),
};


export type CustomerConnection = {
  id: string; provider: string; display_name: string | null; scopes: string[];
  status: string; access_token_expires_at: string | null; token_updated_at: string;
};

export const connectionsApi = {
  list: () => moreAiCustomerApi<CustomerConnection[]>('/api/v1/customer/connections'),
  authorize: (permissions: string[]) => moreAiCustomerApi<{ authorization_url: string; expires_in: number; permissions: string[] }>(
    '/api/v1/customer/connections/google/authorize', { method: 'POST', body: JSON.stringify({ permissions }) },
  ),
  gmailMessages: (connectionId: string, query = 'newer_than:30d') => moreAiCustomerApi<{ items: Array<{id:string;thread_id:string;subject?:string;from?:string;date?:string;snippet?:string;unread?:boolean}>; count: number }>(
    '/api/v1/customer/connections/' + encodeURIComponent(connectionId) + '/gmail/messages?q=' + encodeURIComponent(query),
  ),
  calendarEvents: (connectionId: string, timeMin: string, timeMax: string) => moreAiCustomerApi<{ items: Array<{id:string;summary?:string;status?:string;start?:{dateTime?:string;date?:string};end?:{dateTime?:string;date?:string};html_link?:string;etag?:string}>; count: number }>(
    '/api/v1/customer/connections/' + encodeURIComponent(connectionId) + '/calendar/events?time_min=' + encodeURIComponent(timeMin) + '&time_max=' + encodeURIComponent(timeMax),
  ),
  disconnect: (connectionId: string) => moreAiCustomerApi<{id:string;status:string}>(
    '/api/v1/customer/connections/' + encodeURIComponent(connectionId), { method: 'DELETE' },
  ),
  sendGmail: (connectionId: string, to: string[], subject: string, body: string) => moreAiCustomerApi<{status:string;replayed:boolean;receipt?:Record<string,unknown>}>(
    '/api/v1/customer/connections/' + encodeURIComponent(connectionId) + '/gmail/send',
    { method: 'POST', headers: { 'Idempotency-Key': crypto.randomUUID() }, body: JSON.stringify({ to, subject, body, confirmed: true }) },
  ),
  createCalendarEvent: (connectionId: string, summary: string, start: string, end: string, description = '') => moreAiCustomerApi<{status:string;replayed:boolean;receipt?:Record<string,unknown>}>(
    '/api/v1/customer/connections/' + encodeURIComponent(connectionId) + '/calendar/events',
    { method: 'POST', headers: { 'Idempotency-Key': crypto.randomUUID() }, body: JSON.stringify({ summary, description, start, end, timezone: 'Asia/Jakarta', confirmed: true }) },
  ),
  updateCalendarEvent: (connectionId: string, eventId: string, etag: string, summary: string) => moreAiCustomerApi<{status:string;replayed:boolean;event?:{id:string;summary?:string;etag?:string}}>(
    '/api/v1/customer/connections/' + encodeURIComponent(connectionId) + '/calendar/events/' + encodeURIComponent(eventId),
    { method: 'PATCH', headers: { 'If-Match': etag, 'Idempotency-Key': crypto.randomUUID() }, body: JSON.stringify({ summary, confirmed: true }) },
  ),
  deleteCalendarEvent: (connectionId: string, eventId: string, etag: string) => moreAiCustomerApi<{status:string;replayed:boolean;event_id:string}>(
    '/api/v1/customer/connections/' + encodeURIComponent(connectionId) + '/calendar/events/' + encodeURIComponent(eventId) + '?confirmed=true',
    { method: 'DELETE', headers: { 'If-Match': etag, 'Idempotency-Key': crypto.randomUUID() } },
  ),
};
