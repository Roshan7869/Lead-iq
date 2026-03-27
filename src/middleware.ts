import { NextRequest, NextResponse } from "next/server";

/**
 * Simple in-process rate limiter for Next.js API routes.
 *
 * Uses a sliding window counter stored in a Map (resets on server restart).
 * For multi-instance deployments, replace with an Upstash Redis rate limiter
 * (e.g. @upstash/ratelimit).
 *
 * Limits:
 *   - API routes (/api/*) — 60 requests / 60 s per IP
 *   - Run-miner / run-ai / run-pipeline — 10 requests / 60 s per IP (expensive operations)
 */

const WINDOW_MS = 60_000; // 1 minute
const DEFAULT_LIMIT = 60;
const EXPENSIVE_LIMIT = 10;

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

function checkRateLimit(key: string, limit: number): { allowed: boolean; remaining: number; resetAt: number } {
  const now = Date.now();
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

  // Only rate-limit API routes
  if (!pathname.startsWith("/api/")) {
    return NextResponse.next();
  }

  const ip = getIp(request);
  const isExpensive =
    pathname.startsWith("/api/run-miner") ||
    pathname.startsWith("/api/run-ai") ||
    pathname.startsWith("/api/run-pipeline");
  const limit = isExpensive ? EXPENSIVE_LIMIT : DEFAULT_LIMIT;
  const key = `${ip}:${isExpensive ? "expensive" : "default"}`;

  const { allowed, remaining, resetAt } = checkRateLimit(key, limit);

  const headers = {
    "X-RateLimit-Limit": String(limit),
    "X-RateLimit-Remaining": String(remaining),
    "X-RateLimit-Reset": String(Math.ceil(resetAt / 1000)),
  };

  if (!allowed) {
    return NextResponse.json(
      { error: "Too many requests. Please try again later." },
      { status: 429, headers }
    );
  }

  const response = NextResponse.next();
  Object.entries(headers).forEach(([k, v]) => response.headers.set(k, v));
  return response;
}

export const config = {
  matcher: "/api/:path*",
};
