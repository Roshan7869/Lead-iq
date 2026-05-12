"use client";

import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { Text } from "@/components/ui/text";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Briefcase, Building2, MapPin, Clock, TrendingUp, Search, Users, AlertCircle, RefreshCw } from "lucide-react";

interface JobSignal {
  id: string;
  company_name: string;
  title: string;
  location: string | null;
  work_mode: string | null;
  experience: string | null;
  skills: string[];
  salary_range: string | null;
  posted_date: string;
  source: string;
  hiring_velocity: number; // 0-100
  trust_score: number;
}

export default function JobSignalsPage() {
  const [signals, setSignals] = useState<JobSignal[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const [modeFilter, setModeFilter] = useState<string>("all");
  const [sourceFilter, setSourceFilter] = useState<string>("all");

  async function fetchJobs(source?: string) {
    try {
      const src = source || sourceFilter;
      const endpoint = src === "all" ? "/api/jobs/all?source=indeed&page_size=50" : `/api/jobs/all?source=${src}&page_size=50`;
      const res = await fetch(endpoint);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      const mapped: JobSignal[] = (json.leads ?? []).map((l: any) => ({
        id: l.id,
        company_name: l.company_name || "Unknown",
        title: l.contact_title || "Open Position",
        location: l.location,
        work_mode: "hybrid",
        experience: null,
        skills: [],
        salary_range: null,
        posted_date: l.created_at ? new Date(l.created_at).toLocaleDateString() : "Recent",
        source: l.source || src,
        hiring_velocity: Math.round((l.final_score || 0) * 100),
        trust_score: l.final_score || 5.0,
      }));
      setSignals(mapped);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchJobs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sourceFilter]);

  async function handleRefresh() {
    setRefreshing(true);
    setError(null);
    try {
      await fetch("/api/crawler/run?type=jobs", { method: "POST" });
      await fetchJobs();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setRefreshing(false);
    }
  }

  const workModes = signals.length > 0
    ? ["all", ...Array.from(new Set(signals.map((s) => s.work_mode).filter((m): m is string => !!m)))]
    : ["all"];

  const filtered = signals.filter((s) => {
    const matchesMode = modeFilter === "all" || s.work_mode === modeFilter;
    const matchesSearch =
      !filter ||
      s.company_name.toLowerCase().includes(filter.toLowerCase()) ||
      s.title.toLowerCase().includes(filter.toLowerCase()) ||
      (s.location && s.location.toLowerCase().includes(filter.toLowerCase())) ||
      s.skills.some((sk) => sk.toLowerCase().includes(filter.toLowerCase()));
    return matchesMode && matchesSearch;
  });

  const hotHiring = signals.filter((s) => s.hiring_velocity >= 70).length;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="animate-slide-up">
          <div className="flex items-center gap-3">
            <Briefcase className="h-8 w-8 text-blue-500" />
            <Text variant="h1" className="text-gradient">
              Job Signals
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
            Track hiring velocity and open positions from job platforms
          </Text>
        </div>

        {/* Stats */}
        {!loading && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-slide-up" style={{ animationDelay: "100ms" }}>
            <div className="glass-panel p-4 text-center">
              <Text variant="h2" className="text-blue-400 font-mono">
                {signals.length}
              </Text>
              <Text variant="caption" color="muted">Open Positions</Text>
            </div>
            <div className="glass-panel p-4 text-center">
              <Text variant="h2" className="text-amber-400 font-mono">
                {hotHiring}
              </Text>
              <Text variant="caption" color="muted">High Velocity</Text>
            </div>
            <div className="glass-panel p-4 text-center">
              <Text variant="h2" className="text-violet-400 font-mono">
                {new Set(signals.map((s) => s.company_name)).size}
              </Text>
              <Text variant="caption" color="muted">Companies</Text>
            </div>
            <div className="glass-panel p-4 text-center">
              <Text variant="h2" className="text-emerald-400 font-mono">
                {new Set(signals.map((s) => s.source)).size}
              </Text>
              <Text variant="caption" color="muted">Sources</Text>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-3 animate-slide-up" style={{ animationDelay: "150ms" }}>
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search companies, roles, skills, locations..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-background border border-input text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          {workModes.length > 1 && (
            <select
              value={modeFilter}
              onChange={(e) => setModeFilter(e.target.value)}
              className="px-4 py-2.5 rounded-lg bg-background border border-input text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {workModes.map((m) => (
                <option key={m} value={m}>
                  {m === "all" ? "All Work Modes" : m}
                </option>
              ))}
            </select>
          )}
          <select
            value={sourceFilter}
            onChange={(e) => { setSourceFilter(e.target.value); fetchJobs(e.target.value); }}
            className="px-4 py-2.5 rounded-lg bg-background border border-input text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="all">All Sources</option>
            <option value="indeed">Indeed</option>
            <option value="internshala">Internshala</option>
            <option value="naukri">Naukri</option>
            <option value="shine">Shine</option>
            <option value="linkedin_jobs">LinkedIn Jobs</option>
            <option value="cutshort">Cutshort</option>
            <option value="foundit">Foundit</option>
            <option value="hirect">Hirect</option>
            <option value="instahyre">Instahyre</option>
            <option value="monster">Monster</option>
            <option value="timesjobs">TimesJobs</option>
            <option value="weekday">Weekday</option>
          </select>
        </div>

        {/* Loading */}
        {loading && (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="glass-panel p-4 space-y-3">
                <div className="flex items-center gap-3">
                  <Skeleton className="h-10 w-10 rounded-full" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-5 w-48" />
                    <Skeleton className="h-4 w-32" />
                  </div>
                </div>
                <Skeleton className="h-4 w-full" />
              </div>
            ))}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="glass-panel p-6 text-center text-destructive flex items-center justify-center gap-2">
            <AlertCircle className="h-5 w-5" />
            <Text variant="body">Failed to load job signals: {error}</Text>
          </div>
        )}

        {/* Signals List */}
        {!loading && !error && (
          <div className="space-y-3">
            {filtered.map((signal, index) => (
              <div
                key={signal.id}
                className="glass-panel glass-panel-hover p-5 space-y-3 animate-slide-up"
                style={{ animationDelay: `${200 + index * 50}ms` }}
              >
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                  <div className="flex items-start gap-3 flex-1 min-w-0">
                    <div className="h-10 w-10 rounded-full bg-blue-500/10 flex items-center justify-center shrink-0">
                      <Briefcase className="h-5 w-5 text-blue-400" />
                    </div>
                    <div className="min-w-0">
                      <Text variant="body" className="font-medium truncate">
                        {signal.title}
                      </Text>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5 flex-wrap">
                        <Building2 className="h-3 w-3" />
                        {signal.company_name}
                        {signal.location && (
                          <>
                            <span className="text-border">|</span>
                            <MapPin className="h-3 w-3" />
                            {signal.location}
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-wrap">
                    {signal.hiring_velocity >= 70 && (
                      <Badge variant="outline" className="bg-amber-500/10 text-amber-400 border-amber-500/20 animate-pulse">
                        <TrendingUp className="h-3 w-3 mr-1" />
                        Hot Hiring
                      </Badge>
                    )}
                    <Badge variant="secondary">{signal.source}</Badge>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                  {signal.work_mode && (
                    <span className="flex items-center gap-1">
                      <Users className="h-3 w-3" />
                      {signal.work_mode}
                    </span>
                  )}
                  {signal.experience && (
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {signal.experience}
                    </span>
                  )}
                  {signal.salary_range && (
                    <span className="text-emerald-400 font-medium">{signal.salary_range}</span>
                  )}
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {signal.posted_date}
                  </span>
                </div>

                {signal.skills.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {signal.skills.map((skill) => (
                      <Badge key={skill} variant="outline" className="text-xs">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                )}

                {/* Hiring Velocity Bar */}
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Hiring Velocity</span>
                    <span className={signal.hiring_velocity >= 70 ? "text-amber-400 font-medium" : "text-muted-foreground"}>
                      {signal.hiring_velocity}%
                    </span>
                  </div>
                  <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        signal.hiring_velocity >= 70
                          ? "bg-amber-500"
                          : signal.hiring_velocity >= 40
                          ? "bg-blue-500"
                          : "bg-muted-foreground/30"
                      }`}
                      style={{ width: `${signal.hiring_velocity}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && filtered.length === 0 && (
          <div className="glass-panel p-12 text-center animate-slide-up">
            <Briefcase className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <Text variant="h4" color="muted">
              No job signals match your filters
            </Text>
            <Text variant="body" color="muted">
              Try adjusting your search or work mode filter
            </Text>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
