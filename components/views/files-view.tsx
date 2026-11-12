'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { Search, FileText, Image as ImageIcon, FileSpreadsheet, FileCode, ChevronRight, X, Loader2, FolderOpen } from 'lucide-react';
import { artifactApi, moreAiApi, workspaceApi, type CustomerWorkspaceFile } from '@/lib/api/client';

type ArtifactRecord = {
  id: string;
  storage_path: string;
  mime_type: string | null;
  size_bytes: number | null;
  checksum_sha256: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
};

type FileCategory = 'pdf' | 'docx' | 'image' | 'xlsx' | 'pptx' | 'code';

type ArtifactFile = {
  id: string;
  name: string;
  size: string;
  date: string;
  type: FileCategory;
  checksum: string | null;
};

const categoryFor = (mime: string | null, path: string): FileCategory => {
  const value = (mime || '').toLowerCase();
  const ext = path.split('.').pop()?.toLowerCase() || '';
  if (value === 'application/pdf' || ext === 'pdf') return 'pdf';
  if (value.includes('word') || ['doc', 'docx'].includes(ext)) return 'docx';
  if (value.startsWith('image/')) return 'image';
  if (value.includes('spreadsheet') || ['xls', 'xlsx', 'csv'].includes(ext)) return 'xlsx';
  if (value.includes('presentation') || ['ppt', 'pptx'].includes(ext)) return 'pptx';
  return 'code';
};

const formatSize = (bytes: number | null) => {
  if (bytes === null || !Number.isFinite(bytes)) return 'Ukuran tidak tersedia';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
};

