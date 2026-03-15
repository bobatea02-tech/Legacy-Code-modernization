import { motion, useScroll, useTransform } from "framer-motion";
import { useRef } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Zap, Shield, GitBranch, Binary, Terminal, Cpu } from "lucide-react";

const STAGGER = 0.08;

const RevealText = ({ text, delay = 0, className = "" }: { text: string; delay?: number; className?: string }) => (
  <span className="inline-flex overflow-hidden">
    <motion.span
      initial={{ y: "110%" }}
      animate={{ y: 0 }}
      transition={{ duration: 0.8, delay, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {text}
    </motion.span>
  </span>
);

const FloatingGlyph = ({ char, x, y, delay }: { char: string; x: string; y: string; delay: number }) => (
  <motion.span
    className="absolute font-mono text-foreground/[0.04] select-none pointer-events-none"
    style={{ left: x, top: y, fontSize: "clamp(3rem, 8vw, 10rem)" }}
    initial={{ opacity: 0, scale: 0.5 }}
    animate={{ opacity: 1, scale: 1 }}
    transition={{ duration: 1.5, delay, ease: "easeOut" }}
  >
    <motion.span
      animate={{ y: [0, -15, 0] }}
      transition={{ duration: 6, repeat: Infinity, delay: delay * 2, ease: "easeInOut" }}
      className="inline-block"
    >
      {char}
    </motion.span>
  </motion.span>
);

const features = [
  { icon: GitBranch, title: "MULTI_FILE_DEPENDENCY", desc: "Full dependency graph resolution across entire repositories" },
  { icon: Shield, title: "DETERMINISTIC_OUTPUT", desc: "SHA-256 verified identical outputs on every run" },
  { icon: Binary, title: "AST_LEVEL_PARSE", desc: "Abstract syntax tree analysis, not regex pattern matching" },
  { icon: Zap, title: "CONTEXT_OPTIMIZED", desc: "Intelligent context pruning minimizes token waste" },
  { icon: Terminal, title: "PYTHON_NATIVE", desc: "First-class Python modernization with type inference" },
  { icon: Cpu, title: "PROVIDER_AGNOSTIC", desc: "No vendor lock-in, swap LLM backends without output drift" },
];

const LandingPage = () => {
  const navigate = useNavigate();
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: containerRef });
  const lineWidth = useTransform(scrollYProgress, [0, 0.3], ["0%", "100%"]);

  return (
    <div ref={containerRef} className="min-h-screen pt-[72px]">
      {/* HERO */}
      <section className="relative h-[calc(100vh-72px)] flex flex-col justify-end p-6 md:p-12 overflow-hidden">
        {/* Background glyphs */}
        <FloatingGlyph char="{" x="10%" y="15%" delay={0.5} />
        <FloatingGlyph char="}" x="85%" y="20%" delay={0.7} />
        <FloatingGlyph char="λ" x="70%" y="60%" delay={0.9} />
        <FloatingGlyph char="→" x="20%" y="70%" delay={1.1} />
        <FloatingGlyph char="//" x="50%" y="10%" delay={0.6} />
        <FloatingGlyph char="∴" x="80%" y="75%" delay={1.3} />

        {/* Scanning line */}
        <motion.div
          className="absolute left-0 right-0 h-px bg-primary/30"
          initial={{ top: "0%" }}
          animate={{ top: ["0%", "100%", "0%"] }}
          transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
        />

        {/* Title block */}
        <div className="relative z-10 mb-12">
          <div className="overflow-hidden mb-2">
            <motion.span
              className="mono-label-sm text-primary block"
              initial={{ x: -40, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              LEGACY_CODE_MODERNIZATION_ENGINE
            </motion.span>
          </div>

          <h1 className="text-foreground leading-[0.85]" style={{ fontSize: "clamp(3rem, 12vw, 14rem)", letterSpacing: "-0.06em" }}>
            <RevealText text="MODERNIZE" delay={0.3} />
            <br />
            <RevealText text="NOW" delay={0.3 + STAGGER} className="text-primary" />
          </h1>

          <motion.p
            className="font-body text-muted-foreground text-sm md:text-base max-w-lg mt-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.8 }}
          >
            Deterministic, dependency-aware legacy code translation.
            <br />
            Python-native. No hallucination. No hidden state.
          </motion.p>
        </div>

        {/* CTA row */}
        <motion.div
          className="relative z-10 flex items-center gap-6 mb-12"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2 }}
        >
          <button
            onClick={() => navigate("/intake")}
            className="group mono-label bg-primary text-primary-foreground px-8 py-4 text-xs tracking-[0.3em] flex items-center gap-3 hover:gap-5 transition-all duration-300"
          >
            START_PIPELINE
            <ArrowRight size={14} className="transition-transform duration-300 group-hover:translate-x-1" />
          </button>
          <span className="mono-label-sm text-muted-foreground hidden md:block">
            NO_CREDIT_CARD — NO_VENDOR_LOCK
          </span>
        </motion.div>

        {/* Bottom status bar */}
        <motion.div
          className="absolute bottom-0 left-0 right-0 hairline-t flex items-center px-6 md:px-12 py-3 gap-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.5 }}
        >
          {["DETERMINISTIC", "PYTHON_NATIVE", "SHA256_VERIFIED", "CONTEXT_PRUNED"].map((label, i) => (
            <motion.span
              key={label}
              className="mono-label-sm text-foreground/20 flex items-center gap-2"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1.5 + i * 0.1 }}
            >
              <span className="w-1 h-1 rounded-full bg-primary/40" />
              {label}
            </motion.span>
          ))}
        </motion.div>
      </section>

      {/* Divider with animated line */}
      <div className="relative h-px bg-foreground/[0.08]">
        <motion.div className="absolute inset-y-0 left-0 bg-primary/60" style={{ width: lineWidth }} />
      </div>

      {/* FEATURES GRID */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
        {features.map((f, i) => (
          <motion.div
            key={f.title}
            className={`group p-8 md:p-10 min-h-[280px] flex flex-col justify-between cursor-default
              ${i % 3 !== 2 ? "hairline-r" : ""}
              ${i < 3 ? "hairline-b" : ""}
            `}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.5, delay: i * 0.08 }}
          >
            <div className="flex items-start justify-between">
              <span className="mono-label-sm text-muted-foreground">
                SYSTEM_{String(i + 1).padStart(2, "0")}
              </span>
              <f.icon
                size={28}
                className="text-foreground/10 group-hover:text-primary/80 transition-colors duration-500"
              />
            </div>
            <div>
              <h3 className="text-foreground text-lg md:text-xl mb-2">{f.title}</h3>
              <p className="font-body text-muted-foreground text-sm">{f.desc}</p>
            </div>
          </motion.div>
        ))}
      </section>

      {/* HOW IT WORKS — Animated pipeline strip */}
      <section className="hairline-t">
        <div className="px-6 md:px-12 py-12">
          <motion.span
            className="mono-label-sm text-muted-foreground block mb-8"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
          >
            EXECUTION_PIPELINE
          </motion.span>
        </div>
        <div className="grid grid-cols-3 md:grid-cols-9 hairline-t">
          {[
            "INGEST", "AST_PARSE", "DEP_GRAPH", "CTX_PRUNE",
            "TRANSLATE", "VALIDATE", "DUAL_RUN", "BENCHMARK", "REPORT"
          ].map((phase, i) => (
            <motion.div
              key={phase}
              className="hairline-r p-4 md:p-6 flex flex-col items-center gap-3"
              initial={{ opacity: 0, scale: 0.8 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.06, duration: 0.4 }}
            >
              <motion.div
                className="w-3 h-3 rounded-full bg-foreground/10"
                whileInView={{
                  backgroundColor: ["hsl(0 0% 100% / 0.1)", "hsl(239 84% 67% / 1)", "hsl(239 84% 67% / 0.3)"],
                }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15, duration: 0.8 }}
              />
              <span className="mono-label-sm text-muted-foreground text-center leading-tight">
                {phase}
              </span>
            </motion.div>
          ))}
        </div>
      </section>

      {/* STATS ROW */}
      <section className="hairline-t grid grid-cols-2 md:grid-cols-4">
        {[
          { value: "100+", label: "FILES_PER_REPO" },
          { value: "93.6%", label: "SUCCESS_RATE" },
          { value: "340ms", label: "AVG_LATENCY" },
          { value: "0", label: "HIDDEN_STATE" },
        ].map((stat, i) => (
          <motion.div
            key={stat.label}
            className={`p-8 md:p-12 flex flex-col items-center gap-2 ${i < 3 ? "hairline-r" : ""}`}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.1 }}
          >
            <motion.span
              className="font-headline text-foreground text-3xl md:text-5xl"
              initial={{ scale: 0.5 }}
              whileInView={{ scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 + 0.2, type: "spring", stiffness: 200 }}
            >
              {stat.value}
            </motion.span>
            <span className="mono-label-sm text-muted-foreground">{stat.label}</span>
          </motion.div>
        ))}
      </section>

      {/* FOOTER CTA */}
      <section className="hairline-t p-12 md:p-24 flex flex-col items-center text-center">
        <motion.h2
          className="text-foreground text-3xl md:text-6xl mb-6"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          READY_TO_MODERNIZE?
        </motion.h2>
        <motion.button
          onClick={() => navigate("/intake")}
          className="group mono-label bg-primary text-primary-foreground px-10 py-4 text-xs tracking-[0.3em] flex items-center gap-3 hover:gap-5 transition-all duration-300"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2 }}
        >
          START_PIPELINE
          <ArrowRight size={14} />
        </motion.button>
      </section>
    </div>
  );
};

export default LandingPage;
