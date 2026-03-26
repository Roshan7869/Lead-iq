import { NextResponse } from "next/server";
import { demoLeads } from "@/data/demo-leads";

export async function GET() {
  return NextResponse.json({ leads: demoLeads });
}
