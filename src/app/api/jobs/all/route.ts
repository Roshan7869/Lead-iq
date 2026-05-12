import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.NEXT_PUBLIC_API_URL ?? "";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const source = searchParams.get("source") || "indeed";
  const skills = searchParams.get("skills") || "";
  const location = searchParams.get("location") || "";
  const band = searchParams.get("band") || "";
  const page = searchParams.get("page") || "1";
  const pageSize = searchParams.get("page_size") || "50";

  const auth = req.headers.get("authorization");

  if (BACKEND) {
    try {
      const params = new URLSearchParams({ page, page_size: pageSize });
      if (skills) params.set("skills", skills);
      if (location) params.set("location", location);
      if (band) params.set("band", band);

      const res = await fetch(`${BACKEND}/api/jobs/${source}?${params}`, {
        cache: "no-store",
        headers: auth ? { Authorization: auth } : undefined,
      });
      if (res.ok) {
        const data = await res.json();
        return NextResponse.json(data);
      }
    } catch {
      // Backend unavailable — return fallback
    }
  }

  return NextResponse.json({ total: 0, page: 1, page_size: 50, leads: [], isFallback: true });
}
