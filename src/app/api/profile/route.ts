import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.NEXT_PUBLIC_API_URL ?? "";

function forwardAuth(req: NextRequest): Record<string, string> {
  const auth = req.headers.get("authorization");
  return auth ? { Authorization: auth } : {};
}

/** GET /api/profile — proxy to backend, return defaults if unavailable */
export async function GET(req: NextRequest) {
  if (BACKEND) {
    try {
      const res = await fetch(`${BACKEND}/api/profile`, {
        cache: "no-store",
        headers: forwardAuth(req),
      });
      if (res.ok) {
        const data = await res.json();
        return NextResponse.json(data);
      }
    } catch {}
  }
  // Fallback: return default profile shape
  return NextResponse.json({
    id: 0,
    mode: "b2b_sales",
    product_description: null,
    target_customer: null,
    target_industries: [],
    target_company_sizes: [],
    include_keywords: [],
    exclude_keywords: [],
    hiring_roles: [],
    skills: [],
    min_salary: 0,
    remote_only: false,
    feedback_adjustments: {},
    updated_at: new Date().toISOString(),
  });
}

/** POST /api/profile — proxy save to backend, acknowledge locally if unavailable */
export async function POST(req: NextRequest) {
  const body = await req.json();

  if (BACKEND) {
    try {
      const res = await fetch(`${BACKEND}/api/profile`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...forwardAuth(req) },
        body: JSON.stringify(body),
      });
      if (res.ok) {
        const data = await res.json();
        return NextResponse.json(data);
      }
    } catch {}
  }
  // Acknowledge locally (frontend persists to localStorage too)
  return NextResponse.json({ ...body, id: 1, updated_at: new Date().toISOString() });
}
