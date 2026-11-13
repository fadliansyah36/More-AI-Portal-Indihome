'use client';

import React, { useEffect, useState } from 'react';
import { Play, Copy, Check, Terminal, Code2, FolderGit2, Save, Download, Loader2 } from 'lucide-react';
import { artifactApi, customerApi, type CustomerAgentRun, type CustomerArtifact } from '@/lib/api/client';

interface CodeViewProps { onNavigateToChat?: (prompt: string) => void; }

export const CodeView: React.FC<CodeViewProps> = ({ onNavigateToChat }) => {
  const [activeSubTab, setActiveSubTab] = useState<'editor' | 'projects'>('editor');
  const [code, setCode] = useState<string>(
`def greet(name):
    return f"Hello, {name}!"

# Eksekusi fungsi dengan nama platform
print(greet("MoreAI - Global Partner Network"))`
  );

  const [output, setOutput] = useState<string>('Sandbox eksekusi belum diaktifkan. Kode tidak akan dijalankan pada browser.');
  const [isRunning, setIsRunning] = useState(false);
  const [copied, setCopied] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [savedProjects, setSavedProjects] = useState<CustomerArtifact[]>([]);
  const [availableRuns, setAvailableRuns] = useState<CustomerAgentRun[]>([]);
  const [selectedRunId, setSelectedRunId] = useState('');
  const [projectsLoading, setProjectsLoading] = useState(false);
  const [projectsError, setProjectsError] = useState<string | null>(null);
  const [downloadingProject, setDownloadingProject] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    customerApi.agentRuns().then((items) => {
      if (active) setAvailableRuns(items);
    }).catch(() => {
      // The run selector remains empty when history is unavailable; uploads can
      // still be saved without a run association.
    });
    return () => { active = false; };
  }, []);

  const handleRunCode = () => {
    if (!code.trim() || isRunning) return;
    if (!onNavigateToChat) {
      setOutput('Chat AI belum tersedia pada layar ini. Kode tidak dijalankan.');
      return;
    }
    setIsRunning(true);
    onNavigateToChat('Tinjau kode Python berikut menggunakan Agent MoreAI. Jelaskan tujuan, potensi bug, risiko keamanan, dan usulkan perbaikan. Jangan mengklaim kode sudah dieksekusi.\n\n```python\n' + code + '\n```');
    setOutput('Kode dikirim sebagai permintaan analisis ke Chat AI. Tidak ada proses Python yang dieksekusi pada sandbox.');
    setIsRunning(false);
  };

  useEffect(() => {
    if (activeSubTab !== 'projects') return;
    let active = true;
    setProjectsLoading(true);
    Promise.allSettled([artifactApi.list(), customerApi.agentRuns()]).then(([artifacts, runs]) => {
      if (!active) return;
      if (artifacts.status === 'fulfilled') {
        setSavedProjects(artifacts.value);
        setProjectsError(null);
      } else {
        setProjectsError(artifacts.reason instanceof Error ? artifacts.reason.message : 'Snapshot kode tidak dapat dimuat.');
      }
      if (runs.status === 'fulfilled') setAvailableRuns(runs.value);
    }).finally(() => {
      if (active) setProjectsLoading(false);
    });
    return () => { active = false; };
  }, [activeSubTab]);

  const saveCodeSnapshot = async () => {
    if (!code.trim() || isSaving) return;
    if (new Blob([code]).size > 2_000_000) {
      setOutput('Snapshot kode melebihi batas penyimpanan artefak 2 MB.');
      return;
    }
    setIsSaving(true);
    try {
      await artifactApi.upload('main.py', new Blob([code], { type: 'text/x-python' }), 'text/x-python', selectedRunId || undefined);
      setSavedProjects(await artifactApi.list());
      setProjectsError(null);
      setOutput(selectedRunId
        ? 'Snapshot main.py tersimpan dan ditautkan ke Agent Run ' + selectedRunId.slice(0, 8) + '. Kode tidak dieksekusi.'
        : 'Snapshot main.py berhasil disimpan sebagai artefak privat tanpa tautan Agent Run. Kode tidak dieksekusi.');
    } catch (cause) {
      setOutput(cause instanceof Error ? cause.message : 'Snapshot kode gagal disimpan.');
    } finally {
      setIsSaving(false);
    }
  };

  const downloadCodeSnapshot = async (artifactId: string) => {
    if (downloadingProject) return;
    setDownloadingProject(artifactId);
    try {
      const result = await artifactApi.signedDownload(artifactId);
      window.open(result.url, '_blank', 'noopener,noreferrer');
    } catch (cause) {
      setProjectsError(cause instanceof Error ? cause.message : 'Snapshot kode gagal diunduh.');
    } finally {
      setDownloadingProject(null);
    }
  };

  const codeProjects = savedProjects.filter((artifact) => {
    const filename = typeof artifact.metadata?.filename === 'string' ? artifact.metadata.filename : '';
    return /\.(py|js|jsx|ts|tsx|json|md|sql|sh|yaml|yml|toml)$/i.test(filename);
  });

  const sampleSnippets = [
    {
      name: 'Greeting Default',
      code: `def greet(name):\n    return f"Hello, {name}!"\n\nprint(greet("MoreAI - Global Partner Network"))`,
    },
    {
      name: 'Kalkulator AI Quota',
      code: `def hitung_sisa(quota, used):\n    return quota - used\n\nprint(f"Sisa Kuota: {hitung_sisa(100000, 15000)} Poin")`,
    },
    {
      name: 'Loop Data Pelanggan',
      code: `pelanggan = ["CoffeeHouse", "Resto Nusantara", "Coworking Hub"]\nfor p in pelanggan:\n    print(f"Partner Wi-Fi Aktif: {p}")`,
    },
  ];

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Code Assistant & Sandbox</h1>
          <p className="text-xs text-slate-500">Bantuan coding, analisis AI, dan penyimpanan snapshot kode</p>
        </div>
      </div>

      {/* Editor / Projects Toggle */}
      <div className="flex items-center gap-1 p-1 bg-white rounded-2xl border border-slate-200 shadow-2xs">
        <button
          onClick={() => setActiveSubTab('editor')}
          className={`flex-1 py-1.5 text-xs font-semibold rounded-xl flex items-center justify-center gap-1.5 transition ${
            activeSubTab === 'editor'
              ? 'bg-red-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Code2 className="w-3.5 h-3.5" />
          <span>Editor Python</span>
        </button>
        <button
          onClick={() => setActiveSubTab('projects')}
          className={`flex-1 py-1.5 text-xs font-semibold rounded-xl flex items-center justify-center gap-1.5 transition ${
            activeSubTab === 'projects'
              ? 'bg-red-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <FolderGit2 className="w-3.5 h-3.5" />
          <span>Proyek Tersimpan</span>
        </button>
      </div>

      {activeSubTab === 'editor' ? (
        <div className="space-y-3">
          <div className="rounded-xl border border-slate-200 bg-white p-3 space-y-1.5">
            <label htmlFor="code-artifact-run" className="block text-[11px] font-semibold text-slate-700">Hubungkan snapshot dengan Agent Run</label>
            <select id="code-artifact-run" value={selectedRunId} onChange={(event) => setSelectedRunId(event.target.value)} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700">
              <option value="">Simpan tanpa tautan run</option>
              {availableRuns.map((run) => {
                const prompt = run.input?.prompt;
                const label = typeof prompt === 'string' && prompt.trim() ? prompt.trim().slice(0, 72) : 'Agent Run ' + run.id.slice(0, 8);
                return <option key={run.id} value={run.id}>{label} · {run.status}</option>;
              })}
            </select>
            <p className="text-[10px] text-slate-500">Run dipilih dari riwayat akun dan diverifikasi ulang oleh FastAPI sebelum artefak ditautkan.</p>
          </div>
          {/* Quick Snippet Selector */}
          <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-1">
            <span className="text-[11px] text-slate-400 font-medium shrink-0">Snippet:</span>
            {sampleSnippets.map((s, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setCode(s.code);
                  setOutput('Snippet dimuat. Pilih Analisis dengan AI untuk meminta review; kode belum dieksekusi.');
                }}
                className="px-2.5 py-1 rounded-xl bg-white hover:bg-red-50 text-slate-700 hover:text-red-600 border border-slate-200 text-[11px] font-semibold whitespace-nowrap transition active:scale-95 shrink-0"
              >
                {s.name}
              </button>
            ))}
          </div>

          {/* Code Editor Window (Exact layout from Sheet 2) */}
          <div className="rounded-3xl bg-slate-950 border border-slate-800 overflow-hidden shadow-lg text-white">
            <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900/90 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-red-500/80" />
                  <div className="w-3 h-3 rounded-full bg-amber-500/80" />
                  <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
                </div>
                <span className="text-xs font-mono text-slate-400 ml-2">main.py (Python 3.12)</span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => void saveCodeSnapshot()}
                  disabled={isSaving || !code.trim()}
                  className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-[10px] font-semibold text-slate-300 transition hover:bg-slate-800 hover:text-white disabled:opacity-50"
                  title="Simpan snapshot kode ke artefak privat"
                >
                  {isSaving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
                  Simpan
                </button>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(code);
                    setCopied(true);
                    setTimeout(() => setCopied(false), 2000);
                  }}
                  className="p-1 rounded text-slate-400 hover:text-white transition"
                  title="Salin Kode"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>

            {/* Code Textarea with line numbers feeling */}
            <div className="p-3.5 flex font-mono text-xs leading-relaxed bg-slate-950">
              <div className="text-slate-600 select-none pr-3 text-right shrink-0">
                1<br />2<br />3<br />4<br />5
              </div>
              <textarea
                value={code}
                onChange={(e) => setCode(e.target.value)}
                rows={5}
                spellCheck={false}
                className="w-full bg-transparent text-emerald-400 focus:outline-none resize-none font-mono selection:bg-slate-800"
              />
            </div>

            {/* Action Bar */}
            <div className="px-4 py-2.5 bg-slate-900/80 border-t border-slate-800 flex items-center justify-between">
              <span className="text-[11px] text-slate-400 font-sans">
                Eksekusi sandbox dinonaktifkan hingga supervisor dan approval gate siap
              </span>
              <button
                onClick={handleRunCode}
                disabled={isRunning}
                className="flex items-center gap-1.5 px-4 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 active:scale-95 text-white text-xs font-bold transition shadow-xs"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>{isRunning ? 'Mengirim...' : 'Analisis dengan AI'}</span>
              </button>
            </div>
          </div>

          {/* Hasil Output Terminal (Exact from Sheet 2) */}
          <div className="rounded-3xl bg-slate-900 border border-slate-800 p-4 text-white shadow-xs space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-400 pb-1.5 border-b border-slate-800">
              <span className="flex items-center gap-1.5 font-mono">
                <Terminal className="w-3.5 h-3.5 text-emerald-400" />
                <span>Hasil Output:</span>
              </span>
              <button
                onClick={() => setOutput('')}
                className="text-[10px] text-slate-400 hover:text-white"
              >
                Clear
              </button>
            </div>
            <pre className="font-mono text-xs text-emerald-400 whitespace-pre-wrap min-h-[48px]">
              {output || '(Output kosong)'}
            </pre>
          </div>
        </div>
      ) : (
        <div className="rounded-3xl border border-slate-100 bg-white p-4 text-slate-600 shadow-2xs space-y-3">
          <div>
            <h3 className="text-sm font-bold text-slate-800">Snapshot Kode Tersimpan</h3>
            <p className="mt-1 text-xs text-slate-500">Snapshot disimpan sebagai artefak privat akun dan dapat diunduh kembali. Penyimpanan ini belum merupakan repository Git atau file workspace berversi.</p>
          </div>
          {projectsLoading ? (
            <div className="flex items-center justify-center gap-2 py-6 text-xs text-slate-500"><Loader2 className="h-4 w-4 animate-spin" /> Memuat snapshot…</div>
          ) : projectsError ? (
            <div role="alert" className="rounded-xl border border-red-100 bg-red-50 p-3 text-xs text-red-700">{projectsError}</div>
          ) : codeProjects.length === 0 ? (
            <div className="rounded-2xl bg-slate-50 p-5 text-center text-xs text-slate-500">Belum ada snapshot kode yang tersimpan pada akun ini.</div>
          ) : (
            <div className="space-y-2">
              {codeProjects.map((artifact) => {
                const filename = typeof artifact.metadata?.filename === 'string' ? artifact.metadata.filename : 'File kode';
                const size = artifact.size_bytes == null ? 'Ukuran tidak tersedia' : artifact.size_bytes < 1024 ? artifact.size_bytes + ' B' : (artifact.size_bytes / 1024).toFixed(1) + ' KB';
                return (
                  <div key={artifact.id} className="flex items-center justify-between gap-3 rounded-2xl border border-slate-100 p-3">
                    <div className="min-w-0">
                      <p className="truncate text-xs font-semibold text-slate-900">{filename}</p>
                      <p className="mt-1 text-[10px] text-slate-500">{size} · {new Date(artifact.created_at).toLocaleString('id-ID')}</p>
                      {artifact.run_id && <p className="mt-1 text-[10px] font-medium text-blue-700">Agent Run: {artifact.run_id.slice(0, 8)}</p>}
                    </div>
                    <button type="button" onClick={() => void downloadCodeSnapshot(artifact.id)} disabled={downloadingProject === artifact.id} className="inline-flex shrink-0 items-center gap-1 rounded-xl border border-slate-200 px-3 py-2 text-[10px] font-semibold text-slate-700 disabled:opacity-50">
                      {downloadingProject === artifact.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />}
                      Unduh
                    </button>
                  </div>
                );
              })}
            </div>
          )}
          <button type="button" onClick={() => setActiveSubTab('editor')} className="text-xs font-semibold text-red-600 hover:text-red-700">Kembali ke editor</button>
        </div>
      )}
    </div>
  );
};
