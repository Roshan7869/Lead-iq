import { NextRequest, NextResponse } from "next/server";

/**
 * Next.js middleware — two responsibilities:
 *
 * 1. AUTH GATE: Pages (non /login, non /api/auth/*) require a "leadiq_session"
 *    cookie that gets set by auth-client.ts on successful login.  The real JWT
 *    validation happens on the FastAPI backend; the cookie is just a lightweight
 *    client-side signal so the middleware doesn't need to verify crypto.
 *
 * 2. RATE LIMITING: API routes are limited via sliding window counters stored
 *    in a Map (resets on server restart).  For multi-instance deployments,
 *    replace with @upstash/ratelimit.
 *
 * Limits:
 *   - API routes (/api/*)               — 60 req / 60 s per IP
 *   - run-miner / run-ai  (expensive)   — 10 req / 60 s per IP
 */

const WINDOW_MS       = 60_000;
const DEFAULT_LIMIT   = 60;
const EXPENSIVE_LIMIT = 10;

const SESSION_COOKIE = "leadiq_session";

// Public paths that never need auth
const PUBLIC_PATHS = ["/login", "/api/auth"];

interface RateLimitEntry {
  count: number;
  resetAt: number;
}

const store = new Map<string, RateLimitEntry>();

function getIp(request: NextRequest): string {
  return (
    request.headers.get("x-forwarded-for")?.split(",")[0].trim() ??
    request.headers.get("x-real-ip") ??
    "unknown"
  );
}

function checkRateLimit(
  key: string,
  limit: number,
): { allowed: boolean; remaining: number; resetAt: number } {
  const now   = Date.now();
  const entry = store.get(key);

  if (!entry || now > entry.resetAt) {
    store.set(key, { count: 1, resetAt: now + WINDOW_MS });
    return { allowed: true, remaining: limit - 1, resetAt: now + WINDOW_MS };
  }

  if (entry.count >= limit) {
    return { allowed: false, remaining: 0, resetAt: entry.resetAt };
  }

  entry.count += 1;
  return { allowed: true, remaining: limit - entry.count, resetAt: entry.resetAt };
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // ── Auth gate (page routes only) ──────────────────────────────────────────
  const isPublicPath = PUBLIC_PATHS.some((p) => pathname.startsWith(p));
  const isApiRoute   = pathname.startsWith("/api/");

  if (!isPublicPath && !isApiRoute) {
    // Page request — check session cookie
    const session = request.cookies.get(SESSION_COOKIE);
    if (!session?.value) {
      const loginUrl = new URL("/login", request.url);
      return NextResponse.redirect(loginUrl);
    }
  }

  // ── Rate limiting (API routes only) ──────────────────────────────────────
  if (isApiRoute) {
    const ip          = getIp(request);
    const isExpensive = pathname.startsWith("/api/run-miner") || pathname.startsWith("/api/run-ai");
    const limit       = isExpensive ? EXPENSIVE_LIMIT : DEFAULT_LIMIT;
    const key         = `${ip}:${isExpensive ? "expensive" : "default"}`;

    const { allowed, remaining, resetAt } = checkRateLimit(key, limit);

    const rlHeaders = {
      "X-RateLimit-Limit":     String(limit),
      "X-RateLimit-Remaining": String(remaining),
      "X-RateLimit-Reset":     String(Math.ceil(resetAt / 1000)),
    };

    if (!allowed) {
      return NextResponse.json(
        { error: "Too many requests. Please try again later." },
        { status: 429, headers: rlHeaders },
      );
    }

    const response = NextResponse.next();
    Object.entries(rlHeaders).forEach(([k, v]) => response.headers.set(k, v));
    return response;
  }

  return NextResponse.next();
}

export const config = {
  // Run middleware on all paths except static assets
  matcher: ["/((?!_next/static|_next/image|favicon.ico|robots.txt).*)"],
};
