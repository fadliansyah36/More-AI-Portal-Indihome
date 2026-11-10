'use client';

import React, { useState } from 'react';
import { Play, RotateCcw, Copy, Check, Terminal, Code2, Sparkles, FolderGit2 } from 'lucide-react';

export const CodeView: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState<'editor' | 'projects'>('editor');
  const [code, setCode] = useState<string>(
`def greet(name):
    return f"Hello, {name}!"

# Eksekusi fungsi dengan nama platform
print(greet("MoreAI - Global Partner Network"))`
  );

  const [output, setOutput] = useState<string>('Hello, MoreAI - Global Partner Network!');
  const [isRunning, setIsRunning] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleRunCode = () => {
    setIsRunning(true);
    setTimeout(() => {
      setIsRunning(false);
      // Simulate real execution
      try {
        if (code.includes('print')) {
          const match = code.match(/print\((.*?)\)/);
          if (match) {
            const inner = match[1].replace(/["']/g, '');
            if (inner.includes('greet')) {
              setOutput('Hello, MoreAI - Global Partner Network!\n[Process completed successfully with exit code 0]');
            } else {
              setOutput(`${inner}\n[Process completed successfully with exit code 0]`);
            }
          } else {
            setOutput('Program executed successfully.');
          }
        } else {
          setOutput('[Process completed with no standard output]');
        }
      } catch {
        setOutput('Error executing snippet');
      }
    }, 600);
  };

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
          <p className="text-xs text-slate-500">Minta bantuan coding, generate script, dan uji langsung</p>
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
          {/* Quick Snippet Selector */}
          <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-1">
            <span className="text-[11px] text-slate-400 font-medium shrink-0">Snippet:</span>
            {sampleSnippets.map((s, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setCode(s.code);
                  setOutput('Klik "Run Code" untuk menjalankan snippet.');
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
                Sandboxed MicroVM Environment
              </span>
              <button
                onClick={handleRunCode}
                disabled={isRunning}
                className="flex items-center gap-1.5 px-4 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 active:scale-95 text-white text-xs font-bold transition shadow-xs"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>{isRunning ? 'Menjalankan...' : 'Run Code'}</span>
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
        <div className="p-6 text-center bg-white rounded-3xl border border-slate-100 text-slate-500 space-y-2">
          <FolderGit2 className="w-10 h-10 mx-auto text-slate-300" />
          <h3 className="text-sm font-bold text-slate-800">Proyek Script Terintegrasi</h3>
          <p className="text-xs text-slate-400 max-w-xs mx-auto">
            Proyek backend dan script otomasi disimpan otomatis di workspace MoreAI Anda.
          </p>
        </div>
      )}
    </div>
  );
};
