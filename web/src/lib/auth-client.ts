/**
 * Client-side Clerk token access outside React components.
 *
 * The @clerk/nextjs SDK exposes the loaded instance on window.Clerk;
 * `session.getToken()` returns a short-lived (~60s) session JWT that is
 * refreshed automatically by the Clerk client.
 */

type ClerkLike = {
  loaded?: boolean;
  session?: { getToken?: () => Promise<string | null> };
};

let clerkReadyWaiter: Promise<void> | null = null;

function _getClerk(): ClerkLike | undefined {
  if (typeof window === "undefined") return undefined;
  return (window as unknown as { Clerk?: ClerkLike }).Clerk;
}

/**
 * Wait until Clerk finishes loading AND has an active session.
 *
 * After a sign-in redirect `window.Clerk.loaded` becomes `true` before
 * `window.Clerk.session` is hydrated. If we only gated on `loaded`, the
 * first batch of API requests would go out without a token and land as
 * spurious 401s. Waiting for `session` (with a reasonable timeout) avoids
 * the race entirely.
 */
function waitForClerkReady(timeoutMs = 8000): Promise<void> {
  if (typeof window === "undefined") return Promise.resolve();
  const clerk = _getClerk();
  if (clerk?.loaded && clerk.session) return Promise.resolve();
  if (!clerkReadyWaiter) {
    clerkReadyWaiter = new Promise<void>((resolve) => {
      const startedAt = Date.now();
      const timer = setInterval(() => {
        const c = _getClerk();
        if ((c?.loaded && c.session) || Date.now() - startedAt > timeoutMs) {
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
 * Cached token promise - when multiple hooks (e.g. 6 dashboard queries) call
 * getAuthToken() concurrently, they share the same in-flight token acquisition
 * instead of each independently waiting and calling getToken().
 *
 * A `null` result is never cached so that a transient miss (Clerk session not
 * yet hydrated after redirect) doesn't poison all concurrent callers for 5 s.
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

  // If the token resolved to null (no session yet), bust the cache immediately
  // so the next caller retries instead of sharing the stale null for 5 s.
  _tokenPromise.then((token) => {
    if (token === null) {
      _tokenPromise = null;
      _tokenPromiseExpiry = 0;
    }
  });

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
  await waitForClerkReady();
  const clerk = _getClerk();
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
