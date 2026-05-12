import { NextRequest, NextResponse } from "next/server";
import { demoLeads } from "@/data/demo-leads";

const BACKEND = process.env.NEXT_PUBLIC_API_URL ?? "";

export async function GET(req: NextRequest) {
  // Try real backend first — fall back to demo data gracefully
  const auth = req.headers.get("authorization");
  if (BACKEND) {
    try {
      const res = await fetch(`${BACKEND}/api/leads?limit=200`, {
        cache: "no-store",
        headers: auth ? { Authorization: auth } : undefined,
      });
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data.leads)) {
          return NextResponse.json(data);
        }
      }
    } catch { /* backend unavailable — fall back to demo */}
  }
  return NextResponse.json({ leads: demoLeads, isFallback: true });
}