export const FilesView: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<'semua' | FileCategory>('semua');
  const [files, setFiles] = useState<ArtifactFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<ArtifactFile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [workspaceFiles, setWorkspaceFiles] = useState<Array<CustomerWorkspaceFile & { workspaceId: string; workspaceName: string }>>([]);
  const [workspaceLoading, setWorkspaceLoading] = useState(true);
  const [workspaceError, setWorkspaceError] = useState<string | null>(null);
  const [downloadingFile, setDownloadingFile] = useState<string | null>(null);
  const [downloadingArtifact, setDownloadingArtifact] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    moreAiApi<ArtifactRecord[]>('/api/v1/artifacts')
      .then((rows) => {
        if (!active) return;
        setFiles(rows.map((row) => {
          const metadata = row.metadata || {};
          const name = typeof metadata.filename === 'string'
            ? metadata.filename
            : row.storage_path.split('/').pop() || row.storage_path;
          return {
            id: row.id,
            name,
            size: formatSize(row.size_bytes),
            date: new Date(row.created_at).toLocaleString('id-ID'),
            type: categoryFor(row.mime_type, row.storage_path),
            checksum: row.checksum_sha256,
          };
        }));
        setError(null);
      })
      .catch((cause) => {
        if (active) setError(cause instanceof Error ? cause.message : 'Gagal memuat artifact dari server.');
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);


  useEffect(() => {
    let active = true;
    workspaceApi.list()
      .then(async ({ items }) => {
        const groups = await Promise.all(items.map(async (workspace) => {
          const result = await workspaceApi.files(workspace.id);
          return result.items.map((file) => ({ ...file, workspaceId: workspace.id, workspaceName: workspace.name }));
        }));
        if (active) {
          setWorkspaceFiles(groups.flat());
          setWorkspaceError(null);
        }
      })
      .catch((cause) => {
        if (active) setWorkspaceError(cause instanceof Error ? cause.message : 'Gagal memuat file workspace.');
      })
      .finally(() => { if (active) setWorkspaceLoading(false); });
    return () => { active = false; };
  }, []);

  const downloadWorkspaceFile = async (file: CustomerWorkspaceFile & { workspaceId: string }) => {
    setDownloadingFile(file.id);
    try {
      const result = await workspaceApi.signedDownload(file.workspaceId, file.id);
      window.open(result.url, '_blank', 'noopener,noreferrer');
    } catch (cause) {
      setWorkspaceError(cause instanceof Error ? cause.message : 'Gagal membuat tautan unduhan.');
    } finally {
      setDownloadingFile(null);
    }
  };

  const downloadArtifact = async (file: ArtifactFile) => {
    setDownloadingArtifact(file.id);
    try {
      const result = await artifactApi.signedDownload(file.id);
      window.open(result.url, '_blank', 'noopener,noreferrer');
      setSelectedFile(null);
      setError(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Gagal membuat tautan unduhan artefak.');
    } finally {
      setDownloadingArtifact(null);
    }
  };

  const filteredFiles = useMemo(() => files.filter((file) => {
    const matchesSearch = file.name.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch && (filterType === 'semua' || file.type === filterType);
  }), [files, searchQuery, filterType]);

  const getFileIcon = (type: FileCategory) => {
    switch (type) {
      case 'pdf': return <FileText className="h-5 w-5 text-red-600" />;
      case 'docx': return <FileText className="h-5 w-5 text-blue-600" />;
      case 'image': return <ImageIcon className="h-5 w-5 text-amber-600" />;
      case 'xlsx': return <FileSpreadsheet className="h-5 w-5 text-emerald-600" />;
      case 'pptx': return <FileText className="h-5 w-5 text-orange-600" />;
      default: return <FileCode className="h-5 w-5 text-slate-600" />;
    }
  };

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-slate-900">File Saya & Library</h1>
        <p className="text-xs text-slate-500">Metadata artefak yang tersimpan pada workspace MoreAI.</p>
      </div>

      <div className="relative">
        <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.target.value)}
          placeholder="Cari nama artefak…"
          className="w-full rounded-2xl border border-slate-200 bg-white py-2.5 pl-10 pr-4 text-xs text-slate-900 shadow-2xs placeholder:text-slate-400 focus:border-red-500 focus:outline-none focus:ring-2 focus:ring-red-500/20 sm:text-sm"
        />
      </div>

      <div className="flex items-center gap-1.5 overflow-x-auto py-1">
        {([{ id: 'semua', label: 'Semua' }, { id: 'pdf', label: 'PDF' }, { id: 'docx', label: 'Dokumen' }, { id: 'image', label: 'Gambar' }, { id: 'xlsx', label: 'Spreadsheet' }, { id: 'pptx', label: 'Presentasi' }] as const).map((tab) => (
          <button key={tab.id} onClick={() => setFilterType(tab.id)} className={`whitespace-nowrap rounded-full px-3 py-1.5 text-xs font-medium transition ${filterType === tab.id ? 'bg-red-600 text-white' : 'border border-slate-200 bg-white text-slate-600 hover:bg-slate-50'}`}>
            {tab.label}
          </button>
        ))}
      </div>

      <div className="space-y-2">
        {loading ? (
          <div className="flex items-center justify-center gap-2 rounded-3xl border border-slate-100 bg-white p-10 text-sm text-slate-500"><Loader2 className="h-4 w-4 animate-spin" /> Memuat data artifact…</div>
        ) : error ? (
          <div role="alert" className="rounded-3xl border border-red-100 bg-white p-8 text-center text-sm text-red-600">{error}</div>
        ) : filteredFiles.length === 0 ? (
          <div className="rounded-3xl border border-slate-100 bg-white p-8 text-center text-slate-500">
            <FolderOpen className="mx-auto mb-2 h-10 w-10 text-slate-300" />
            <p className="text-xs font-medium">{files.length === 0 ? 'Belum ada artefak tersimpan pada akun ini.' : 'Tidak ada artefak yang cocok dengan pencarian.'}</p>
          </div>
        ) : filteredFiles.map((file) => (
          <button key={file.id} type="button" onClick={() => setSelectedFile(file)} className="group flex w-full items-center justify-between rounded-2xl border border-slate-100 bg-white p-3 text-left shadow-2xs transition hover:border-red-200">
            <span className="flex min-w-0 items-center gap-3">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-slate-100 bg-slate-50">{getFileIcon(file.type)}</span>
              <span className="min-w-0">
                <span className="block truncate text-xs font-bold text-slate-900 group-hover:text-red-600">{file.name}</span>
                <span className="mt-0.5 flex gap-2 text-[10px] text-slate-500"><span>{file.size}</span><span>·</span><span>{file.date}</span></span>
              </span>
            </span>
            <ChevronRight className="h-4 w-4 shrink-0 text-slate-300" />
          </button>
        ))}
      </div>


      <section className="space-y-3 pt-3">
        <div>
          <h2 className="text-sm font-bold text-slate-900">File Workspace Agent</h2>
          <p className="text-xs text-slate-500">File kerja yang tersimpan pada workspace aktif dan dibagikan melalui keanggotaan workspace.</p>
        </div>
        {workspaceLoading ? (
          <div className="rounded-2xl border border-slate-100 bg-white p-5 text-xs text-slate-500">Memuat file workspace…</div>
        ) : workspaceError ? (
          <div role="alert" className="rounded-2xl border border-red-100 bg-white p-4 text-xs text-red-600">{workspaceError}</div>
        ) : workspaceFiles.length === 0 ? (
          <div className="rounded-2xl border border-slate-100 bg-white p-5 text-xs text-slate-500">Belum ada file pada workspace yang dapat diakses.</div>
        ) : workspaceFiles.map((file) => (
          <div key={file.workspaceId + ':' + file.id} className="flex items-center justify-between gap-3 rounded-2xl border border-slate-100 bg-white p-3">
            <div className="min-w-0">
              <p className="truncate text-xs font-semibold text-slate-900">{file.path}</p>
              <p className="mt-1 truncate text-[10px] text-slate-500">{file.workspaceName} · v{file.version} · {formatSize(file.size_bytes)}</p>
            </div>
            <button
              type="button"
              disabled={!file.storage_path || downloadingFile === file.id}
              onClick={() => void downloadWorkspaceFile(file)}
              className="shrink-0 rounded-xl border border-slate-200 px-3 py-2 text-[10px] font-semibold text-slate-700 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {downloadingFile === file.id ? 'Menyiapkan…' : 'Unduh'}
            </button>
          </div>
        ))}
      </section>

      {selectedFile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs">
          <div className="w-full max-w-sm rounded-3xl border border-slate-100 bg-white p-5 text-slate-800 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex min-w-0 items-center gap-2">{getFileIcon(selectedFile.type)}<h3 className="truncate text-sm font-bold text-slate-900">{selectedFile.name}</h3></div>
              <button type="button" onClick={() => setSelectedFile(null)} aria-label="Tutup detail" className="rounded-lg p-1 text-slate-400 hover:bg-slate-100"><X className="h-5 w-5" /></button>
            </div>
            <div className="my-4 space-y-2 rounded-2xl border border-slate-100 bg-slate-50 p-4 text-xs text-slate-600">
              <div className="flex justify-between gap-3"><span className="text-slate-400">Ukuran</span><span>{selectedFile.size}</span></div>
              <div className="flex justify-between gap-3"><span className="text-slate-400">Dibuat</span><span>{selectedFile.date}</span></div>
              <div className="flex justify-between gap-3"><span className="text-slate-400">SHA-256</span><span className="max-w-[60%] truncate">{selectedFile.checksum || 'Belum tersedia'}</span></div>
            </div>
            <div className="flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => setSelectedFile(null)}
                className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600"
              >
                Tutup
              </button>
              <button
                type="button"
                disabled={downloadingArtifact === selectedFile.id}
                onClick={() => void downloadArtifact(selectedFile)}
                className="rounded-xl bg-red-600 px-3 py-2 text-xs font-semibold text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {downloadingArtifact === selectedFile.id ? 'Menyiapkan…' : 'Unduh artefak'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
