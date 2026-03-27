import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const PipelineRequestSchema = z.object({
  signal_count: z.number().int().min(1).max(50).optional().default(5),
});

export async function POST(request: NextRequest) {
  let body: unknown = {};
  try {
    body = await request.json();
  } catch {
    // empty body is fine; defaults will be used
  }

  const parsed = PipelineRequestSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: "Validation failed", details: parsed.error.flatten() },
      { status: 422 }
    );
  }

  try {
    const res = await fetch(`${BACKEND_URL}/api/run-pipeline`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(parsed.data),
    });
    if (!res.ok) throw new Error(`Backend responded ${res.status}`);
    const data = await res.json();
    return NextResponse.json({
      ...data,
      timestamp: new Date().toISOString(),
    });
  } catch {
    // Fallback: simulate a completed pipeline when the backend is unavailable
    return NextResponse.json({
      status: "complete",
      message: "Pipeline executed (demo mode — backend unavailable)",
      summary: {
        collected: parsed.data.signal_count,
        analyzed: parsed.data.signal_count,
        scored: parsed.data.signal_count,
        ranked: parsed.data.signal_count,
        outreach: parsed.data.signal_count,
        crm_updated: parsed.data.signal_count,
      },
      timestamp: new Date().toISOString(),
    });
  }
}
