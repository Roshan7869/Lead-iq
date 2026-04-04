import { NextRequest, NextResponse } from "next/server";
import { demoLeads } from "@/data/demo-leads";

const BACKEND = process.env.NEXT_PUBLIC_API_URL ?? "";

export async function GET(req: NextRequest) {
  // Try real backend first — fall back to demo data gracefully
  const auth = req.headers.get("authorization");
  const authHeader = auth ? { Authorization: auth } : {};
  if (BACKEND) {
    try {
      const res = await fetch(`${BACKEND}/api/leads?limit=200`, {
        cache: "no-store",
        headers: authHeader,
      });
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data.leads) && data.leads.length > 0) {
          return NextResponse.json(data);
        }
      }
    } catch {}
  }
  return NextResponse.json({ leads: demoLeads });
}
