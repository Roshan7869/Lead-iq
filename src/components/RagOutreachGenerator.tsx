"use client";

import { useState } from "react";
import { toast } from "sonner";

interface RagOutreachGeneratorProps {
  companyId: string;
  companyName: string;
}

export function RagOutreachGenerator({ companyId, companyName }: RagOutreachGeneratorProps) {
  const [productDesc, setProductDesc] = useState("");
  const [valueProp, setValueProp] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const generate = async () => {
    if (!productDesc || !valueProp) {
      toast.error("Please fill in product description and value proposition");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch("/api/proxy/api/outreach/rag", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_id: companyId,
          company_name: companyName,
          product_description: productDesc,
          value_proposition: valueProp,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResult(data);
      toast.success(`Outreach generated (confidence: ${data.confidence})`);
    } catch (err) {
      toast.error("Failed to generate outreach");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="text-sm font-medium">Your Product/Service</label>
        <textarea
          className="w-full mt-1 p-2 border rounded-md bg-background"
          rows={2}
          placeholder="What do you sell?"
          value={productDesc}
          onChange={(e) => setProductDesc(e.target.value)}
        />
      </div>

      <div>
        <label className="text-sm font-medium">Value Proposition</label>
        <textarea
          className="w-full mt-1 p-2 border rounded-md bg-background"
          rows={2}
          placeholder="Why should they care?"
          value={valueProp}
          onChange={(e) => setValueProp(e.target.value)}
        />
      </div>

      <button
        onClick={generate}
        disabled={loading}
        className="px-4 py-2 bg-primary text-primary-foreground rounded-md font-medium hover:opacity-90 disabled:opacity-50"
      >
        {loading ? "Generating with RAG..." : "🎯 Generate RAG Outreach"}
      </button>

      {result && (
        <div className="glass-panel p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Subject:</span>
            <span className="text-xs bg-green-500 text-white px-2 py-0.5 rounded">
              {result.confidence}
            </span>
          </div>
          <p className="text-sm font-semibold">{result.subject}</p>

          <div className="text-sm font-medium">Body:</div>
          <p className="text-sm whitespace-pre-wrap">{result.body}</p>

          <div className="text-xs text-muted-foreground pt-2 border-t">
            <div>Personalization Score: {result.personalization_score}/10</div>
            <div>Sources: {result.sources_used?.length || 0}</div>
            <div>Model: {result.metadata?.model_used || "unknown"}</div>
            <div>Latency: {result.metadata?.latency_ms || 0}ms</div>
          </div>
        </div>
      )}
    </div>
  );
}
