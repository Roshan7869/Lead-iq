"use client";

/**
 * WebMCPProvider — Browser WebMCP Layer (Chrome early preview).
 *
 * Registers client-side MCP tools via `window.agent.provideContext()`.
 * These tools let browser AI agents interact with the LeadIQ dashboard
 * directly — filtering leads, exporting CSVs, marking leads contacted.
 *
 * The `if (!("agent" in window)) return` guard means this silently does
 * nothing in browsers that don't support WebMCP yet — zero risk.
 */

import { useEffect } from "react";
import { useLeads } from "@/hooks/use-leads";

// Extend Window type for WebMCP agent API
declare global {
  interface Window {
    agent?: {
      provideContext: (context: {
        name: string;
        description: string;
        tools: Array<{
          name: string;
          description: string;
          parameters: Record<string, unknown>;
          handler: (...args: unknown[]) => Promise<unknown>;
        }>;
      }) => void;
    };
  }
}

export function WebMCPProvider({ children }: { children: React.ReactNode }) {
  const { leads, refreshLeads } = useLeads();

  useEffect(() => {
    // Guard: only register if browser supports WebMCP
    if (!("agent" in window)) return;

    window.agent?.provideContext({
      name: "leadiq-dashboard",
      description:
        "LeadIQ AI lead intelligence dashboard. Filter, export, and manage B2B leads.",
      tools: [
        {
          name: "filter_leads_by_score",
          description:
            "Filter visible leads by minimum score. Returns leads with final_score >= threshold.",
          parameters: {
            type: "object",
            properties: {
              min_score: {
                type: "number",
                description: "Minimum score threshold (0-100)",
              },
            },
            required: ["min_score"],
          },
          handler: async (...args: unknown[]) => {
            const params = args[0] as { min_score: number };
            const minScore = params.min_score ?? 0;
            const filtered = leads.filter(
              (l) => (l.intentScore ?? 0) >= minScore
            );
            return {
              count: filtered.length,
              leads: filtered.map((l) => ({
                id: l.id,
                name: l.name,
                company: l.company,
                score: l.intentScore,
                stage: l.stage,
                priority: l.priority,
              })),
            };
          },
        },
        {
          name: "export_leads_csv",
          description:
            "Export currently visible leads as a CSV download. Triggers a file download in the browser.",
          parameters: { type: "object", properties: {} },
          handler: async () => {
            const headers = [
              "ID",
              "Name",
              "Company",
              "Title",
              "Stage",
              "Priority",
              "Intent Score",
              "Source",
              "Detected At",
            ];
            const rows = leads.map((l) =>
              [
                l.id,
                l.name,
                l.company,
                l.title,
                l.stage,
                l.priority,
                l.intentScore,
                l.source,
                l.detectedAt,
              ].join(",")
            );
            const csv = [headers.join(","), ...rows].join("\n");
            const blob = new Blob([csv], { type: "text/csv" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `leadiq-export-${new Date().toISOString().slice(0, 10)}.csv`;
            a.click();
            URL.revokeObjectURL(url);
            return {
              success: true,
              count: leads.length,
              filename: a.download,
            };
          },
        },
        {
          name: "mark_lead_contacted",
          description:
            'Mark a lead as "contacted" in the pipeline by calling the backend API.',
          parameters: {
            type: "object",
            properties: {
              lead_id: {
                type: "string",
                description: "UUID of the lead to mark as contacted",
              },
            },
            required: ["lead_id"],
          },
          handler: async (...args: unknown[]) => {
            const params = args[0] as { lead_id: string };
            try {
              const res = await fetch(`/api/lead/${params.lead_id}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ stage: "contacted" }),
              });
              if (!res.ok) {
                return {
                  success: false,
                  error: `API returned ${res.status}`,
                };
              }
              await refreshLeads();
              return { success: true, lead_id: params.lead_id, new_stage: "contacted" };
            } catch (err) {
              return {
                success: false,
                error: err instanceof Error ? err.message : "Unknown error",
              };
            }
          },
        },
        {
          name: "get_dashboard_summary",
          description:
            "Get a summary of the current dashboard state: total leads, by priority, by stage.",
          parameters: { type: "object", properties: {} },
          handler: async () => {
            const byPriority = leads.reduce(
              (acc, l) => {
                acc[l.priority] = (acc[l.priority] || 0) + 1;
                return acc;
              },
              {} as Record<string, number>
            );
            const byStage = leads.reduce(
              (acc, l) => {
                acc[l.stage] = (acc[l.stage] || 0) + 1;
                return acc;
              },
              {} as Record<string, number>
            );
            return {
              total: leads.length,
              by_priority: byPriority,
              by_stage: byStage,
            };
          },
        },
      ],
    });
  }, [leads, refreshLeads]);

  return <>{children}</>;
}
