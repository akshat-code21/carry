/**
 * Client-side Clerk token access outside React components.
 *
 * The @clerk/nextjs SDK exposes the loaded instance on window.Clerk;
 * `session.getToken()` returns a short-lived (~60s) session JWT that is
 * refreshed automatically by the Clerk client.
 */

let clerkReadyWaiter: Promise<void> | null = null;

/**
 * Wait until Clerk finishes loading its session state (window.Clerk.loaded).
 * Without this, requests fired on first page load race the Clerk bootstrap,
 * go out without an Authorization header, and land as spurious 401s.
 */
function waitForClerkLoaded(timeoutMs = 8000): Promise<void> {
  if (typeof window === "undefined") return Promise.resolve();
  const clerk = (window as unknown as { Clerk?: { loaded?: boolean } }).Clerk;
  if (clerk?.loaded) return Promise.resolve();
  if (!clerkReadyWaiter) {
    clerkReadyWaiter = new Promise<void>((resolve) => {
      const startedAt = Date.now();
      const timer = setInterval(() => {
        const loaded = (window as unknown as { Clerk?: { loaded?: boolean } }).Clerk?.loaded;
        if (loaded || Date.now() - startedAt > timeoutMs) {
          clearInterval(timer);
          clerkReadyWaiter = null;
          resolve();
        }
      }, 50);
    });
  }
  return clerkReadyWaiter;
}

/**
 * Cached token promise — when multiple hooks (e.g. 6 dashboard queries) call
 * getAuthToken() concurrently, they share the same in-flight token acquisition
 * instead of each independently waiting and calling getToken().
 */
let _tokenPromise: Promise<string | null> | null = null;
let _tokenPromiseExpiry = 0;

export async function getAuthToken(): Promise<string | null> {
  if (typeof window === "undefined") return null;

  // Reuse a recent in-flight or freshly-resolved token promise (valid for 5s)
  const now = Date.now();
  if (_tokenPromise && now < _tokenPromiseExpiry) {
    return _tokenPromise;
  }

  _tokenPromise = _acquireToken();
  _tokenPromiseExpiry = now + 5000; // cache the promise for 5 seconds

  // Clear the cached promise once it resolves (so next call after 5s gets fresh)
  _tokenPromise.finally(() => {
    // Only clear if this is still the current cached promise
    if (Date.now() >= _tokenPromiseExpiry) {
      _tokenPromise = null;
    }
  });

  return _tokenPromise;
}

async function _acquireToken(): Promise<string | null> {
  await waitForClerkLoaded();
  const clerk = (window as unknown as {
    Clerk?: { session?: { getToken?: () => Promise<string | null> } };
  }).Clerk;
  if (!clerk?.session?.getToken) return null;
  try {
    return await clerk.session.getToken();
  } catch {
    return null;
  }
}

/** API error with machine-readable code from the backend detail payload. */
export class ApiError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}
