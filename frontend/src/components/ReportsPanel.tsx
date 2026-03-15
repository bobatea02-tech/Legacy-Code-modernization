import { useState } from "react";

const tabs = [
  "DETERMINISM_REPORT",
  "FAILURE_ANALYSIS",
  "QUALITY_SCORE",
  "TRANSLATION_SAMPLE",
];

const reportData: Record<string, object> = {
  DETERMINISM_REPORT: {
    run_count: 2,
    sha256_match: true,
    output_hash: "a3f8c2...e91b",
    variance_detected: false,
    confidence: 0.997,
  },
  FAILURE_ANALYSIS: {
    total_files: 47,
    failed_translations: 2,
    failure_reasons: ["UNSUPPORTED_DECORATOR", "CIRCULAR_IMPORT"],
    recovery_applied: true,
  },
  QUALITY_SCORE: {
    overall: 94.2,
    type_coverage: 98.1,
    test_parity: 91.7,
    complexity_delta: -12.4,
  },
  TRANSLATION_SAMPLE: {
    source_lang: "PYTHON_3.8",
    target_lang: "TYPESCRIPT_5.x",
    lines_processed: 12847,
    avg_time_per_file_ms: 340,
  },
};

const ReportsPanel = () => {
  const [activeTab, setActiveTab] = useState(tabs[0]);

  return (
    <section className="hairline-b">
      {/* Tab bar */}
      <div className="flex overflow-x-auto">
        {tabs.map((tab, i) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 px-6 py-4 mono-label-sm transition-colors duration-300 ${
              i < tabs.length - 1 ? "hairline-r" : ""
            } ${
              activeTab === tab
                ? "text-primary"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="hairline-t p-6 min-h-[250px]">
        <pre className="font-mono text-sm text-foreground/70 leading-loose">
          {JSON.stringify(reportData[activeTab], null, 2)}
        </pre>
      </div>
    </section>
  );
};

export default ReportsPanel;
