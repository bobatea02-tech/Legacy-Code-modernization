import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";
import { useBackendStatus } from "@/hooks/useBackendStatus";

const navItems = [
  { to: "/", label: "HOME" },
  { to: "/intake", label: "INTAKE" },
  { to: "/pipeline", label: "PIPELINE" },
  { to: "/results", label: "RESULTS" },
  { to: "/inspect", label: "INSPECT" },
];

const Navbar = () => {
  const backendStatus = useBackendStatus();

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

      {/* Right — backend connection indicator */}
      <BackendIndicator status={backendStatus} />
    </nav>
  );
};

// ── Indicator component ──────────────────────────────────────────────────────

interface BackendIndicatorProps {
  status: "connected" | "disconnected" | "checking";
}

const BackendIndicator = ({ status }: BackendIndicatorProps) => {
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
        "Checking backend…"
      }
    >
      {/* Animated dot */}
      <span className="relative flex h-2 w-2">
        {/* Ping ring — only when connected */}
        {isConnected && (
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60" />
        )}
        <span
          className={cn(
            "relative inline-flex rounded-full h-2 w-2",
            isConnected    && "bg-emerald-400",
            isDisconnected && "bg-red-400",
            isChecking     && "bg-muted-foreground animate-pulse",
          )}
        />
      </span>

      {/* Label */}
      <span
        className={cn(
          "mono-label-sm leading-none",
          isConnected    && "text-emerald-400",
          isDisconnected && "text-red-400",
          isChecking     && "text-muted-foreground",
        )}
      >
        {isConnected    ? "CONNECTED" :
         isDisconnected ? "DISCONNECTED" :
         "CHECKING…"}
      </span>
    </div>
  );
};

export default Navbar;
