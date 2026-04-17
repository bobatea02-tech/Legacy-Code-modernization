import { useState } from "react";
import { NavLink } from "react-router-dom";
import { KeyRound, RotateCcw } from "lucide-react";
import { cn } from "@/lib/utils";
import { useBackendStatus } from "@/hooks/useBackendStatus";
import { useApiKeyStatus } from "@/hooks/useApiKeyStatus";

const navItems = [
  { to: "/", label: "HOME" },
  { to: "/intake", label: "INTAKE" },
  { to: "/pipeline", label: "PIPELINE" },
  { to: "/results", label: "RESULTS" },
  { to: "/inspect", label: "INSPECT" },
  { to: "/history", label: "HISTORY" },
];

const Navbar = () => {
  const backendStatus = useBackendStatus();
  const { status: apiKey, resetQuota } = useApiKeyStatus();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 h-[72px] flex items-center justify-between px-6 hairline-b bg-background/80 backdrop-blur-md">
      {/* Left — brand */}
      <div className="flex items-center gap-3">
        <span className="font-headline text-foreground text-lg tracking-[-0.06em] uppercase">
          MODERNIZE NOW
        </span>
        <span className="w-1.5 h-1.5 rounded-full bg-foreground inline-block" />
        <span className="mono-label-md text-muted-foreground">V1.0</span>
      </div>

      {/* Centre — nav links */}
      <div className="flex items-center gap-0">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              cn(
                "mono-label-sm px-4 py-2 transition-colors duration-300",
                isActive
                  ? "text-primary"
                  : "text-muted-foreground hover:text-foreground"
              )
            }
          >
            {item.label}
          </NavLink>
        ))}
      </div>

      {/* Right — indicators */}
      <div className="flex items-center gap-2">
        {/* Only show API key indicator when backend is reachable */}
        {backendStatus === "connected" && (
          <ApiKeyIndicator status={apiKey} onReset={resetQuota} />
        )}
        <BackendIndicator status={backendStatus} />
      </div>
    </nav>
  );
};

// ── Backend connection indicator ─────────────────────────────────────────────

const BackendIndicator = ({ status }: { status: "connected" | "disconnected" | "checking" }) => {
  const isConnected    = status === "connected";
  const isChecking     = status === "checking";
  const isDisconnected = status === "disconnected";

  return (
    <div
      className={cn(
        "flex items-center gap-2 px-3 py-1.5 rounded border transition-all duration-500",
        isConnected    && "border-emerald-500/40 bg-emerald-500/10",
        isDisconnected && "border-red-500/40 bg-red-500/10",
        isChecking     && "border-muted/40 bg-muted/10",
      )}
      title={
        isConnected    ? "Backend connected" :
        isDisconnected ? "Backend unreachable" :
        "Checking backend..."
      }
    >
      <span className="relative flex h-2 w-2">
        {isConnected && (
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60" />
        )}
        <span className={cn(
          "relative inline-flex rounded-full h-2 w-2",
          isConnected    && "bg-emerald-400",
          isDisconnected && "bg-red-400",
          isChecking     && "bg-muted-foreground animate-pulse",
        )} />
      </span>
      <span className={cn(
        "mono-label-sm leading-none",
        isConnected    && "text-emerald-400",
        isDisconnected && "text-red-400",
        isChecking     && "text-muted-foreground",
      )}>
        {isConnected ? "CONNECTED" : isDisconnected ? "DISCONNECTED" : "CHECKING..."}
      </span>
    </div>
  );
};

// ── API key / quota indicator ─────────────────────────────────────────────────

interface ApiKeyIndicatorProps {
  status: ReturnType<typeof useApiKeyStatus>["status"];
  onReset: () => void;
}

