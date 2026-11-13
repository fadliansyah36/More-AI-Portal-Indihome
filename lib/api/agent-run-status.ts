/** Canonical presentation semantics for persisted OpenManus Agent Run states. */
export const TERMINAL_AGENT_RUN_STATUSES = [
  'succeeded',
  'failed',
  'cancelled',
  'timed_out',
  'expired',
] as const;

export const ACTIVE_AGENT_RUN_STATUSES = [
  'queued',
  'pending',
  'running',
  'awaiting_approval',
  'waiting_approval',
] as const;

const LABELS: Record<string, string> = {
  queued: 'Dalam antrean',
  pending: 'Menunggu worker',
  running: 'Sedang berjalan',
  awaiting_approval: 'Menunggu persetujuan',
  waiting_approval: 'Menunggu persetujuan',
  succeeded: 'Selesai',
  failed: 'Gagal',
  cancelled: 'Dibatalkan',
  timed_out: 'Waktu eksekusi habis',
  expired: 'Kedaluwarsa',
};

export function isTerminalAgentRunStatus(status: string): boolean {
  return (TERMINAL_AGENT_RUN_STATUSES as readonly string[]).includes(status);
}

export function isActiveAgentRunStatus(status: string): boolean {
  return (ACTIVE_AGENT_RUN_STATUSES as readonly string[]).includes(status);
}

export function agentRunStatusLabel(status: string): string {
  return LABELS[status] || status;
}
