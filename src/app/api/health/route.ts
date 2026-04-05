import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    status: "ok",
    service: "LeadIQ API",
    timestamp: new Date().toISOString(),
  });
}
