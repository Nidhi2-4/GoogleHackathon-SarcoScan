/**
 * Calls to the SarcoScan backend. Next.js forwards /api to FastAPI (see next.config.ts),
 * so the browser only ever talks to its own origin.
 */

// The access token lives only in this variable. It is never written to browser storage,
// so a script injected into the page cannot read it from there.
let accessToken: string | null = null;
let refreshing: Promise<boolean> | null = null;

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function errorFrom(response: Response): Promise<ApiError> {
  let message = `Request failed (${response.status})`;
  try {
    const body = await response.json();
    if (typeof body.detail === "string") message = body.detail;
    else if (Array.isArray(body.detail)) message = body.detail.map((d: { msg: string }) => d.msg).join(". ");
  } catch {
    // not JSON: keep the generic message
  }
  return new ApiError(response.status, message);
}

/**
 * Get a new access token with the refresh cookie. Calls made at the same time share one request:
 * the backend rotates the cookie on every refresh and treats a second use of the old one as theft.
 */
export function refresh(): Promise<boolean> {
  refreshing ??= fetch("/api/v1/auth/refresh", { method: "POST" })
    .then(async (response) => {
      accessToken = response.ok ? (await response.json()).access_token : null;
      return response.ok;
    })
    .catch(() => false)
    .finally(() => {
      refreshing = null;
    });
  return refreshing;
}

function send(path: string, init: RequestInit): Promise<Response> {
  const headers = new Headers(init.headers);
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  return fetch(`/api/v1${path}`, { ...init, headers });
}

async function request(path: string, init: RequestInit = {}): Promise<Response> {
  let response = await send(path, init);
  // The access token lasts 15 minutes. On 401, refresh once and repeat the call.
  if (response.status === 401 && (await refresh())) response = await send(path, init);
  if (!response.ok) throw await errorFrom(response);
  return response;
}

export const api = {
  get: <T>(path: string) => request(path).then((r) => r.json() as Promise<T>),
  post: <T>(path: string, body?: unknown) =>
    request(path, {
      method: "POST",
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    }).then((r) => r.json() as Promise<T>),
  upload: <T>(path: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request(path, { method: "POST", body: form }).then((r) => r.json() as Promise<T>);
  },
  /** X-rays need the login token, so they are fetched here instead of through an <img src>. */
  blob: (path: string) => request(path).then((r) => r.blob()),
};

export async function login(email: string, password: string): Promise<void> {
  const response = await fetch("/api/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) throw await errorFrom(response);
  accessToken = (await response.json()).access_token;
}

export async function logout(): Promise<void> {
  accessToken = null;
  await fetch("/api/v1/auth/logout", { method: "POST" }).catch(() => undefined);
}
