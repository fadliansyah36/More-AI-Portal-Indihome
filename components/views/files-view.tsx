'use client';

import React, { useState } from 'react';
import {
  Search,
  Folder,
  FileText,
  Image as ImageIcon,
  FileSpreadsheet,
  FileCode,
  Upload,
  Download,
  Share2,
  Trash2,
  Plus,
  Eye,
  X,
  ChevronRight,
} from 'lucide-react';
import { ARTIFACT_FILES } from '@/lib/data';
import { ArtifactFile } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';

export const FilesView: React.FC = () => {
  const { showToast } = useToast();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<'semua' | 'pdf' | 'docx' | 'image' | 'xlsx' | 'pptx'>('semua');
  const [files, setFiles] = useState<ArtifactFile[]>(ARTIFACT_FILES);
  const [selectedFile, setSelectedFile] = useState<ArtifactFile | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const filteredFiles = files.filter((file) => {
    const matchesSearch = file.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = filterType === 'semua' ? true : file.type === filterType;
    return matchesSearch && matchesType;
  });

  const handleSimulateUpload = () => {
    setIsUploading(true);
    setTimeout(() => {
      const newFile: ArtifactFile = {
        id: `file-${Date.now()}`,
        name: `Dokumen_AI_Baru_${new Date().toLocaleDateString('id-ID').replace(/\//g, '-')}.pdf`,
        size: '1.5 MB',
        date: 'Hari ini',
        type: 'pdf',
      };
      setFiles([newFile, ...files]);
      setIsUploading(false);
      showToast('File berhasil diunggah ke workspace MoreAI!', 'success');
    }, 800);
  };

  const getFileIcon = (type: ArtifactFile['type']) => {
    switch (type) {
      case 'pdf':
        return <FileText className="w-5 h-5 text-red-600" />;
      case 'docx':
        return <FileText className="w-5 h-5 text-blue-600" />;
      case 'image':
        return <ImageIcon className="w-5 h-5 text-amber-600" />;
      case 'xlsx':
        return <FileSpreadsheet className="w-5 h-5 text-emerald-600" />;
      case 'pptx':
        return <FileText className="w-5 h-5 text-orange-600" />;
      default:
        return <FileCode className="w-5 h-5 text-slate-600" />;
    }
  };

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Title & Upload Action */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">File Saya & Library</h1>
          <p className="text-xs text-slate-500">Penyimpanan dokumen, artefak AI, dan hasil riset</p>
        </div>
        <button
          onClick={handleSimulateUpload}
          disabled={isUploading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white text-xs font-semibold shadow-xs active:scale-95 transition"
        >
          <Upload className="w-3.5 h-3.5" />
          <span>{isUploading ? 'Mengunggah...' : 'Unggah File'}</span>
        </button>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Cari file dokumen, gambar, atau data..."
          className="w-full text-xs sm:text-sm pl-10 pr-4 py-2.5 rounded-2xl bg-white border border-slate-200 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500 transition shadow-2xs"
        />
      </div>

      {/* Folders Summary Cards */}
      <div className="grid grid-cols-3 gap-2">
        <div
          onClick={() => setFilterType('docx')}
          className="cursor-pointer p-3 rounded-2xl bg-white border border-slate-100 hover:border-blue-200 shadow-2xs transition group"
        >
          <Folder className="w-6 h-6 text-blue-500 mb-1 group-hover:scale-105 transition-transform" />
          <h3 className="text-xs font-bold text-slate-900">Dokumen</h3>
          <span className="text-[10px] text-slate-500">12 Item</span>
        </div>

        <div
          onClick={() => setFilterType('image')}
          className="cursor-pointer p-3 rounded-2xl bg-white border border-slate-100 hover:border-amber-200 shadow-2xs transition group"
        >
          <Folder className="w-6 h-6 text-amber-500 mb-1 group-hover:scale-105 transition-transform" />
          <h3 className="text-xs font-bold text-slate-900">Gambar</h3>
          <span className="text-[10px] text-slate-500">24 Item</span>
        </div>

        <div
          onClick={() => setFilterType('pptx')}
          className="cursor-pointer p-3 rounded-2xl bg-white border border-slate-100 hover:border-orange-200 shadow-2xs transition group"
        >
          <Folder className="w-6 h-6 text-orange-500 mb-1 group-hover:scale-105 transition-transform" />
          <h3 className="text-xs font-bold text-slate-900">Presentasi</h3>
          <span className="text-[10px] text-slate-500">8 Item</span>
        </div>
      </div>

      {/* Category Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-1">
        {(
          [
            { id: 'semua', label: 'Semua' },
            { id: 'pdf', label: 'PDF' },
            { id: 'docx', label: 'Dokumen' },
            { id: 'image', label: 'Gambar' },
            { id: 'xlsx', label: 'Spreadsheet' },
            { id: 'pptx', label: 'Presentasi' },
          ] as const
        ).map((tab) => (
          <button
            key={tab.id}
            onClick={() => setFilterType(tab.id)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition ${
              filterType === tab.id
                ? 'bg-red-600 text-white shadow-2xs'
                : 'bg-white text-slate-600 hover:text-slate-900 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Files List */}
      <div className="space-y-2">
        {filteredFiles.length === 0 ? (
          <div className="p-8 text-center bg-white rounded-3xl border border-slate-100 text-slate-500">
            <FileText className="w-10 h-10 mx-auto text-slate-300 mb-2" />
            <p className="text-xs font-medium">Tidak ada file yang cocok dengan pencarian.</p>
          </div>
        ) : (
          filteredFiles.map((file) => (
            <div
              key={file.id}
              onClick={() => setSelectedFile(file)}
              className="cursor-pointer p-3 rounded-2xl bg-white border border-slate-100 hover:border-red-200 shadow-2xs hover:shadow-xs transition flex items-center justify-between group"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-10 h-10 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
                  {getFileIcon(file.type)}
                </div>
                <div className="min-w-0">
                  <h3 className="text-xs font-bold text-slate-900 truncate group-hover:text-red-600 transition">
                    {file.name}
                  </h3>
                  <div className="flex items-center gap-2 text-[10px] text-slate-500 mt-0.5">
                    <span>{file.size}</span>
                    <span>·</span>
                    <span>{file.date}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-1">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    showToast(`Mengunduh file: ${file.name}`, 'info');
                  }}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition"
                  title="Unduh File"
                >
                  <Download className="w-4 h-4" />
                </button>
                <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-slate-600 transition" />
              </div>
            </div>
          ))
        )}
      </div>

      {/* File Preview Modal */}
      {selectedFile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-fadeIn">
          <div className="w-full max-w-sm rounded-3xl bg-white p-5 shadow-2xl border border-slate-100 text-slate-800">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2 min-w-0">
                {getFileIcon(selectedFile.type)}
                <h3 className="text-sm font-bold text-slate-900 truncate">
                  {selectedFile.name}
                </h3>
              </div>
              <button
                onClick={() => setSelectedFile(null)}
                className="p-1 rounded-lg hover:bg-slate-100 text-slate-400"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="my-4 p-4 rounded-2xl bg-slate-50 border border-slate-100 text-xs text-slate-600 space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-400">Ukuran:</span>
                <span className="font-semibold text-slate-700">{selectedFile.size}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Tanggal Diperbarui:</span>
                <span className="font-semibold text-slate-700">{selectedFile.date}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Penyimpanan:</span>
                <span className="font-semibold text-emerald-600">Cloud Storage IndiHome</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Status Integritas:</span>
                <span className="font-semibold text-slate-700">Terenkripsi SHA-256</span>
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => {
                  showToast(`Mengunduh ${selectedFile.name}...`, 'success');
                  setSelectedFile(null);
                }}
                className="flex-1 py-2.5 rounded-xl bg-red-600 text-white text-xs font-bold hover:bg-red-700 transition flex items-center justify-center gap-1.5 shadow-xs"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Unduh File</span>
              </button>
              <button
                onClick={() => {
                  showToast('Tautan berbagi telah disalin ke clipboard.', 'success');
                  setSelectedFile(null);
                }}
                className="px-4 py-2.5 rounded-xl bg-slate-100 text-slate-700 text-xs font-semibold hover:bg-slate-200 transition flex items-center gap-1.5"
              >
                <Share2 className="w-3.5 h-3.5" />
                <span>Bagikan</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
