import { existsSync } from "node:fs";
import { createWorkerServer } from "./server.ts";

const token = process.env.WORKER_TOKEN ?? "";
const defaultDataDir = ".openfuse/browser-profiles";
const legacyDataDir = ".openmuse/browser-profiles";
const dataDir =
  process.env.WORKER_DATA_DIR ??
  (!existsSync(defaultDataDir) && existsSync(legacyDataDir) ? legacyDataDir : defaultDataDir);
const idleTimeoutMs = Number(process.env.WORKER_IDLE_TIMEOUT_MS ?? 600_000);
if (!Number.isSafeInteger(idleTimeoutMs) || idleTimeoutMs < 60_000 || idleTimeoutMs > 3_600_000) {
  throw new Error("WORKER_IDLE_TIMEOUT_MS must be between 60000 and 3600000.");
}
const worker = await createWorkerServer({
  token,
  dataDir,
  maxSessions: 3,
  idleTimeoutMs,
});
worker.server.listen(8790, process.env.WORKER_HOST ?? "127.0.0.1", () => {
  console.log("OpenFuse browser worker listening on port 8790");
});
let stopping = false;
async function stop() {
  if (stopping) return;
  stopping = true;
  const deadline = setTimeout(() => process.exit(1), 30_000);
  deadline.unref();
  await worker.close();
  process.exit(0);
}
process.on("SIGTERM", () => {
  void stop();
});
process.on("SIGINT", () => {
  void stop();
});
