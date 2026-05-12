import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.NEXT_PUBLIC_API_URL ?? "";

export async function GET(req: NextRequest) {
  const auth = req.headers.get("authorization");

  if (BACKEND) {
    try {
      const res = await fetch(`${BACKEND}/api/collectors/health`, {
        cache: "no-store",
        headers: auth ? { Authorization: auth } : undefined,
      });
      if (res.ok) {
        const data = await res.json();
        return NextResponse.json(data);
      }
    } catch {
      // Backend unavailable — return fallback
    }
  }

  return NextResponse.json({ sources: [], isFallback: true });
}
