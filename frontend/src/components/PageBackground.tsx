import { motion } from "framer-motion";

const PageBackground = () => (
  <>
    {/* Scanning line */}
    <motion.div
      className="fixed left-0 right-0 h-px bg-primary/20 pointer-events-none z-10"
      initial={{ top: "0%" }}
      animate={{ top: ["0%", "100%", "0%"] }}
      transition={{ duration: 12, repeat: Infinity, ease: "linear" }}
    />

    {/* Floating grid dots */}
    {[
      { x: "8%", y: "20%", d: 0 },
      { x: "92%", y: "35%", d: 0.5 },
      { x: "75%", y: "80%", d: 1.2 },
      { x: "15%", y: "65%", d: 0.8 },
      { x: "50%", y: "12%", d: 1.5 },
      { x: "35%", y: "90%", d: 0.3 },
    ].map((dot, i) => (
      <motion.div
        key={i}
        className="fixed w-1 h-1 rounded-full bg-primary/20 pointer-events-none z-0"
        style={{ left: dot.x, top: dot.y }}
        animate={{
          opacity: [0.1, 0.4, 0.1],
          scale: [1, 1.8, 1],
        }}
        transition={{
          duration: 4,
          repeat: Infinity,
          delay: dot.d,
          ease: "easeInOut",
        }}
      />
    ))}

    {/* Corner brackets */}
    <motion.div
      className="fixed top-[80px] left-4 pointer-events-none z-0 text-foreground/[0.04] font-mono text-6xl"
      animate={{ opacity: [0.02, 0.06, 0.02] }}
      transition={{ duration: 5, repeat: Infinity }}
    >
      &#91;
    </motion.div>
    <motion.div
      className="fixed bottom-4 right-4 pointer-events-none z-0 text-foreground/[0.04] font-mono text-6xl"
      animate={{ opacity: [0.02, 0.06, 0.02] }}
      transition={{ duration: 5, repeat: Infinity, delay: 2.5 }}
    >
      &#93;
    </motion.div>
  </>
);

export default PageBackground;
