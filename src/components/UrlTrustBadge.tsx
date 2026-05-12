"use client";

import { useEffect, useState } from "react";

interface UrlTrustBadgeProps {
  url?: string;
  score?: number;
  compact?: boolean;
}

export function UrlTrustBadge({ url, score, compact = false }: UrlTrustBadgeProps) {
  const [trust, setTrust] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (score !== undefined) {
      setLoading(false);
      return;
    }
    if (!url) {
      setLoading(false);
      return;
    }
    fetch(`/api/validate-url?url=${encodeURIComponent(url)}`)
      .then((r) => r.json())
      .then((data) => {
        setTrust(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [url, score]);

  const finalScore = score ?? trust?.score ?? 0;

  if (loading) return <span className="text-xs text-muted-foreground">Validating...</span>;

  const getColor = () => {
    if (finalScore >= 8) return "bg-emerald-500";
    if (finalScore >= 5) return "bg-amber-500";
    return "bg-red-500";
  };

  const getLabel = () => {
    if (finalScore >= 8) return "Trusted";
    if (finalScore >= 5) return "Verify";
    return "Caution";
  };

  if (compact) {
    return (
      <span className={`px-2 py-0.5 rounded text-[10px] text-white font-medium ${getColor()}`}>
        {getLabel()}
      </span>
    );
  }

  return (
    <div className="inline-flex items-center gap-2">
      <span className={`px-2 py-0.5 rounded text-xs text-white font-medium ${getColor()}`}>
        {getLabel()} ({finalScore.toFixed(1)}/10)
      </span>
      {url && (
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-muted-foreground hover:underline truncate max-w-[200px]"
        >
          {new URL(url).hostname}
        </a>
      )}
    </div>
  );
}
