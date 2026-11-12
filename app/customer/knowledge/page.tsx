'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { createSupabaseBrowserClient } from '@/lib/supabase/client';
import { KnowledgeLibraryView } from '@/components/views/knowledge-library-view';

export default function CustomerKnowledgePage() {
  const router = useRouter();
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    let active = true;
    createSupabaseBrowserClient().auth.getSession().then(({ data, error }) => {
      if (!active) return;
      if (error || !data.session) {
        router.replace('/customer/login');
        return;
      }
      setAuthorized(true);
    });
    return () => { active = false; };
  }, [router]);

  if (!authorized) {
    return <main className="flex min-h-screen items-center justify-center bg-slate-50 text-sm text-slate-500">Memeriksa sesi Customer…</main>;
  }

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-6 sm:px-6">
      <div className="mx-auto max-w-4xl">
        <a href="/customer" className="mb-5 inline-flex text-xs font-semibold text-slate-600 hover:text-red-600">← Kembali ke MoreAI</a>
        <KnowledgeLibraryView />
      </div>
    </main>
  );
}
