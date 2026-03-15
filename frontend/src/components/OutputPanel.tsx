import { useState } from "react";
import { Copy, Download } from "lucide-react";

const fileTree = [
  { name: "src/", depth: 0, active: false },
  { name: "main.py", depth: 1, active: false },
  { name: "utils/", depth: 1, active: false },
  { name: "legacy_handler.py", depth: 2, active: true },
  { name: "config.py", depth: 2, active: false },
  { name: "tests/", depth: 0, active: false },
  { name: "test_handler.py", depth: 1, active: false },
];

const sampleCode = `// modernized_handler.ts
import { pipe, map } from 'fp-ts/function';
import { TaskEither } from 'fp-ts/TaskEither';

interface LegacyPayload {
  id: string;
  data: Record<string, unknown>;
  timestamp: number;
}

export const processPayload = (
  payload: LegacyPayload
): TaskEither<Error, Result> =>
  pipe(
    validateSchema(payload),
    map(normalizeKeys),
    map(transformTypes),
    map(generateOutput)
  );`;

const OutputPanel = () => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(sampleCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section className="hairline-t hairline-b">
      <div className="grid grid-cols-1 md:grid-cols-[300px_1fr]">
        {/* File tree */}
        <div className="hairline-r p-6 min-h-[400px]">
          <span className="mono-label-sm text-muted-foreground block mb-4">
            LEGACY_FILE_TREE
          </span>
          <div className="space-y-1">
            {fileTree.map((file, i) => (
              <div
                key={i}
                className={`font-mono text-sm cursor-pointer transition-colors duration-300 ${
                  file.active ? "text-primary" : "text-foreground/60 hover:text-foreground"
                }`}
                style={{ paddingLeft: `${file.depth * 16}px` }}
              >
                {file.name}
              </div>
            ))}
          </div>
        </div>

        {/* Code preview */}
        <div className="p-6 min-h-[400px] flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <span className="mono-label-sm text-muted-foreground">
              MODERNIZED_OUTPUT
            </span>
            <button
              onClick={handleCopy}
              className="hairline px-3 py-1.5 mono-label-sm text-muted-foreground hover:text-primary hover:border-primary transition-colors duration-300 flex items-center gap-2"
              style={{ borderColor: copied ? "hsl(239 84% 67%)" : undefined }}
            >
              <Copy size={12} />
              {copied ? "COPIED" : "COPY"}
            </button>
          </div>

          <pre className="font-mono text-sm text-foreground/80 leading-relaxed overflow-auto flex-1">
            <code>{sampleCode}</code>
          </pre>

          <div className="mt-6">
            <button className="hairline px-6 py-3 mono-label-sm text-foreground/60 hover:text-primary hover:border-primary transition-colors duration-300 flex items-center gap-2">
              <Download size={14} />
              DOWNLOAD_PACKAGE
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};

export default OutputPanel;
