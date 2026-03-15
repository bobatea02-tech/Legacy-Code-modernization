import { Upload, Link, Shield, FileArchive } from "lucide-react";
import { motion } from "framer-motion";
import { usePipelineStore } from "@/stores/pipelineStore";
import { apiClient, ApiError } from "@/services/api";
import { useNavigate } from "react-router-dom";
import { useState, useRef } from "react";
import PageBackground from "@/components/PageBackground";
import SystemConstraints from "@/components/SystemConstraints";

const IntakeView = () => {
  const {
    repoUrl,
    repoHash,
    deterministicMode,
    strictValidation,
    contextWindowLimit,
    isValid,
    useBackend,
    setRepoUrl,
    setStrictValidation,
    startPipeline,
    setRunId,
  } = usePipelineStore();
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.name.endsWith('.zip')) {
      setError('Only ZIP files are supported');
      return;
    }

    // Validate file size (100MB limit)
    const maxSize = 100 * 1024 * 1024;
    if (file.size > maxSize) {
      setError('File too large. Maximum size is 100MB');
      return;
    }

    setError(null);
    setUploadedFile(file);

    if (useBackend) {
      // Upload to backend immediately
      setUploading(true);
      try {
        const result = await apiClient.uploadRepository(file);
        // Store the repo_id in the repoUrl field (it will be used for pipeline start)
        // This also triggers validation in the store
        setRepoUrl(result.repo_id);
        console.log('Upload successful:', result);
      } catch (err) {
        if (err instanceof ApiError) {
          setError(`Upload failed: ${err.message}`);
        } else {
          setError('Failed to upload file');
        }
        setUploadedFile(null);
      } finally {
        setUploading(false);
      }
    } else {
      // Demo mode - just store the file name and mark as valid
      setRepoUrl(`file://${file.name}`);
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleStart = async () => {
    setError(null);

    if (useBackend) {
      // Real backend flow
      setSubmitting(true);
      try {
        let finalRepoId = repoUrl;
        
        // Check if repoUrl is a Git URL (not a repo_id from file upload)
        if (repoUrl && (repoUrl.startsWith('http://') || repoUrl.startsWith('https://') || repoUrl.startsWith('git@'))) {
          // It's a Git URL, need to upload it first
          console.log('Uploading from Git URL:', repoUrl);
          const uploadResult = await apiClient.uploadRepositoryFromUrl(repoUrl);
          finalRepoId = uploadResult.repo_id;
          console.log('Git repository uploaded:', uploadResult);
        }
        
        // Start pipeline with repo_id
        const response = await apiClient.startModernizationPipeline(
          finalRepoId,
          "python"
        );

        setRunId(response.run_id);
        startPipeline();
        navigate("/pipeline");
      } catch (err) {
        if (err instanceof ApiError) {
          setError(`API Error (${err.status}): ${err.message}`);
        } else {
          setError("Failed to connect to backend. Check VITE_API_BASE_URL.");
        }
      } finally {
        setSubmitting(false);
      }
    } else {
      // Demo mode
      startPipeline();
      navigate("/pipeline");
    }
  };

  return (
    <div className="min-h-screen pt-[72px] relative">
      <PageBackground />

      <motion.div
        className="hairline-b px-6 py-12"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <h1 className="text-foreground text-4xl md:text-6xl leading-none">
          REPOSITORY
          <br />
          INTAKE
        </h1>
        <p className="font-body text-muted-foreground text-sm mt-4 max-w-md">
          Submit a repository and configure execution parameters for the
          deterministic modernization pipeline.
        </p>
      </motion.div>

      {error && (
        <motion.div
          className="hairline-b px-6 py-4 bg-destructive/5"
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
        >
          <span className="mono-label-sm text-destructive">⚠ {error}</span>
        </motion.div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2">
        {/* Repository Input Panel */}
        <motion.div
          className="hairline-r hairline-b p-6"
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <span className="mono-label-sm text-muted-foreground block mb-6">
            REPOSITORY_INPUT
          </span>

          {/* Hidden file input */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".zip"
            onChange={handleFileSelect}
            className="hidden"
          />

          {/* Upload area */}
          <div 
            onClick={handleUploadClick}
            className="hairline p-8 mb-6 flex flex-col items-center justify-center gap-3 min-h-[140px] cursor-pointer hover:bg-foreground/[0.02] transition-colors duration-300"
          >
            {uploading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div>
                <span className="mono-label-sm text-primary">UPLOADING...</span>
              </>
            ) : uploadedFile ? (
              <>
                <FileArchive size={20} className="text-primary" />
                <span className="mono-label-sm text-primary">{uploadedFile.name}</span>
                <span className="mono-label-sm text-foreground/40">
                  {(uploadedFile.size / (1024 * 1024)).toFixed(2)} MB
                </span>
                <span className="mono-label-sm text-foreground/20 text-xs">CLICK TO CHANGE</span>
              </>
            ) : (
              <>
                <Upload size={20} className="text-muted-foreground" />
                <span className="mono-label-sm text-muted-foreground">
                  UPLOAD_ZIP_FILE
                </span>
                <span className="mono-label-sm text-foreground/20">OR</span>
              </>
            )}
          </div>

          <div className="flex items-center gap-3 mb-6">
            <Link size={14} className="text-muted-foreground shrink-0" />
            <input
              type="text"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="GIT_REPOSITORY_URL"
              className="w-full bg-transparent font-mono text-sm text-foreground placeholder:text-muted-foreground outline-none hairline-b pb-2"
            />
          </div>

          <div className="flex items-center gap-3">
            <Shield size={14} className="text-muted-foreground shrink-0" />
            <div>
              <span className="mono-label-sm text-muted-foreground block">SHA256_HASH</span>
              <span className="font-mono text-xs text-foreground/40 mt-1 block break-all">
                {repoHash || (uploadedFile ? "UPLOADED" : "AWAITING_INPUT")}
              </span>
            </div>
          </div>
        </motion.div>

        {/* Configuration Panel */}
        <motion.div
          className="hairline-b p-6"
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          <span className="mono-label-sm text-muted-foreground block mb-6">CONFIGURATION</span>

          <div className="mb-6">
            <span className="mono-label-sm text-foreground/40 block mb-3">TARGET_LANGUAGE</span>
            <div className="flex gap-0">
              <span className="mono-label-sm px-6 py-3 hairline text-primary-foreground bg-primary">
                PYTHON
              </span>
            </div>
          </div>

          <div className="mb-6 flex items-center justify-between">
            <span className="mono-label-sm text-foreground/40">DETERMINISTIC_MODE</span>
            <span className="mono-label-sm text-primary">
              {deterministicMode ? "ENABLED" : "DISABLED"}
            </span>
          </div>

          <div className="mb-6 flex items-center justify-between">
            <span className="mono-label-sm text-foreground/40">STRICT_VALIDATION</span>
            <button
              onClick={() => setStrictValidation(!strictValidation)}
              className={`mono-label-sm px-4 py-1.5 hairline transition-colors duration-300 ${
                strictValidation ? "text-primary border-primary" : "text-muted-foreground"
              }`}
              style={strictValidation ? { borderColor: "hsl(239 84% 67%)" } : {}}
            >
              {strictValidation ? "ON" : "OFF"}
            </button>
          </div>

          <div className="mb-6 flex items-center justify-between">
            <span className="mono-label-sm text-foreground/40">CONTEXT_WINDOW_LIMIT</span>
            <span className="font-mono text-sm text-foreground/60">
              {contextWindowLimit.toLocaleString()}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="mono-label-sm text-foreground/40">MODE</span>
            <span className={`mono-label-sm ${useBackend ? "text-primary" : "text-foreground/40"}`}>
              {useBackend ? "LIVE_BACKEND" : "DEMO_SIMULATION"}
            </span>
          </div>
        </motion.div>
      </div>

      {/* Execution Control + Constraints */}
      <div className="grid grid-cols-1 md:grid-cols-2">
        <motion.div
          className="hairline-r hairline-b p-6 flex items-center"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
        >
          <button
            onClick={handleStart}
            disabled={!isValid || submitting || uploading}
            className={`mono-label w-full py-4 text-xs tracking-[0.3em] transition-colors duration-300 ${
              isValid && !submitting && !uploading
                ? "bg-primary text-primary-foreground hover:bg-primary/90"
                : "bg-muted text-muted-foreground cursor-not-allowed"
            }`}
          >
            {uploading ? "UPLOADING..." : submitting ? "CONNECTING..." : "START_PIPELINE"}
          </button>
        </motion.div>

        <SystemConstraints />
      </div>
    </div>
  );
};

export default IntakeView;
