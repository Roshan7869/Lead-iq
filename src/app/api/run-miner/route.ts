import { NextResponse } from "next/server";

export async function POST() {
  return NextResponse.json({
    status: "running",
    message: "Demand miner worker triggered",
    timestamp: new Date().toISOString(),
  });
}
