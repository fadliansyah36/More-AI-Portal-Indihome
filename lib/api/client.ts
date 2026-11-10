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
  headers.set('Authorization', `Bearer ${data.session.access_token}`);
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    cache: 'no-store',
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const message = payload?.detail || payload?.error?.message || `MoreAI API error (${response.status})`;
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}
