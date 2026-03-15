import { Cpu } from "lucide-react";
import { motion } from "framer-motion";

const constraints = [
  "CONTEXT_OPTIMIZED",
  "MULTI_FILE_DEPENDENCY_MODE",
  "PROVIDER_AGNOSTIC",
  "NO_HIDDEN_STATE",
];

const SystemConstraints = () => (
  <motion.div
    className="hairline-b p-6"
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5, delay: 0.6 }}
  >
    <span className="mono-label-sm text-muted-foreground block mb-4">SYSTEM_CONSTRAINTS</span>
    <div className="flex flex-wrap gap-3">
      {constraints.map((c, i) => (
        <motion.span
          key={c}
          className="mono-label-sm text-foreground/20 hairline px-3 py-1.5 flex items-center gap-2"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.7 + i * 0.08 }}
        >
          <Cpu size={8} className="text-primary/40" />
          {c}
        </motion.span>
      ))}
    </div>
  </motion.div>
);

export default SystemConstraints;
