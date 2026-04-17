import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "@/components/Navbar";
import Index from "./pages/Index";
import IntakeView from "./pages/IntakeView";
import PipelineView from "./pages/PipelineView";
import ResultsView from "./pages/ResultsView";
import InspectView from "./pages/InspectView";
import HistoryView from "./pages/HistoryView";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <div className="min-h-screen bg-background text-foreground">
          <div className="noise-overlay" />
          <Navbar />
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/intake" element={<IntakeView />} />
            <Route path="/pipeline" element={<PipelineView />} />
            <Route path="/results" element={<ResultsView />} />
            <Route path="/inspect" element={<InspectView />} />
            <Route path="/history" element={<HistoryView />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </div>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
