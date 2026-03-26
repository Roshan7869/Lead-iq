import { NextResponse } from "next/server";

export async function POST() {
  return NextResponse.json({
    status: "running",
    message: "AI analyzer worker triggered",
    timestamp: new Date().toISOString(),
  });
}
