import { moreAiCustomerApi } from '@/lib/api/client';

export type CustomerKnowledgeDocument = {
  id: string;
  title: string;
  workspace_id: string | null;
  source_type: 'text' | 'file' | 'url';
  source_ref: string | null;
  content_sha256: string;
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
  get: (documentId: string) => moreAiCustomerApi<{
    document: CustomerKnowledgeDocument;
    chunks: CustomerKnowledgeChunk[];
    chunk_count: number;
  }>('/api/v1/customer/knowledge/documents/' + encodeURIComponent(documentId)),
  archive: (documentId: string) => moreAiCustomerApi<{ id: string; status: 'archived' }>(
    '/api/v1/customer/knowledge/documents/' + encodeURIComponent(documentId) + '/archive',
    { method: 'POST' },
  ),
};
