"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Cpu, Sparkles, RefreshCw, Check, ChevronDown } from "lucide-react";

interface ModelInfo {
  id: string;
  label: string;
  provider: "nvidia" | "openrouter";
  tier: "fast" | "medium" | "reasoning";
  description: string;
}

const MODEL_REGISTRY: Record<string, ModelInfo> = {
  "nemotron-nano-9b-v2": { id: "nemotron-nano-9b-v2", label: "Nemotron Nano 9B v2", provider: "nvidia", tier: "fast", description: "High-efficiency agentic tasks" },
  "mistral-nemotron": { id: "mistral-nemotron", label: "Mistral Nemotron", provider: "nvidia", tier: "medium", description: "Mistral collaboration model" },
  "nemotron-3-super-120b": { id: "nemotron-3-super-120b", label: "Nemotron 3 Super 120B", provider: "nvidia", tier: "reasoning", description: "Complex reasoning & planning" },
  "nemotron-3-nano-omni": { id: "nemotron-3-nano-omni", label: "Nemotron 3 Nano Omni", provider: "nvidia", tier: "reasoning", description: "Omni-modal (text/images/video/speech)" },
  "llama-3.1-8b": { id: "llama-3.1-8b", label: "Llama 3.1 8B", provider: "nvidia", tier: "fast", description: "Fast extraction & classification" },
  "deepseek-r1": { id: "deepseek-r1", label: "DeepSeek R1", provider: "nvidia", tier: "reasoning", description: "Deep reasoning & coding" },
  "kimi-k2.6": { id: "kimi-k2.6", label: "Kimi K2.6", provider: "openrouter", tier: "reasoning", description: "Kimi via OpenRouter" },
};

interface ModelSelectorProps {
  value?: string;
  onChange?: (modelId: string) => void;
  showLabel?: boolean;
}

export function ModelSelector({ value, onChange, showLabel = true }: ModelSelectorProps) {
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState(value || "nemotron-nano-9b-v2");
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);

  const selectedModel = MODEL_REGISTRY[selected] || MODEL_REGISTRY["nemotron-nano-9b-v2"];

  const handleSelect = (id: string) => {
    setSelected(id);
    setOpen(false);
    onChange?.(id);
  };

  const testModel = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await fetch("/api/run-ai", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model: selected, prompt: "Respond with just: OK", max_tokens: 10 }),
      });
      const data = await res.json();
      setTestResult(data.success ? "Connected" : "Error: " + (data.error || "unknown"));
    } catch (e: any) {
      setTestResult("Error: " + e.message);
    } finally {
      setTesting(false);
    }
  };

  const providerColor = selectedModel.provider === "nvidia" ? "text-emerald-400" : "text-violet-400";
  const Icon = selectedModel.tier === "reasoning" ? Sparkles : Cpu;

  return (
    <div className="relative">
      {showLabel && (
        <label className="text-xs font-medium text-muted-foreground mb-1.5 block">AI Model</label>
      )}
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-background border border-input text-sm hover:bg-accent/50 transition-colors"
      >
        <Icon className={"h-4 w-4 " + providerColor} />
        <span className="flex-1 text-left">{selectedModel.label}</span>
        <Badge variant="outline" className="text-[10px] px-1.5 py-0">{selectedModel.tier}</Badge>
        <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute top-full left-0 right-0 mt-1 z-50 bg-popover border border-border rounded-lg shadow-xl overflow-hidden">
            <div className="p-2 space-y-0.5 max-h-64 overflow-y-auto">
              {Object.entries(MODEL_REGISTRY).map(([id, model]) => (
                <button
                  key={id}
                  onClick={() => handleSelect(id)}
                  className={"w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm hover:bg-accent transition-colors " + (selected === id ? "bg-accent" : "")}
                >
                  <Cpu className={"h-3.5 w-3.5 shrink-0 " + (model.provider === "nvidia" ? "text-emerald-400" : "text-violet-400")} />
                  <div className="flex-1 text-left">
                    <div className="font-medium">{model.label}</div>
                    <div className="text-[11px] text-muted-foreground">{model.description}</div>
                  </div>
                  {selected === id && <Check className="h-3.5 w-3.5 text-primary" />}
                </button>
              ))}
            </div>
            <div className="border-t border-border p-2 flex items-center gap-2">
              <button onClick={testModel} disabled={testing}
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium bg-primary/10 text-primary hover:bg-primary/20 transition-colors disabled:opacity-50"
              >
                <RefreshCw className={"h-3 w-3 " + (testing ? "animate-spin" : "")} />
                {testing ? "Testing..." : "Test Connection"}
              </button>
              {testResult && (
                <span className={"text-xs " + (testResult === "Connected" ? "text-emerald-400" : "text-destructive")}>
                  {testResult}
                </span>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
