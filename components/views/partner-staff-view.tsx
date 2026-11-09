'use client';

import React, { useState } from 'react';
import { ArrowLeft, Users, UserPlus, Shield, CheckCircle2, Trash2 } from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { useToast } from '@/components/ui/toast-context';

interface PartnerStaffViewProps {
  onBack: () => void;
  onNavigateTab: (tab: NavigationTab) => void;
}

export const PartnerStaffView: React.FC<PartnerStaffViewProps> = ({
  onBack,
  onNavigateTab,
}) => {
  const { showToast } = useToast();
  const [showAddModal, setShowAddModal] = useState(false);
  const [newStaffName, setNewStaffName] = useState('');
  const [newStaffRole, setNewStaffRole] = useState('Kasir / Front Desk');

  const [staffList, setStaffList] = useState([
    {
      id: 'staff-1',
      name: 'Farhan Fadliansyah',
      role: 'Owner / Manajer Utama',
      email: 'farhan@coffeehouse.id',
      phone: '+62 811-2345-6789',
      status: 'Aktif',
      canPrintQR: true,
      canResetSession: true,
      canViewAnalytics: true,
    },
    {
      id: 'staff-2',
      name: 'Rian Anggoro',
      role: 'Supervisor Shift Pagi',
      email: 'rian@coffeehouse.id',
      phone: '+62 812-9876-5432',
      status: 'Aktif',
      canPrintQR: true,
      canResetSession: true,
      canViewAnalytics: false,
    },
    {
      id: 'staff-3',
      name: 'Siti Rahmawati',
      role: 'Kasir & Layanan Tamu',
      email: 'siti@coffeehouse.id',
      phone: '+62 813-5555-1234',
      status: 'Aktif',
      canPrintQR: true,
      canResetSession: false,
      canViewAnalytics: false,
    },
  ]);

  const handleAddStaff = () => {
    if (!newStaffName.trim()) {
      showToast('Masukkan nama staf baru.', 'error');
      return;
    }
    const newStaff = {
      id: `staff-${Date.now()}`,
      name: newStaffName,
      role: newStaffRole,
      email: `${newStaffName.toLowerCase().replace(/\s+/g, '')}@coffeehouse.id`,
      phone: '+62 812-0000-1111',
      status: 'Aktif',
      canPrintQR: true,
      canResetSession: true,
      canViewAnalytics: false,
    };
    setStaffList([...staffList, newStaff]);
    setNewStaffName('');
    setShowAddModal(false);
    showToast(`Staf baru "${newStaffName}" berhasil ditambahkan!`, 'success');
  };

  const handleRemove = (name: string, id: string) => {
    setStaffList((prev) => prev.filter((s) => s.id !== id));
    showToast(`Akses staf ${name} dinonaktifkan.`, 'info');
  };

  return (
    <div className="space-y-4 pb-20 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <button onClick={onBack} className="p-1 rounded-lg text-slate-400 hover:text-slate-700">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="text-center">
          <span className="text-[10px] font-bold text-red-600 uppercase tracking-wider block">
            Sheet 4 Screen 6
          </span>
          <h1 className="text-sm sm:text-base font-bold text-slate-900 leading-tight">
            Manajemen Staf &amp; Operator
          </h1>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="text-xs font-bold text-red-600 flex items-center gap-1 hover:text-red-700"
        >
          <UserPlus className="w-4 h-4" />
          <span className="hidden sm:inline">Tambah Staf</span>
        </button>
      </div>

      {/* Staff List */}
      <div className="space-y-3">
        {staffList.map((staf) => (
          <div
            key={staf.id}
            className="p-4 rounded-3xl bg-white border border-slate-100 shadow-xs flex items-center justify-between text-xs"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-slate-800 to-slate-700 text-white flex items-center justify-center font-bold text-sm shadow-2xs">
                {staf.name.slice(0, 2).toUpperCase()}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-bold text-slate-900">{staf.name}</h3>
                  <span className="text-[9px] font-bold bg-emerald-50 text-emerald-600 px-2 py-0.5 rounded-full border border-emerald-200">
                    {staf.status}
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 mt-0.5">{staf.role}</p>
                <p className="text-[10px] text-slate-400 mt-0.5 font-mono">{staf.email}</p>
              </div>
            </div>

            {staf.id !== 'staff-1' && (
              <button
                onClick={() => handleRemove(staf.name, staf.id)}
                className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition"
                title="Hapus Staf"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        ))}
      </div>

      {/* Add Staff Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-fadeIn">
          <div className="w-full max-w-sm rounded-3xl bg-white p-5 shadow-2xl border border-slate-100 space-y-3">
            <h3 className="text-sm font-bold text-slate-900">Tambah Operator / Staf Baru</h3>
            <div className="space-y-2 text-xs">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Nama Lengkap Staf</label>
                <input
                  type="text"
                  value={newStaffName}
                  onChange={(e) => setNewStaffName(e.target.value)}
                  placeholder="Contoh: Maya Putri"
                  className="w-full p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 focus:bg-white focus:outline-none"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Peran / Jabatan</label>
                <select
                  value={newStaffRole}
                  onChange={(e) => setNewStaffRole(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 focus:bg-white focus:outline-none"
                >
                  <option value="Kasir / Front Desk">Kasir / Front Desk</option>
                  <option value="Supervisor Shift">Supervisor Shift</option>
                  <option value="Teknisi IT Venue">Teknisi IT Venue</option>
                </select>
              </div>
            </div>

            <div className="flex gap-2 pt-2">
              <button
                onClick={() => setShowAddModal(false)}
                className="flex-1 py-2 rounded-xl bg-slate-100 text-slate-600 font-semibold text-xs hover:bg-slate-200 transition"
              >
                Batal
              </button>
              <button
                onClick={handleAddStaff}
                className="flex-1 py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-xs transition shadow-xs"
              >
                Simpan Staf
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
