'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { CalendarDays, Mail, RefreshCw, ShieldCheck, Unplug, Link2, AlertCircle } from 'lucide-react';
import { connectionsApi, type CustomerConnection } from '@/lib/api/client';

const permissions = [
  { key: 'gmail.read', label: 'Baca Gmail', detail: 'Daftar email dan metadata pesan' },
  { key: 'gmail.send', label: 'Kirim Gmail', detail: 'Akses kirim email; memerlukan konfirmasi aksi' },
  { key: 'calendar.read', label: 'Baca Calendar', detail: 'Lihat jadwal dan agenda' },
  { key: 'calendar.write', label: 'Kelola Calendar', detail: 'Membuat dan mengubah agenda; memerlukan konfirmasi aksi' },
] as const;

type MailItem = { id: string; subject?: string; from?: string; date?: string; snippet?: string; unread?: boolean };
type CalendarItem = { id: string; summary?: string; start?: { dateTime?: string; date?: string }; end?: { dateTime?: string; date?: string }; html_link?: string };

export function ConnectionsCenterView() {
  const [items, setItems] = useState<CustomerConnection[]>([]);
  const [selected, setSelected] = useState<string[]>(['gmail.read', 'calendar.read']);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mail, setMail] = useState<Record<string, MailItem[]>>({});
  const [events, setEvents] = useState<Record<string, CalendarItem[]>>({});
  const [mailTo, setMailTo] = useState('');
  const [mailSubject, setMailSubject] = useState('');
  const [mailBody, setMailBody] = useState('');
  const [eventSummary, setEventSummary] = useState('');
  const [eventStart, setEventStart] = useState('');
  const [eventEnd, setEventEnd] = useState('');

  const refresh = useCallback(async () => {
    setLoading(true); setError(null);
    try { setItems(await connectionsApi.list()); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Connections Center tidak dapat dimuat.'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);

  const connect = async () => {
    if (!selected.length) return;
    setBusy('connect'); setError(null);
    try {
      const result = await connectionsApi.authorize(selected);
      window.location.assign(result.authorization_url);
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Google OAuth tidak dapat dimulai.'); setBusy(null); }
  };

  const disconnect = async (id: string) => {
    setBusy(id); setError(null);
    try { await connectionsApi.disconnect(id); await refresh(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Koneksi gagal diputus.'); }
    finally { setBusy(null); }
  };

  const loadMail = async (connection: CustomerConnection) => {
    setBusy(connection.id); setError(null);
    try { const result = await connectionsApi.gmailMessages(connection.id); setMail(current => ({ ...current, [connection.id]: result.items })); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Gmail tidak dapat dimuat.'); }
    finally { setBusy(null); }
  };

  const sendMail = async (connection: CustomerConnection) => {
    const recipients = mailTo.split(',').map(value => value.trim()).filter(Boolean);
    if (!recipients.length || !mailSubject.trim() || !mailBody.trim()) return;
    if (!window.confirm('Kirim email sekarang ke ' + recipients.join(', ') + '? Tindakan ini tidak dapat dibatalkan.')) return;
    setBusy(connection.id); setError(null);
    try { await connectionsApi.sendGmail(connection.id, recipients, mailSubject.trim(), mailBody); setMailTo(''); setMailSubject(''); setMailBody(''); window.alert('Email diterima oleh Gmail API.'); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Pengiriman email gagal atau hasilnya belum diketahui. Periksa folder Sent sebelum mencoba kembali.'); }
    finally { setBusy(null); }
  };

  const createEvent = async (connection: CustomerConnection) => {
    if (!eventSummary.trim() || !eventStart || !eventEnd) return;
    if (!window.confirm('Buat agenda Calendar "' + eventSummary + '" pada ' + eventStart + '?')) return;
    setBusy(connection.id); setError(null);
    try { await connectionsApi.createCalendarEvent(connection.id, eventSummary.trim(), new Date(eventStart).toISOString(), new Date(eventEnd).toISOString()); setEventSummary(''); setEventStart(''); setEventEnd(''); await loadCalendar(connection); window.alert('Agenda berhasil dibuat di Google Calendar.'); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Pembuatan agenda gagal atau hasilnya belum diketahui.'); }
    finally { setBusy(null); }
  };

  const loadCalendar = async (connection: CustomerConnection) => {
    setBusy(connection.id); setError(null);
    try {
      const from = new Date(); const until = new Date(Date.now() + 30 * 86400000);
      const result = await connectionsApi.calendarEvents(connection.id, from.toISOString(), until.toISOString());
      setEvents(current => ({ ...current, [connection.id]: result.items }));
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Calendar tidak dapat dimuat.'); }
    finally { setBusy(null); }
  };

  return <div className="space-y-4 pb-20 animate-fadeIn">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div><h1 className="text-xl font-bold tracking-tight text-slate-900">Connections Center</h1><p className="mt-1 text-xs text-slate-500">Hubungkan layanan eksternal ke OpenManus melalui FastAPI. Credential disimpan terenkripsi di backend dan tidak dikirim ke browser.</p></div>
      <button onClick={() => void refresh()} disabled={loading} className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700"><RefreshCw className={'h-3.5 w-3.5 ' + (loading ? 'animate-spin' : '')}/>Segarkan</button>
    </div>
    <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-2xs space-y-3">
      <div className="flex items-center gap-2"><div className="flex h-9 w-9 items-center justify-center rounded-xl bg-red-50 text-red-600"><Link2 className="h-4 w-4"/></div><div><h2 className="text-sm font-bold text-slate-900">Hubungkan Google Workspace</h2><p className="text-[10px] text-slate-500">OAuth 2.0 Authorization Code + PKCE · persetujuan scope terpisah</p></div></div>
      <div className="grid gap-2 sm:grid-cols-2">{permissions.map(item=><label key={item.key} className="flex items-start gap-2 rounded-xl border border-slate-100 bg-slate-50 p-3"><input type="checkbox" checked={selected.includes(item.key)} onChange={event=>setSelected(current=>event.target.checked?[...current,item.key]:current.filter(key=>key!==item.key))} className="mt-0.5 accent-red-600"/><span><strong className="block text-xs text-slate-800">{item.label}</strong><span className="text-[10px] text-slate-500">{item.detail}</span></span></label>)}</div>
      <button onClick={()=>void connect()} disabled={busy==='connect'||!selected.length} className="rounded-xl bg-red-600 px-4 py-2.5 text-xs font-bold text-white hover:bg-red-700 disabled:opacity-50">{busy==='connect'?'Mengalihkan ke Google…':'Hubungkan akun Google'}</button>
    </section>
    {error && <div role="alert" className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700"><AlertCircle className="h-4 w-4 shrink-0"/>{error}</div>}
    {loading ? <p className="rounded-2xl border border-slate-100 bg-white p-8 text-center text-xs text-slate-500">Memuat status koneksi…</p>
      : items.length===0 ? <div className="rounded-2xl border border-slate-100 bg-white p-8 text-center"><ShieldCheck className="mx-auto mb-2 h-7 w-7 text-slate-400"/><p className="text-sm font-semibold text-slate-800">Belum ada koneksi aktif</p><p className="mt-1 text-xs text-slate-500">Pilih permission yang diperlukan lalu hubungkan akun Google.</p></div>
      : <div className="space-y-3">{items.map(connection=><article key={connection.id} className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-2xs">
        <div className="flex flex-wrap items-start justify-between gap-2"><div><div className="flex items-center gap-2"><h3 className="text-sm font-bold text-slate-900">{connection.display_name || 'Google Account'}</h3><span className={'rounded-full px-2 py-0.5 text-[10px] font-semibold '+(connection.status==='connected'?'bg-emerald-50 text-emerald-700':'bg-amber-50 text-amber-700')}>{connection.status}</span></div><p className="mt-1 text-[10px] text-slate-500">Google · diperbarui {new Date(connection.token_updated_at).toLocaleString('id-ID')}</p></div><button onClick={()=>void disconnect(connection.id)} disabled={busy===connection.id} className="inline-flex items-center gap-1 rounded-lg border border-rose-200 px-2.5 py-1.5 text-[10px] font-semibold text-rose-700 disabled:opacity-50"><Unplug className="h-3 w-3"/>Putuskan</button></div>
        <div className="flex flex-wrap gap-1">{connection.scopes.filter(scope=>scope!=='openid'&&scope!=='email'&&scope!=='profile').map(scope=><span key={scope} className="rounded-lg border border-slate-200 bg-slate-50 px-2 py-1 text-[9px] text-slate-600">{scope.split('/').pop()}</span>)}</div>
        <div className="flex flex-wrap gap-2">
          {connection.scopes.includes('https://www.googleapis.com/auth/gmail.readonly')&&<button onClick={()=>void loadMail(connection)} disabled={busy===connection.id} className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-[10px] font-semibold text-slate-700"><Mail className="h-3 w-3"/>Muat Gmail</button>}
          {(connection.scopes.includes('https://www.googleapis.com/auth/calendar.readonly')||connection.scopes.includes('https://www.googleapis.com/auth/calendar.events'))&&<button onClick={()=>void loadCalendar(connection)} disabled={busy===connection.id} className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-[10px] font-semibold text-slate-700"><CalendarDays className="h-3 w-3"/>Muat Calendar 30 hari</button>}
        </div>
        {mail[connection.id]&&<div className="space-y-1 rounded-xl bg-slate-50 p-3"><p className="text-[10px] font-bold text-slate-700">Email terbaru</p>{mail[connection.id].length?mail[connection.id].map(item=><div key={item.id} className="border-t border-slate-200 py-2"><p className="text-xs font-semibold text-slate-800">{item.subject||'(Tanpa subjek)'}</p><p className="text-[10px] text-slate-500">{item.from} · {item.date}</p><p className="text-[10px] text-slate-600">{item.snippet}</p></div>):<p className="text-xs text-slate-500">Tidak ada email ditemukan.</p>}</div>}
        {events[connection.id]&&<div className="space-y-1 rounded-xl bg-slate-50 p-3"><p className="text-[10px] font-bold text-slate-700">Agenda 30 hari</p>{events[connection.id].length?events[connection.id].map(event=><div key={event.id} className="border-t border-slate-200 py-2"><p className="text-xs font-semibold text-slate-800">{event.summary||'(Tanpa judul)'}</p><p className="text-[10px] text-slate-500">{event.start?.dateTime||event.start?.date||'Waktu tidak tersedia'}</p></div>):<p className="text-xs text-slate-500">Tidak ada agenda.</p>}</div>}
        {connection.scopes.includes('https://www.googleapis.com/auth/gmail.send')&&<form onSubmit={event=>{event.preventDefault();void sendMail(connection);}} className="space-y-2 rounded-xl border border-slate-200 p-3">
          <p className="text-[10px] font-bold text-slate-700">Kirim Gmail · konfirmasi wajib</p>
          <input value={mailTo} onChange={event=>setMailTo(event.target.value)} placeholder="Penerima email (pisahkan koma)" className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"/>
          <input value={mailSubject} onChange={event=>setMailSubject(event.target.value)} placeholder="Subjek" className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"/>
          <textarea value={mailBody} onChange={event=>setMailBody(event.target.value)} placeholder="Isi email" rows={3} className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"/>
          <button disabled={busy===connection.id||!mailTo.trim()||!mailSubject.trim()||!mailBody.trim()} className="rounded-lg bg-red-600 px-3 py-2 text-[10px] font-bold text-white disabled:opacity-40">Tinjau & kirim email</button>
        </form>}
        {connection.scopes.includes('https://www.googleapis.com/auth/calendar.events')&&<form onSubmit={event=>{event.preventDefault();void createEvent(connection);}} className="space-y-2 rounded-xl border border-slate-200 p-3">
          <p className="text-[10px] font-bold text-slate-700">Buat agenda Calendar · konfirmasi wajib</p>
          <input value={eventSummary} onChange={event=>setEventSummary(event.target.value)} placeholder="Judul agenda" className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"/>
          <div className="grid gap-2 sm:grid-cols-2"><input type="datetime-local" value={eventStart} onChange={event=>setEventStart(event.target.value)} className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"/><input type="datetime-local" value={eventEnd} onChange={event=>setEventEnd(event.target.value)} className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"/></div>
          <button disabled={busy===connection.id||!eventSummary.trim()||!eventStart||!eventEnd} className="rounded-lg bg-red-600 px-3 py-2 text-[10px] font-bold text-white disabled:opacity-40">Tinjau & buat agenda</button>
        </form>}
      </article>)}</div>}
    <p className="text-[10px] text-slate-400">Aksi Gmail send dan Calendar write tetap memerlukan konfirmasi eksplisit dan receipt idempotent; tombol baca di sini hanya menggunakan scope read yang telah disetujui.</p>
  </div>;
}
