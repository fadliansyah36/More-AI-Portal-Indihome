'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { Search, FileText, Image as ImageIcon, FileSpreadsheet, FileCode, ChevronRight, X, Loader2, FolderOpen, UploadCloud } from 'lucide-react';
import { artifactApi, workspaceApi, type CustomerWorkspace, type CustomerWorkspaceFile, type CustomerWorkspaceFileVersion } from '@/lib/api/client';

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
  const [workspaces, setWorkspaces] = useState<CustomerWorkspace[]>([]);
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState('');
  const [uploadingWorkspaceFile, setUploadingWorkspaceFile] = useState(false);
  const [workspaceUploadMessage, setWorkspaceUploadMessage] = useState<string | null>(null);
  const [workspaceFiles, setWorkspaceFiles] = useState<Array<CustomerWorkspaceFile & { workspaceId: string; workspaceName: string }>>([]);
  const [workspaceLoading, setWorkspaceLoading] = useState(true);
  const [workspaceError, setWorkspaceError] = useState<string | null>(null);
  const [downloadingFile, setDownloadingFile] = useState<string | null>(null);
  const [downloadingArtifact, setDownloadingArtifact] = useState<string | null>(null);
  const [uploadingArtifact, setUploadingArtifact] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [historyFile, setHistoryFile] = useState<(CustomerWorkspaceFile & { workspaceId: string; workspaceName: string }) | null>(null);
  const [fileVersions, setFileVersions] = useState<CustomerWorkspaceFileVersion[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [downloadingVersion, setDownloadingVersion] = useState<number | null>(null);

  useEffect(() => {
    let active = true;
    artifactApi.list()
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
        if (active) {
          setWorkspaces(items);
          setSelectedWorkspaceId((current) => current || items[0]?.id || '');
        }
        const groups = await Promise.allSettled(items.map(async (workspace) => {
          const result = await workspaceApi.files(workspace.id);
          return result.items.map((file) => ({ ...file, workspaceId: workspace.id, workspaceName: workspace.name }));
        }));
        if (active) {
          setWorkspaceFiles(groups.flatMap((group) => group.status === 'fulfilled' ? group.value : []));
          setWorkspaceError(groups.some((group) => group.status === 'rejected')
            ? 'Sebagian file workspace gagal dimuat. File dari workspace lain yang berhasil tetap ditampilkan.'
            : null);
        }
      })
      .catch((cause) => {
        if (active) setWorkspaceError(cause instanceof Error ? cause.message : 'Gagal memuat file workspace.');
      })
      .finally(() => { if (active) setWorkspaceLoading(false); });
    return () => { active = false; };
  }, []);

  const uploadWorkspaceFile = async (file: File) => {
    if (!selectedWorkspaceId) {
      setWorkspaceError('Pilih workspace terlebih dahulu sebelum mengunggah file.');
      return;
    }
    if (file.size < 1 || file.size > 2_000_000) {
      setWorkspaceError('File workspace harus berukuran 1 byte hingga 2 MB.');
      return;
    }
    if (!/^[A-Za-z0-9][A-Za-z0-9._ -]{0,179}$/.test(file.name) || file.name === '.' || file.name === '..') {
      setWorkspaceError('Nama file hanya boleh menggunakan huruf Latin, angka, titik, garis bawah, spasi, atau tanda hubung.');
      return;
    }
    const workspace = workspaces.find((item) => item.id === selectedWorkspaceId);
    if (!workspace) {
      setWorkspaceError('Workspace yang dipilih tidak lagi tersedia. Muat ulang halaman.');
      return;
    }
    const existing = workspaceFiles.find((item) => item.workspaceId === selectedWorkspaceId && item.path === file.name);
    setUploadingWorkspaceFile(true);
    setWorkspaceUploadMessage(null);
    setWorkspaceError(null);
    try {
      await workspaceApi.uploadFile(
        selectedWorkspaceId,
        file.name,
        existing?.version ?? 0,
        file,
        crypto.randomUUID(),
      );
      const refreshed = await workspaceApi.files(selectedWorkspaceId);
      setWorkspaceFiles((current) => [
        ...current.filter((item) => item.workspaceId !== selectedWorkspaceId),
        ...refreshed.items.map((item) => ({
          ...item,
          workspaceId: selectedWorkspaceId,
          workspaceName: workspace.name,
        })),
      ]);
      setWorkspaceUploadMessage('File tersimpan sebagai versi baru pada workspace yang dipilih.');
    } catch (cause) {
      // Reconcile local CAS version after conflicts or ambiguous network failures.
      // The server may have committed the immutable version even if its response was lost.
      try {
        const refreshed = await workspaceApi.files(selectedWorkspaceId);
        setWorkspaceFiles((current) => [
          ...current.filter((item) => item.workspaceId !== selectedWorkspaceId),
          ...refreshed.items.map((item) => ({
            ...item,
            workspaceId: selectedWorkspaceId,
            workspaceName: workspace.name,
          })),
        ]);
      } catch {
        // Preserve the original upload error; a later explicit reload can recover.
      }
      setWorkspaceError(cause instanceof Error ? cause.message : 'Upload workspace gagal diproses oleh server.');
    } finally {
      setUploadingWorkspaceFile(false);
    }
  };

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

  const openVersionHistory = async (file: CustomerWorkspaceFile & { workspaceId: string; workspaceName: string }) => {
    setHistoryFile(file); setHistoryLoading(true); setHistoryError(null); setFileVersions([]);
    try { const result = await workspaceApi.versions(file.workspaceId, file.id); setFileVersions(result.items); }
    catch (cause) { setHistoryError(cause instanceof Error ? cause.message : 'Gagal memuat riwayat versi file.'); }
    finally { setHistoryLoading(false); }
  };

  const downloadWorkspaceVersion = async (version: number) => {
    if (!historyFile) return;
    setDownloadingVersion(version);
    try { const result = await workspaceApi.signedDownload(historyFile.workspaceId, historyFile.id, version); window.open(result.url, '_blank', 'noopener,noreferrer'); }
    catch (cause) { setHistoryError(cause instanceof Error ? cause.message : 'Gagal mengunduh versi file.'); }
    finally { setDownloadingVersion(null); }
  };
  const uploadArtifactFile = async (file: File) => {
    if (file.size < 1 || file.size > 2_000_000) {
      setError('File artefak harus berukuran 1 byte hingga 2 MB.');
      return;
    }
    if (!/^[A-Za-z0-9][A-Za-z0-9._ -]{0,179}$/.test(file.name) || file.name === '.' || file.name === '..') {
      setError('Nama file harus menggunakan huruf Latin, angka, titik, garis bawah, spasi, atau tanda hubung.');
      return;
    }
    setUploadingArtifact(true);
    setUploadMessage(null);
    setError(null);
    try {
      await artifactApi.upload(file.name, file, file.type || 'application/octet-stream');
      const rows = await artifactApi.list();
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
      setUploadMessage('File berhasil disimpan sebagai artefak privat pada akun Anda.');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Upload artefak gagal diproses oleh server.');
    } finally {
      setUploadingArtifact(false);
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
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">File Saya & Library</h1>
          <p className="text-xs text-slate-500">Metadata artefak yang tersimpan pada workspace MoreAI.</p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <label className="inline-flex cursor-pointer items-center gap-1.5 rounded-xl bg-red-600 px-3 py-2 text-xs font-semibold text-white transition hover:bg-red-700">
            <UploadCloud className="h-3.5 w-3.5" />
            {uploadingArtifact ? 'Mengunggah…' : 'Unggah file'}
            <input
              type="file"
              className="hidden"
              disabled={uploadingArtifact}
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) void uploadArtifactFile(file);
                event.currentTarget.value = '';
              }}
            />
          </label>
          <Link href="/customer/knowledge" className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold text-red-700 transition hover:bg-red-100">
            Knowledge Library
          </Link>
        </div>
      </div>

      {uploadMessage && <div role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-800">{uploadMessage}</div>}
      {uploadingArtifact && <div role="status" className="rounded-xl border border-slate-200 bg-white p-3 text-xs text-slate-600">Mengirim file ke private Artifact Storage…</div>}

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
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-sm font-bold text-slate-900">File Workspace Agent</h2>
            <p className="text-xs text-slate-500">File kerja yang tersimpan sebagai versi immutable pada workspace yang dapat Anda akses.</p>
          </div>
          <div className="flex items-center gap-2">
            <select
              aria-label="Pilih workspace untuk upload"
              value={selectedWorkspaceId}
              onChange={(event) => setSelectedWorkspaceId(event.target.value)}
              disabled={workspaces.length === 0 || uploadingWorkspaceFile}
              className="max-w-44 rounded-xl border border-slate-200 bg-white px-2.5 py-2 text-xs text-slate-700 disabled:opacity-50"
            >
              {workspaces.length === 0 ? <option value="">Tidak ada workspace</option> : workspaces.map((workspace) => (
                <option key={workspace.id} value={workspace.id}>{workspace.name}</option>
              ))}
            </select>
            <label className="inline-flex cursor-pointer items-center gap-1.5 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold text-red-700 transition hover:bg-red-100">
              <UploadCloud className="h-3.5 w-3.5" />
              {uploadingWorkspaceFile ? 'Mengunggah…' : 'Upload workspace'}
              <input
                type="file"
                className="hidden"
                disabled={uploadingWorkspaceFile || workspaces.length === 0}
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) void uploadWorkspaceFile(file);
                  event.currentTarget.value = '';
                }}
              />
            </label>
          </div>
        </div>
        {workspaceUploadMessage && <div role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-800">{workspaceUploadMessage}</div>}
        {uploadingWorkspaceFile && <div role="status" className="rounded-xl border border-slate-200 bg-white p-3 text-xs text-slate-600">Mengunggah file ke Storage privat dan mengunci versi metadata…</div>}
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
            <div className="flex shrink-0 items-center gap-1.5">
              <button type="button" onClick={() => void openVersionHistory(file)} className="rounded-xl border border-slate-200 px-3 py-2 text-[10px] font-semibold text-slate-700 transition hover:bg-slate-50">Riwayat</button>
              <button type="button" disabled={!file.storage_path || downloadingFile === file.id} onClick={() => void downloadWorkspaceFile(file)} className="rounded-xl border border-slate-200 px-3 py-2 text-[10px] font-semibold text-slate-700 disabled:cursor-not-allowed disabled:opacity-40">
                {downloadingFile === file.id ? 'Menyiapkan…' : 'Unduh'}
              </button>
            </div>
          </div>
        ))}
      </section>

      {historyFile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs">
          <div className="w-full max-w-lg rounded-3xl border border-slate-100 bg-white p-5 text-slate-800 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3"><div className="min-w-0"><h3 className="truncate text-sm font-bold text-slate-900">Riwayat versi file</h3><p className="mt-1 truncate text-[10px] text-slate-500">{historyFile.workspaceName} · {historyFile.path}</p></div><button type="button" onClick={() => setHistoryFile(null)} aria-label="Tutup riwayat versi" className="rounded-lg p-1 text-slate-400 hover:bg-slate-100"><X className="h-5 w-5" /></button></div>
            <div className="mt-4 max-h-[55vh] space-y-2 overflow-y-auto">
              {historyLoading ? <div className="flex items-center gap-2 rounded-2xl bg-slate-50 p-5 text-xs text-slate-500"><Loader2 className="h-4 w-4 animate-spin" /> Memuat riwayat versi…</div> : historyError ? <div role="alert" className="rounded-2xl border border-red-100 bg-red-50 p-4 text-xs text-red-600">{historyError}</div> : fileVersions.length === 0 ? <div className="rounded-2xl bg-slate-50 p-5 text-xs text-slate-500">Belum ada riwayat versi tersimpan.</div> : fileVersions.map((version) => (
                <div key={version.id + ':' + version.version} className="flex items-center justify-between gap-3 rounded-2xl border border-slate-100 p-3"><div className="min-w-0"><p className="text-xs font-semibold text-slate-900">Versi {version.version}{version.current ? ' · Saat ini' : ''}</p><p className="mt-1 text-[10px] text-slate-500">{formatSize(version.size_bytes)} · {new Date(version.committed_at).toLocaleString('id-ID')}</p><p className="mt-1 truncate text-[10px] text-slate-400">SHA-256: {version.sha256}</p></div><button type="button" disabled={downloadingVersion === version.version} onClick={() => void downloadWorkspaceVersion(version.version)} className="shrink-0 rounded-xl border border-slate-200 px-3 py-2 text-[10px] font-semibold text-slate-700 disabled:opacity-50">{downloadingVersion === version.version ? 'Menyiapkan…' : 'Unduh'}</button></div>
              ))}
            </div>
            <div className="mt-4 flex justify-end"><button type="button" onClick={() => setHistoryFile(null)} className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600">Tutup</button></div>
          </div>
        </div>
      )}
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
