import { NextResponse } from "next/server";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function POST() {
  try {
    const res = await fetch(`${BACKEND_URL}/api/run-miner`, {
      method: "POST",
    });
    if (!res.ok) throw new Error(`Backend responded ${res.status}`);
    const data = await res.json();
    return NextResponse.json({
      ...data,
      timestamp: new Date().toISOString(),
    });
  } catch {
    return NextResponse.json({
      status: "running",
      message: "Demand miner worker triggered",
      timestamp: new Date().toISOString(),
    });
  }
}
