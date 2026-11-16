'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { artifactApi, browserSessionApi, type CustomerBrowserPreviewRequest } from '@/lib/api/client';

type ReconnectStatus = 'loading' | 'active' | 'close_requested' | 'closed' | 'expired' | 'unavailable';
type PreviewState = {
  status: 'idle' | 'queued' | 'processing' | 'succeeded' | 'failed' | 'expired';
  requestId: string | null;
  error: string | null;
  imageUrl: string | null;
  artifactId: string | null;
  createdAt: string | null;
};

const POLL_INTERVAL_MS = 1800;
const MAX_POLL_DURATION_MS = 90_000;

export function useBrowserSessionPreview(sessionId: string | null) {
  const [reconnectStatus, setReconnectStatus] = useState<ReconnectStatus>('loading');
  const [preview, setPreview] = useState<PreviewState>({
    status: 'idle', requestId: null, error: null, imageUrl: null, artifactId: null, createdAt: null,
  });
  const [refreshing, setRefreshing] = useState(false);
  const mounted = useRef(false);
  const pollGeneration = useRef(0);

  const loadSignedPreview = useCallback(async (artifactId: string) => {
    const download = await artifactApi.signedDownload(artifactId);
    setPreview((current) => ({ ...current, imageUrl: download.url, artifactId }));
  }, []);

  const restore = useCallback(async () => {
    if (!sessionId) {
      setReconnectStatus('unavailable');
      return;
    }
    setReconnectStatus('loading');
    try {
      const state = await browserSessionApi.state(sessionId);
      if (!mounted.current) return;
      setReconnectStatus(state.session.effective_status);
      const request = state.preview_request;
      setPreview({
        status: request?.status ?? 'idle',
        requestId: request?.id ?? null,
        error: request?.error_code ?? null,
        imageUrl: null,
        artifactId: null,
        createdAt: request?.created_at ?? null,
      });
      if (state.session.effective_status === 'active' && state.preview?.artifact_id) {
        await loadSignedPreview(state.preview.artifact_id);
      }
    } catch (error) {
      if (!mounted.current) return;
      setReconnectStatus('unavailable');
      setPreview((current) => ({
        ...current,
        error: error instanceof Error ? error.message : 'browser_session_reconnect_failed',
      }));
    }
  }, [sessionId, loadSignedPreview]);

  const pollRequest = useCallback(async (requestId: string, generation: number) => {
    const startedAt = Date.now();
    while (mounted.current && generation === pollGeneration.current) {
      if (Date.now() - startedAt > MAX_POLL_DURATION_MS) {
        setPreview((current) => ({ ...current, error: 'browser_preview_poll_timeout' }));
        setRefreshing(false);
        return;
      }
      try {
        const request: CustomerBrowserPreviewRequest = await browserSessionApi.previewRequest(requestId);
        if (!mounted.current || generation !== pollGeneration.current) return;
        setPreview((current) => ({
          ...current, status: request.status, error: request.error_code,
          requestId: request.id, createdAt: request.created_at,
        }));
        if (request.status === 'succeeded' && request.artifact_id) {
          await loadSignedPreview(request.artifact_id);
          setRefreshing(false);
          return;
        }
        if (request.status === 'failed' || request.status === 'expired') {
          setRefreshing(false);
          return;
        }
      } catch (error) {
        if (!mounted.current || generation !== pollGeneration.current) return;
        setPreview((current) => ({
          ...current, error: error instanceof Error ? error.message : 'browser_preview_status_unavailable',
        }));
      }
      await new Promise((resolve) => window.setTimeout(resolve, POLL_INTERVAL_MS));
    }
  }, [loadSignedPreview]);

  const refresh = useCallback(async () => {
    if (!sessionId || reconnectStatus !== 'active' || refreshing) return;
    const generation = ++pollGeneration.current;
    setRefreshing(true);
    setPreview((current) => ({
      ...current, status: 'queued', requestId: null, error: null,
    }));
    try {
      const queued = await browserSessionApi.requestPreview(sessionId);
      if (!mounted.current || generation !== pollGeneration.current) return;
      setPreview((current) => ({
        ...current, status: queued.status, requestId: queued.request_id, error: null,
      }));
      // The requestId/status state transition starts the single reconnect poll effect.
    } catch (error) {
      if (!mounted.current || generation !== pollGeneration.current) return;
      setPreview((current) => ({
        ...current, status: 'failed',
        error: error instanceof Error ? error.message : 'browser_preview_request_failed',
      }));
      setRefreshing(false);
    }
  }, [sessionId, reconnectStatus, refreshing, pollRequest]);

  useEffect(() => {
    mounted.current = true;
    void restore();
    return () => {
      mounted.current = false;
      pollGeneration.current += 1;
    };
  }, [restore]);

  useEffect(() => {
    if (preview.requestId && (preview.status === 'queued' || preview.status === 'processing')) {
      const generation = ++pollGeneration.current;
      setRefreshing(true);
      void pollRequest(preview.requestId, generation);
      return () => { pollGeneration.current += 1; };
    }
    return undefined;
  }, [preview.requestId, preview.status, pollRequest]);

  const renewSignedPreviewUrl = useCallback(async () => {
    if (!preview.artifactId) return;
    try {
      await loadSignedPreview(preview.artifactId);
    } catch (error) {
      setPreview((current) => ({
        ...current, error: error instanceof Error ? error.message : 'browser_preview_download_failed',
      }));
    }
  }, [preview.artifactId, loadSignedPreview]);

  return {
    reconnectStatus, preview, refreshing,
    refresh, restore, renewSignedPreviewUrl,
  };
}
