import { moreAiCustomerApi, moreAiCustomerApiPage } from '@/lib/api/client';

export type CustomerKnowledgeDocument = {
  id: string;
  title: string;
  workspace_id: string | null;
  source_type: 'text' | 'file' | 'url';
  source_ref: string | null;
  content_sha256: string | null;
  status: 'processing' | 'ready' | 'failed' | 'archived';
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type CustomerKnowledgeChunk = {
  id: string;
  chunk_index: number;
  token_count: number | null;
  created_at: string;
};

export type CustomerKnowledgeDocumentDetail = {
  document: CustomerKnowledgeDocument;
  chunks: CustomerKnowledgeChunk[];
  chunk_count: number;
  total_chunk_count: number;
  next_after_chunk_index: number | null;
};

export const knowledgeApi = {
  upload: (file: File, options: { workspaceId?: string; title?: string } = {}) => {
    const body = new FormData();
    body.append('file', file, file.name);
    if (options.workspaceId) body.append('workspace_id', options.workspaceId);
    if (options.title) body.append('title', options.title);
    return moreAiCustomerApi<{
      document: CustomerKnowledgeDocument;
      status: 'processing' | 'ready' | 'failed';
      reused: boolean;
      upload: { filename: string; size_bytes: number; mime_type: string };
    }>('/api/v1/customer/knowledge/documents/upload', { method: 'POST', body });
  },
  list: (options: { workspaceId?: string; status?: CustomerKnowledgeDocument['status']; limit?: number } = {}) => {
    const params = new URLSearchParams();
    if (options.workspaceId) params.set('workspace_id', options.workspaceId);
    if (options.status) params.set('status', options.status);
    if (options.limit) params.set('limit', String(Math.min(100, Math.max(1, options.limit))));
    const query = params.toString();
    return moreAiCustomerApi<{ items: CustomerKnowledgeDocument[]; count: number }>(
      '/api/v1/customer/knowledge/documents' + (query ? '?' + query : ''),
    );
  },
  listPage: (options: { workspaceId?: string; status?: CustomerKnowledgeDocument['status']; limit?: number; cursor?: string } = {}) => {
    const params = new URLSearchParams();
    if (options.workspaceId) params.set('workspace_id', options.workspaceId);
    if (options.status) params.set('status', options.status);
    params.set('limit', String(Math.min(100, Math.max(1, options.limit ?? 50))));
    if (options.cursor) params.set('cursor', options.cursor);
    return moreAiCustomerApiPage<CustomerKnowledgeDocument>(
      '/api/v1/customer/knowledge/documents?' + params.toString(),
    );
  },
  get: (documentId: string, options: { limit?: number; afterChunkIndex?: number } = {}) => moreAiCustomerApi<CustomerKnowledgeDocumentDetail>(
    '/api/v1/customer/knowledge/documents/' + encodeURIComponent(documentId)
      + '?limit=' + Math.min(200, Math.max(1, options.limit ?? 100))
      + (options.afterChunkIndex === undefined ? '' : '&after_chunk_index=' + encodeURIComponent(String(options.afterChunkIndex))),
  ),
  chunksPage: (documentId: string, limit = 100, afterChunkIndex?: number) =>
    moreAiCustomerApi<CustomerKnowledgeDocumentDetail>(
      '/api/v1/customer/knowledge/documents/' + encodeURIComponent(documentId)
        + '?limit=' + Math.min(200, Math.max(1, limit))
        + (afterChunkIndex === undefined ? '' : '&after_chunk_index=' + encodeURIComponent(String(afterChunkIndex))),
    ),
  retry: (documentId: string) => moreAiCustomerApi<{ id: string; status: 'processing'; ingestion_state: 'queued' }>(
    '/api/v1/customer/knowledge/documents/' + encodeURIComponent(documentId) + '/retry',
    { method: 'POST' },
  ),
  reindex: (documentId: string) => moreAiCustomerApi<{ id: string; status: 'processing'; ingestion_state: 'queued' }>(
    '/api/v1/customer/knowledge/documents/' + encodeURIComponent(documentId) + '/reindex',
    { method: 'POST' },
  ),
  archive: (documentId: string) => moreAiCustomerApi<{ id: string; status: 'archived' }>(
    '/api/v1/customer/knowledge/documents/' + encodeURIComponent(documentId) + '/archive',
    { method: 'POST' },
  ),
};
