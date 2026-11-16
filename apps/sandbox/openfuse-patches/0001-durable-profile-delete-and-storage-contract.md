# OpenFuse durable profile lifecycle patch

Target upstream: `CopilotKit/openfuse`  
Pinned upstream commit: `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`

This patch is maintained outside `vendor/openmanusweb`; it does not modify the pristine OpenManus source snapshot. It extends the pinned OpenFuse browser worker API so MoreAI can remove a profile only after the MoreAI ownership reconciler has established that no canonical session row exists.

## 1. `apps/worker/src/browser.ts`

Add the following method to the object returned by `createBrowserManager`:

```ts
deleteProfile: (id: string) =>
  serial(id, async () => {
    validateSessionId(id);
    const instance = running.get(id);
    if (instance) {
      throw new WorkerError(
        "SESSION_ACTIVE",
        "An active browser profile cannot be deleted.",
        409,
      );
    }
    if (!sessions.has(id)) {
      // Idempotent cleanup: a profile already removed is considered absent.
      await rm(directory(id), { recursive: true, force: true });
      return { id, status: "deleted", already_absent: true };
    }
    await rm(directory(id), { recursive: true, force: true });
    sessions.delete(id);
    return { id, status: "deleted", already_absent: false };
  }),
```

## 2. `apps/worker/src/server.ts`

Extend the session route matcher to include `delete-profile` and dispatch it only for authenticated DELETE requests:

```ts
const match =
  /^\/sessions\/([^/]+)\/(navigate|close|screenshot|read|input|downloads|delete-profile)(?:\/([^/]+))?$/.exec(
    pathname,
  );
```

Add the dispatch branch before the final not-found branch:

```ts
else if (action === "delete-profile" && !downloadId && request.method === "DELETE")
  json(200, await browser.deleteProfile(id));
```

## 3. Durable storage requirement

The OpenFuse worker must mount its configured `WORKER_DATA_DIR` (default `.openfuse/browser-profiles`) to a persistent, private volume. The volume must not be shared across tenants or unrelated OpenFuse deployments. Its permissions must remain owner-only. Backups and retention must be encrypted at rest and access-controlled. An ephemeral container filesystem is not an acceptable production configuration.

The pinned upstream worker already:
- writes session metadata atomically to `session.json`;
- stores the persistent Chromium profile under `<WORKER_DATA_DIR>/<session UUID>/profile`;
- saves cookie state to `storage.json` when closing a context;
- reloads saved cookies and persistent profile data when reopening;
- restores closed session metadata on worker startup.

MoreAI must continue to use the canonical session UUID as the OpenFuse profile ID. The MoreAI API's encrypted `encrypted_state` column is not the active profile persistence mechanism; the durable OpenFuse profile volume is. Do not describe the API column as proof of browser storage persistence.

## 4. Security and deployment gate

The patch is required before the MoreAI supervisor can call `DELETE /sessions/{id}/delete-profile`. Until the pinned OpenFuse worker is rebuilt and deployed with this patch, orphan profile deletion remains unavailable and must fail closed. Never delete a profile based solely on age or a missing transient list response.
