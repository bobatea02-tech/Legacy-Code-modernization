import { Hexagon, Triangle, Square, Zap, Cpu, Shield } from "lucide-react";
import { useState } from "react";

const features = [
  {
    tag: "SYSTEM_01",
    icon: Hexagon,
    title: "CODE_TRANSLATION",
    subtitle: "Multi-language AST transformation with deterministic output",
  },
  {
    tag: "SYSTEM_02",
    icon: Triangle,
    title: "DEPENDENCY_GRAPH",
    subtitle: "Automated dependency resolution and version mapping",
  },
  {
    tag: "SYSTEM_03",
    icon: Square,
    title: "TYPE_INFERENCE",
    subtitle: "Static analysis with full type coverage generation",
  },
  {
    tag: "SYSTEM_04",
    icon: Zap,
    title: "RUNTIME_VALIDATION",
    subtitle: "Dual-run comparison engine for behavioral parity",
  },
  {
    tag: "SYSTEM_05",
    icon: Cpu,
    title: "PATTERN_DETECTION",
    subtitle: "Legacy anti-pattern identification and refactoring",
  },
  {
    tag: "SYSTEM_06",
    icon: Shield,
    title: "SECURITY_AUDIT",
    subtitle: "Vulnerability scanning during modernization pipeline",
  },
];

const BentoGrid = () => {
  return (
    <section className="grid grid-cols-1 md:grid-cols-3">
      {features.map((feature, i) => (
        <BentoCard key={feature.tag} feature={feature} index={i} />
      ))}
    </section>
  );
};

interface BentoCardProps {
  feature: (typeof features)[0];
  index: number;
}

const BentoCard = ({ feature, index }: BentoCardProps) => {
  const [hovered, setHovered] = useState(false);
  const Icon = feature.icon;

  return (
    <div
      className={`relative h-[400px] p-6 flex flex-col justify-between transition-colors duration-300
        ${index % 3 !== 2 ? "hairline-r" : ""}
        ${index < 3 ? "hairline-b" : ""}
      `}
      style={{ backgroundColor: hovered ? "rgba(255,255,255,0.02)" : "transparent" }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <span className="mono-label-sm text-muted-foreground">{feature.tag}</span>

      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <Icon
          size={120}
          strokeWidth={0.5}
          className="text-foreground transition-opacity duration-300"
          style={{ opacity: hovered ? 1 : 0.2 }}
        />
      </div>

      <div>
        <h3 className="font-headline text-foreground text-2xl tracking-[-0.06em] uppercase mb-1">
          {feature.title}
        </h3>
        <p className="font-body text-sm text-foreground/40">{feature.subtitle}</p>
      </div>
    </div>
  );
};

export default BentoGrid;
