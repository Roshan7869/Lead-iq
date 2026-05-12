import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.NEXT_PUBLIC_API_URL ?? "";

const FALLBACK = {
  nvidia: {
    curated: {
      "nemotron-3-super-120b": "nvidia/nemotron-3-super-120b-a12b",
      "nemotron-3-nano-omni": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
      "nemotron-nano-9b-v2": "nvidia/nvidia-nemotron-nano-9b-v2",
      "mistral-nemotron": "mistralai/mistral-nemotron",
      "llama-3.1-8b": "meta/llama-3.1-8b-instruct",
      "mixtral-8x7b": "mistralai/mixtral-8x7b-instruct-v0.1",
      "deepseek-r1": "deepseek-ai/deepseek-r1",
    },
    all: {},
  },
  openrouter: {
    "kimi-k2.6": "mistralai/mistral-7b-instruct:free",
  },
  default: { fast: "nemotron-nano-9b-v2", medium: "mistral-nemotron", reasoning: "nemotron-3-super-120b" },
  isFallback: true,
};

export async function GET(req: NextRequest) {
  const auth = req.headers.get("authorization");

  if (BACKEND) {
    try {
      const res = await fetch(`${BACKEND}/api/models`, {
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

  return NextResponse.json(FALLBACK);
}
