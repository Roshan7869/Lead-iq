"use client";

import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { Text } from "@/components/ui/text";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { UrlTrustBadge } from "@/components/UrlTrustBadge";
import { ExternalLink, Building2, Calendar, IndianRupee, Search, Shield, RefreshCw } from "lucide-react";

interface Scheme {
  name: string;
  description: string;
  eligibility: string;
  deadline: string | null;
  funding_amount: string | null;
  source_url: string;
  department: string;
  trust_score: number;
}

interface SchemesResponse {
  schemes: Scheme[];
  total: number;
  last_updated: string;
}

export default function SchemesPage() {
  const [data, setData] = useState<SchemesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const [deptFilter, setDeptFilter] = useState<string>("all");

  async function fetchSchemes() {
    try {
      const res = await fetch("/api/schemes");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchSchemes();
  }, []);

  async function handleRefresh() {
    setRefreshing(true);
    setError(null);
    try {
      await fetch("/api/crawler/run?type=schemes", { method: "POST" });
      await fetchSchemes();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setRefreshing(false);
    }
  }

  const departments = data
    ? ["all", ...Array.from(new Set(data.schemes.map((s) => s.department)))]
    : ["all"];

  const filtered = data?.schemes.filter((s) => {
    const matchesDept = deptFilter === "all" || s.department === deptFilter;
    const matchesSearch =
      !filter ||
      s.name.toLowerCase().includes(filter.toLowerCase()) ||
      s.description.toLowerCase().includes(filter.toLowerCase()) ||
      s.eligibility.toLowerCase().includes(filter.toLowerCase());
    return matchesDept && matchesSearch;
  });

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="animate-slide-up">
          <div className="flex items-center gap-3">
            <Shield className="h-8 w-8 text-emerald-500" />
            <Text variant="h1" className="text-gradient">
              Government Schemes
            </Text>
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="ml-auto inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary/10 text-primary text-sm font-medium hover:bg-primary/20 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
              {refreshing ? "Refreshing..." : "Refresh"}
            </button>
          </div>
          <Text variant="body" color="muted" className="mt-2">
            Verified startup & MSME schemes from government portals
          </Text>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-3 animate-slide-up" style={{ animationDelay: "100ms" }}>
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search schemes..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-background border border-input text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <select
            value={deptFilter}
            onChange={(e) => setDeptFilter(e.target.value)}
            className="px-4 py-2.5 rounded-lg bg-background border border-input text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            {departments.map((d) => (
              <option key={d} value={d}>
                {d === "all" ? "All Departments" : d}
              </option>
            ))}
          </select>
        </div>

        {/* Stats */}
        {!loading && data && (
          <div className="flex items-center gap-3 animate-slide-up" style={{ animationDelay: "150ms" }}>
            <Badge variant="secondary">{filtered?.length ?? 0} schemes</Badge>
            <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
              <Shield className="h-3 w-3 mr-1" />
              All sources verified (gov.in)
            </Badge>
            {data.last_updated && (
              <Text variant="caption" color="muted">
                Updated {new Date(data.last_updated).toLocaleDateString()}
              </Text>
            )}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="grid md:grid-cols-2 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="glass-panel p-5 space-y-3">
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-2/3" />
                <div className="flex gap-2 pt-2">
                  <Skeleton className="h-8 w-24" />
                  <Skeleton className="h-8 w-24" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="glass-panel p-8 text-center text-destructive">
            <Text variant="h4">Failed to load schemes</Text>
            <Text variant="body" color="muted">{error}</Text>
          </div>
        )}

        {/* Schemes Grid */}
        {!loading && !error && filtered && (
          <div className="grid md:grid-cols-2 gap-4">
            {filtered.map((scheme, index) => (
              <div
                key={scheme.name + scheme.department}
                className="glass-panel glass-panel-hover p-5 space-y-4 animate-slide-up"
                style={{ animationDelay: `${200 + index * 50}ms` }}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <Text variant="h4" className="truncate">
                      {scheme.name}
                    </Text>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant="outline" className="text-xs">
                        <Building2 className="h-3 w-3 mr-1" />
                        {scheme.department}
                      </Badge>
                      <UrlTrustBadge score={scheme.trust_score} compact />
                    </div>
                  </div>
                </div>

                <Text variant="body" color="muted" className="line-clamp-3">
                  {scheme.description}
                </Text>

                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-muted-foreground">Eligibility:</span>
                    <span className="text-foreground">{scheme.eligibility}</span>
                  </div>
                  {scheme.deadline && (
                    <div className="flex items-center gap-2 text-sm">
                      <Calendar className="h-4 w-4 text-muted-foreground" />
                      <span className="text-foreground">Deadline: {scheme.deadline}</span>
                    </div>
                  )}
                  {scheme.funding_amount && (
                    <div className="flex items-center gap-2 text-sm">
                      <IndianRupee className="h-4 w-4 text-emerald-500" />
                      <span className="text-emerald-400 font-medium">{scheme.funding_amount}</span>
                    </div>
                  )}
                </div>

                <a
                  href={scheme.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary/10 text-primary text-sm font-medium hover:bg-primary/20 transition-colors"
                >
                  <ExternalLink className="h-4 w-4" />
                  View Official Page
                </a>
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && filtered?.length === 0 && (
          <div className="glass-panel p-12 text-center animate-slide-up">
            <Shield className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <Text variant="h4" color="muted">
              No schemes match your filters
            </Text>
            <Text variant="body" color="muted">
              Try adjusting your search or department filter
            </Text>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
