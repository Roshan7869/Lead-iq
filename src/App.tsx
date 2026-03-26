import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { LeadProvider } from "@/hooks/use-leads";
import { ThemeProvider } from "@/components/theme-provider";
import Overview from "./pages/Overview";
import Pipeline from "./pages/Pipeline";
import DemandMiner from "./pages/DemandMiner";
import CommandCenter from "./pages/CommandCenter";
import ROITracker from "./pages/ROITracker";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider defaultTheme="dark" storageKey="leadiq-theme">
      <TooltipProvider>
        <LeadProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<Overview />} />
              <Route path="/pipeline" element={<Pipeline />} />
              <Route path="/demand-miner" element={<DemandMiner />} />
              <Route path="/command-center" element={<CommandCenter />} />
              <Route path="/roi-tracker" element={<ROITracker />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </LeadProvider>
      </TooltipProvider>
    </ThemeProvider>
  </QueryClientProvider>
);

export default App;
