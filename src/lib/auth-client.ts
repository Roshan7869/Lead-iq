/**
 * lib/auth-client.ts — Client-side JWT token management.
 *
 * Tokens are stored in localStorage. A lightweight "leadiq_session" cookie
 * (non-httpOnly) is also set so the Next.js middleware can gate page access
 * without having to read localStorage (which is unavailable server-side).
 *
 * Never store sensitive user data here — only the JWT strings.
 */

const ACCESS_KEY  = 'leadiq:access_token';
const REFRESH_KEY = 'leadiq:refresh_token';
const SESSION_COOKIE = 'leadiq_session';

// ── Cookie helper (middleware-readable) ───────────────────────────────────────

function setCookie(name: string, value: string, days: number): void {
  if (typeof document === 'undefined') return;
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${value}; expires=${expires}; path=/; SameSite=Lax`;
}

function deleteCookie(name: string): void {
  if (typeof document === 'undefined') return;
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; SameSite=Lax`;
}

// ── Token storage ─────────────────────────────────────────────────────────────

export function setTokens(accessToken: string, refreshToken: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(ACCESS_KEY, accessToken);
  localStorage.setItem(REFRESH_KEY, refreshToken);
  setCookie(SESSION_COOKIE, '1', 30);   // session flag for middleware
}

export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(REFRESH_KEY);
}

export function clearTokens(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  deleteCookie(SESSION_COOKIE);
}

export function isAuthenticated(): boolean {
  const token = getAccessToken();
  if (!token) return false;
  try {
    // Decode without verifying (verification happens on backend)
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp * 1000 > Date.now();
  } catch {
    return false;
  }
}

// ── Auth header helper ─────────────────────────────────────────────────────────

export function getAuthHeader(): Record<string, string> {
  const token = getAccessToken();
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

// ── API call helpers ──────────────────────────────────────────────────────────

const BACKEND = process.env.NEXT_PUBLIC_API_URL ?? '';

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export async function loginRequest(
  username: string,
  password: string,
): Promise<AuthTokens> {
  const resp = await fetch(`${BACKEND}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: 'Login failed' }));
    throw new Error(err.detail ?? 'Login failed');
  }

  const data: AuthTokens = await resp.json();
  setTokens(data.access_token, data.refresh_token);
  return data;
}

export async function refreshRequest(): Promise<AuthTokens | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;

  const resp = await fetch(`${BACKEND}/api/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refresh }),
  });

  if (!resp.ok) {
    clearTokens();
    return null;
  }

  const data: AuthTokens = await resp.json();
  setTokens(data.access_token, data.refresh_token);
  return data;
}

export async function logoutRequest(): Promise<void> {
  const token = getAccessToken();
  if (token) {
    await fetch(`${BACKEND}/api/auth/logout`, {
      method: 'POST',
      headers: { ...getAuthHeader() },
    }).catch(() => {});
  }
  clearTokens();
}
