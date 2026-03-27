import { NextResponse } from "next/server";
import { demoLeads } from "@/data/demo-leads";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function GET() {
  try {
    const res = await fetch(`${BACKEND_URL}/api/leads`, {
      next: { revalidate: 0 },
    });
    if (!res.ok) throw new Error(`Backend responded ${res.status}`);
    const data = await res.json();
    // Merge demo leads with CRM leads so the UI always has data
    const crmLeads: unknown[] = Array.isArray(data.leads) ? data.leads : [];
    const leads = crmLeads.length > 0 ? crmLeads : demoLeads;
    return NextResponse.json({ leads });
  } catch {
    // Graceful fallback: return demo data when backend is unavailable
    return NextResponse.json({ leads: demoLeads });
  }
}
