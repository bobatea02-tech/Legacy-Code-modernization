import { useState, useEffect } from "react";

const CommandBar = () => {
  const [time, setTime] = useState({ h: 0, m: 0, s: 0 });

  useEffect(() => {
    const interval = setInterval(() => {
      setTime((prev) => {
        let s = prev.s + 1;
        let m = prev.m;
        let h = prev.h;
        if (s >= 60) { s = 0; m++; }
        if (m >= 60) { m = 0; h++; }
        return { h, m, s };
      });
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const pad = (n: number) => String(n).padStart(2, "0");

  const labels = ["CONTEXT_OPTIMIZED", "MULTI_FILE_MODE", "DETERMINISTIC_ENGINE"];

  return (
    <section className="hairline-b grid grid-cols-1 md:grid-cols-4">
      {/* Repo input */}
      <div className="flex items-center px-6 py-5 hairline-r">
        <input
          type="text"
          placeholder="REPOSITORY_URL"
          className="w-full bg-transparent font-mono text-sm text-foreground placeholder:text-muted-foreground outline-none hairline-b pb-2"
        />
      </div>

      {/* Analyze button */}
      <div className="flex items-center justify-center px-6 py-5 hairline-r">
        <button className="mono-label bg-secondary text-secondary-foreground px-8 py-3 text-xs tracking-[0.3em] hover:bg-primary hover:text-primary-foreground transition-colors duration-300 w-full">
          ANALYZE
        </button>
      </div>

      {/* Countdown */}
      <div className="flex items-center justify-center px-6 py-5 hairline-r font-mono text-2xl text-foreground">
        <span className="tabular-nums">{pad(time.h)}</span>
        <span className="text-foreground/20 mx-1">:</span>
        <span className="tabular-nums">{pad(time.m)}</span>
        <span className="text-foreground/20 mx-1">:</span>
        <span className="tabular-nums">{pad(time.s)}</span>
      </div>

      {/* System labels */}
      <div className="flex flex-col justify-center gap-2 px-6 py-5">
        {labels.map((label) => (
          <span key={label} className="mono-label-sm text-muted-foreground">
            {label}
          </span>
        ))}
      </div>
    </section>
  );
};

export default CommandBar;