const ApiKeyIndicator = ({ status, onReset }: ApiKeyIndicatorProps) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const [resetting, setResetting] = useState(false);

  const { quota_exhausted, usage_percent, total_tokens_used, daily_token_limit, total_requests } = status;

  const isExhausted = quota_exhausted || (status.failed_requests > 0 && total_requests === 0);

  const barColor =
    isExhausted || usage_percent >= 100 ? "bg-red-500" :
    usage_percent >= 80                  ? "bg-yellow-400" :
    usage_percent >= 50                  ? "bg-orange-400" :
    "bg-emerald-400";

  const labelColor =
    isExhausted || usage_percent >= 100 ? "text-red-400" :
    usage_percent >= 80                  ? "text-yellow-400" :
    "text-foreground/60";

  const borderColor =
    isExhausted || usage_percent >= 100 ? "border-red-500/40 bg-red-500/10" :
    usage_percent >= 80                  ? "border-yellow-400/40 bg-yellow-400/10" :
    "border-muted/30 bg-muted/5";

  const handleReset = async () => {
    setResetting(true);
    await onReset();
    setResetting(false);
  };

  return (
    <div
      className="relative"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <button
        className={cn(
          "flex items-center gap-2 px-3 py-1.5 rounded border transition-all duration-300",
          borderColor,
        )}
        onClick={() => setShowTooltip(v => !v)}
        title="Gemini API key usage"
      >
        <KeyRound size={11} className={labelColor} />

        {isExhausted ? (
          <span className="mono-label-sm text-red-400 animate-pulse">NEW_API_KEY_NEEDED</span>
        ) : (
          <>
            <div className="w-16 h-1.5 bg-muted/40 rounded-full overflow-hidden">
              <div
                className={cn("h-full rounded-full transition-all duration-700", barColor)}
                style={{ width: `${Math.min(usage_percent, 100)}%` }}
              />
            </div>
            <span className={cn("mono-label-sm tabular-nums", labelColor)}>
              {usage_percent.toFixed(0)}%
            </span>
          </>
        )}
      </button>

      {showTooltip && (
        <div className="absolute right-0 top-full mt-2 w-80 z-50 rounded border border-muted/30 bg-background/95 backdrop-blur-md shadow-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="mono-label-sm text-foreground/60">GEMINI_API_USAGE</span>
            <KeyRound size={12} className={labelColor} />
          </div>

          <div className="w-full h-2 bg-muted/30 rounded-full overflow-hidden mb-1">
            <div
              className={cn("h-full rounded-full transition-all duration-700", barColor)}
              style={{ width: `${Math.min(usage_percent, 100)}%` }}
            />
          </div>
          <div className="flex justify-between mb-4">
            <span className="font-mono text-xs text-foreground/40">
              {total_tokens_used.toLocaleString()} tokens used
            </span>
            <span className="font-mono text-xs text-foreground/40">
              {daily_token_limit.toLocaleString()} limit
            </span>
          </div>

          <div className="space-y-1.5 mb-4">
            <Row label="USAGE" value={`${usage_percent.toFixed(1)}%`} highlight={usage_percent >= 80} />
            <Row label="REQUESTS" value={total_requests.toString()} />
            {status.failed_requests > 0 && (
              <Row label="FAILED" value={status.failed_requests.toString()} danger />
            )}
          </div>

          {isExhausted && (
            <div className="mb-3 p-2 rounded bg-red-500/10 border border-red-500/30">
              <p className="mono-label-sm text-red-400 mb-1">NEW API KEY NEEDED</p>
              <p className="font-mono text-xs text-red-400/70 leading-relaxed">
                Update <code className="bg-red-500/10 px-1 rounded">LLM_API_KEY</code> in{" "}
                <code className="bg-red-500/10 px-1 rounded">backend/.env</code>, then click
                the button below — no restart needed.
              </p>
              {status.last_error && (
                <p className="font-mono text-xs text-foreground/30 mt-1 break-all">
                  {status.last_error.slice(0, 120)}
                </p>
              )}
            </div>
          )}

          <button
            onClick={() => handleReset()}
            disabled={resetting}
            className={cn(
              "w-full flex items-center justify-center gap-2 py-2 mono-label-sm rounded border transition-colors duration-200",
              resetting
                ? "text-muted-foreground border-muted/20 cursor-not-allowed"
                : "text-foreground/70 hover:text-foreground border-muted/30 hover:border-foreground/40 hover:bg-foreground/5"
            )}
          >
            <RotateCcw size={10} className={resetting ? "animate-spin" : ""} />
            {resetting ? "RELOADING KEY..." : "RELOAD_KEY_&_RESET"}
          </button>
          <p className="font-mono text-xs text-foreground/20 text-center mt-1">
            Reads new key from .env instantly
          </p>
        </div>
      )}
    </div>
  );
};

const Row = ({ label, value, highlight, danger }: { label: string; value: string; highlight?: boolean; danger?: boolean }) => (
  <div className="flex justify-between">
    <span className="mono-label-sm text-foreground/30">{label}</span>
    <span className={cn(
      "font-mono text-xs",
      danger     && "text-red-400",
      highlight  && !danger && "text-yellow-400",
      !danger && !highlight && "text-foreground/60",
    )}>{value}</span>
  </div>
);

export default Navbar;
