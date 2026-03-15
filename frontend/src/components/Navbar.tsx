import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";

const navItems = [
  { to: "/", label: "HOME" },
  { to: "/intake", label: "INTAKE" },
  { to: "/pipeline", label: "PIPELINE" },
  { to: "/results", label: "RESULTS" },
  { to: "/inspect", label: "INSPECT" },
];

const Navbar = () => {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 h-[72px] flex items-center justify-between px-6 hairline-b bg-background/80 backdrop-blur-md">
      <div className="flex items-center gap-3">
        <span className="font-headline text-foreground text-lg tracking-[-0.06em] uppercase">
          MODERNIZE NOW
        </span>
        <span className="w-1.5 h-1.5 rounded-full bg-foreground inline-block" />
        <span className="mono-label-md text-muted-foreground">V1.0</span>
      </div>

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

      <div className="w-[1px]" />
    </nav>
  );
};

export default Navbar;
