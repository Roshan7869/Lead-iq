"use client";

import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { Text } from "@/components/ui/text";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendingUp, DollarSign, Building, MapPin, Search, AlertCircle, RefreshCw } from "lucide-react";

interface FundingEvent {
  id: string;
  company_name: string;
  amount: string | null;
  round_type: string | null;
  date: string;
  source: string;
  location: string | null;
  industry: string | null;
  trust_score: number;
  is_verified: boolean;
}

export default function FundingPage() {
  const [events, setEvents] = useState<FundingEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  async function fetchFunding() {
    try {
      const res = await fetch("/api/funding?limit=100");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setEvents(json.events ?? []);
      setLastUpdated(json.last_updated ?? null);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchFunding();
  }, []);

  async function handleRefresh() {
    setRefreshing(true);
    setError(null);
    try {
      // First trigger crawl
      await fetch("/api/crawler/run?type=funding", { method: "POST" });
      // Then re-fetch
      await fetchFunding();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setRefreshing(false);
    }
  }

  const filtered = events.filter(
    (e) =>
      !filter ||
      e.company_name.toLowerCase().includes(filter.toLowerCase()) ||
      (e.industry && e.industry.toLowerCase().includes(filter.toLowerCase())) ||
      (e.location && e.location.toLowerCase().includes(filter.toLowerCase()))
  );

  const totalAmount = filtered.reduce((sum, e) => {
    const match = e.amount?.match(/[\d.]+/);
    return sum + (match ? parseFloat(match[0]) : 0);
  }, 0);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="animate-slide-up">
          <div className="flex items-center gap-3 justify-between">
            <div className="flex items-center gap-3">
              <TrendingUp className="h-8 w-8 text-violet-500" />
              <Text variant="h1" className="text-gradient">
                Funding Signals
              </Text>
            </div>
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary/10 text-primary text-sm font-medium hover:bg-primary/20 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
              {refreshing ? "Refreshing..." : "Refresh"}
            </button>
          </div>
          <Text variant="body" color="muted" className="mt-2">
            Track verified funding rounds and investment activity
          </Text>
        </div>

        {/* Stats Cards */}
        {!loading && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-slide-up" style={{ animationDelay: "100ms" }}>
            <div className="glass-panel p-4 text-center">
              <Text variant="h2" className="text-violet-400 font-mono">{events.length}</Text>
              <Text variant="caption" color="muted">Total Events</Text>
            </div>
            <div className="glass-panel p-4 text-center">
              <Text variant="h2" className="text-emerald-400 font-mono">{events.filter((e) => e.is_verified).length}</Text>
              <Text variant="caption" color="muted">Verified</Text>
            </div>
            <div className="glass-panel p-4 text-center">
              <Text variant="h2" className="text-amber-400 font-mono">{new Set(events.map((e) => e.source)).size}</Text>
              <Text variant="caption" color="muted">Sources</Text>
            </div>
            <div className="glass-panel p-4 text-center">
              <Text variant="h2" className="text-blue-400 font-mono">{totalAmount.toFixed(1)}M+</Text>
              <Text variant="caption" color="muted">Tracked ($)</Text>
            </div>
          </div>
        )}

        {/* Search + Status */}
        <div className="flex flex-col sm:flex-row gap-3 animate-slide-up" style={{ animationDelay: "150ms" }}>
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search companies, industries, locations..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-background border border-input text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          {lastUpdated && (
            <div className="flex items-center px-3 text-xs text-muted-foreground bg-muted/30 rounded-lg">
              Updated {new Date(lastUpdated).toLocaleTimeString()}
            </div>
          )}
        </div>

        {/* Loading */}
        {loading && (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="glass-panel p-4 flex items-center gap-4">
                <Skeleton className="h-10 w-10 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-5 w-48" />
                  <Skeleton className="h-4 w-32" />
                </div>
                <Skeleton className="h-8 w-20" />
              </div>
            ))}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="glass-panel p-6 text-center text-destructive flex items-center justify-center gap-2">
            <AlertCircle className="h-5 w-5" />
            <Text variant="body">Failed to load funding data: {error}</Text>
          </div>
        )}

        {/* Events List */}
        {!loading && !error && (
          <div className="space-y-3">
            {filtered.map((event, index) => (
              <div
                key={event.id}
                className="glass-panel glass-panel-hover p-4 flex flex-col sm:flex-row sm:items-center gap-4 animate-slide-up"
                style={{ animationDelay: `${200 + index * 50}ms` }}
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <div className="h-10 w-10 rounded-full bg-violet-500/10 flex items-center justify-center shrink-0">
                    <DollarSign className="h-5 w-5 text-violet-400" />
                  </div>
                  <div className="min-w-0">
                    <Text variant="body" className="font-medium truncate">
                      {event.company_name}
                    </Text>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
                      <Building className="h-3 w-3" />
                      {event.industry || "Unknown industry"}
                      {event.location && (
                        <>
                          <span className="text-border">|</span>
                          <MapPin className="h-3 w-3" />
                          {event.location}
                        </>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 flex-wrap">
                  {event.amount && (
                    <Badge variant="secondary" className="bg-emerald-500/10 text-emerald-300 border-emerald-500/20">
                      {event.amount}
                    </Badge>
                  )}
                  {event.round_type && (
                    <Badge variant="secondary" className="bg-violet-500/10 text-violet-300 border-violet-500/20">
                      {event.round_type}
                    </Badge>
                  )}
                  <Text variant="caption" color="muted">
                    {event.date ? new Date(event.date).toLocaleDateString() : "Recent"}
                  </Text>
                  <Badge variant="outline" className={event.is_verified ? "bg-emerald-500/10 text-emerald-400" : ""}>
                    {event.is_verified ? "Verified" : "Unverified"}
                  </Badge>
                  <Badge variant="outline" className="text-xs">{event.source}</Badge>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && filtered.length === 0 && (
          <div className="glass-panel p-12 text-center animate-slide-up">
            <TrendingUp className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <Text variant="h4" color="muted">No funding events found</Text>
            <Text variant="body" color="muted">
              Try a different search or click Refresh to fetch the latest data
            </Text>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}