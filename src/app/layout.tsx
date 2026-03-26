import type { Metadata } from "next";
import { QueryClientProviderWrapper } from "@/components/query-client-provider";
import { ThemeProvider } from "@/components/theme-provider";
import { TooltipProvider } from "@/components/ui/tooltip";
import { LeadProvider } from "@/hooks/use-leads";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import "./globals.css";

export const metadata: Metadata = {
  title: "LeadIQ — AI Lead Intelligence Platform",
  description:
    "AI-powered lead intelligence, scoring, and outreach platform. Automatically detect demand signals, score leads, and generate personalized outreach.",
  keywords: ["lead generation", "AI", "sales intelligence", "outreach", "CRM"],
  authors: [{ name: "LeadIQ" }],
  openGraph: {
    title: "LeadIQ — AI Lead Intelligence Platform",
    description: "AI-powered lead intelligence, scoring, and outreach platform.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <QueryClientProviderWrapper>
          <ThemeProvider defaultTheme="dark" storageKey="leadiq-theme">
            <TooltipProvider>
              <LeadProvider>
                <Toaster />
                <Sonner />
                {children}
              </LeadProvider>
            </TooltipProvider>
          </ThemeProvider>
        </QueryClientProviderWrapper>
      </body>
    </html>
  );
}
