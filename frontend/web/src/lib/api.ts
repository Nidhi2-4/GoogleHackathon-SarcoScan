/**
 * Calls to the SarcoScan backend. Next.js forwards /api to FastAPI (see next.config.ts),
 * so the browser only ever talks to its own origin.
 */

// ponytail: the login token sits in localStorage so a page reload keeps you signed in. Fine while the
// database holds made-up patients; move it to an HttpOnly cookie before real patient data.
const TOKEN_KEY = "sarcoscan_token";

const token = () => (typeof window === "undefined" ? null : localStorage.getItem(TOKEN_KEY));

export const hasToken = () => token() !== null;

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

async function request(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  const saved = token();
  if (saved) headers.set("Authorization", `Bearer ${saved}`);
  const response = await fetch(`/api/v1${path}`, { ...init, headers });
  if (response.status === 401 && saved) {
    // The token ran out (7 days) or the account was switched off: back to the sign-in page.
    logout();
    window.location.assign("/login");
  }
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
  patch: <T>(path: string, body: unknown) =>
    request(path, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then((r) => r.json() as Promise<T>),
  upload: <T>(path: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request(path, { method: "POST", body: form }).then((r) => r.json() as Promise<T>);
  },
  /** X-rays need the login token, so they are fetched here instead of through an <img src>. */
  blob: (path: string) => request(path).then((r) => r.blob()),
};

async function authenticate(path: string, body: object): Promise<void> {
  const response = await fetch(`/api/v1/auth/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw await errorFrom(response);
  localStorage.setItem(TOKEN_KEY, (await response.json()).access_token);
}

export const login = (email: string, password: string) => authenticate("login", { email, password });

export const signup = (name: string, email: string, password: string) =>
  authenticate("signup", { name, email, password });

export function logout(): void {
  localStorage.removeItem(TOKEN_KEY);
}
