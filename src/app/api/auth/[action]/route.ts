/**
 * /api/auth — Proxy endpoints to backend /api/auth/*
 *
 * The frontend calls NEXT.js /api/auth/... which proxies to FastAPI.
 * This avoids CORS issues when NEXT_PUBLIC_API_URL is not set.
 */
import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.NEXT_PUBLIC_API_URL ?? "";

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ action: string }> },
) {
  const { action } = await params;

  if (!BACKEND) {
    return NextResponse.json({ detail: "Backend not configured" }, { status: 503 });
  }

  const body = await req.json().catch(() => null);

  const upstream = await fetch(`${BACKEND}/api/auth/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });

  const data = await upstream.json().catch(() => ({ detail: "Parse error" }));
  return NextResponse.json(data, { status: upstream.status });
}

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ action: string }> },
) {
  const { action } = await params;

  if (!BACKEND) {
    return NextResponse.json({ authenticated: false }, { status: 200 });
  }

  const token = req.nextUrl.searchParams.get("token") ?? "";
  const upstream = await fetch(`${BACKEND}/api/auth/${action}?token=${token}`, {
    headers: { Authorization: req.headers.get("authorization") ?? "" },
  });

  const data = await upstream.json().catch(() => ({}));
  return NextResponse.json(data, { status: upstream.status });
}
