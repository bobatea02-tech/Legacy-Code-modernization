"""Translation orchestrator for dependency-aware code translation."""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import hashlib
import json
import re
import networkx as nx

from app.llm.llm_service import LLMService
from app.parsers.base import ASTNode
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class TranslationStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    PENDING = "pending"


@dataclass
class TranslationResult:
    module_name: str
    status: TranslationStatus
    translated_code: str = ""
    source_file: str = ""          # original source file absolute path
    output_filename: str = ""      # derived output .py filename (stem only)
    dependencies_used: List[str] = field(default_factory=list)
    token_usage: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    source_hash: Optional[str] = None


class TranslationStore:
    """In-memory cache for translated code."""

    def __init__(self):
        self._cache: Dict[str, TranslationResult] = {}
        self._hash_index: Dict[str, str] = {}

    def get_by_hash(self, source_hash: str) -> Optional[TranslationResult]:
        module_name = self._hash_index.get(source_hash)
        return self._cache.get(module_name) if module_name else None

    def store(self, result: TranslationResult) -> None:
        self._cache[result.module_name] = result
        if result.source_hash:
            self._hash_index[result.source_hash] = result.module_name


class TranslationOrchestrator:
    """Orchestrates translation of every AST node to Python."""

    def __init__(
        self,
        llm_service: LLMService,
        context_optimizer=None,
        translation_store: Optional[TranslationStore] = None,
        prompt_manager=None,
    ):
        self.llm_service = llm_service
        self.translation_store = translation_store or TranslationStore()
        self.settings = get_settings()
        self._prompt_version = "1.0.0"
        logger.info("TranslationOrchestrator initialized")

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def translate_repository(
        self,
        dependency_graph: nx.DiGraph,
        ast_index: Dict[str, ASTNode],
        target_language: str = "python",
    ) -> List[TranslationResult]:
        """Translate every node in ast_index to target_language."""

        logger.info(
            f"Starting repository translation: {len(ast_index)} nodes -> {target_language}",
            extra={"stage_name": "translation_orchestration"},
        )

        sorted_nodes = self._safe_sort(dependency_graph, ast_index)

        results: List[TranslationResult] = []
        for node_id in sorted_nodes:
            node = ast_index.get(node_id)
            if node is None:
                continue
            result = await self._translate_node(node, dependency_graph, ast_index, target_language)
            results.append(result)

        success = sum(1 for r in results if r.status == TranslationStatus.SUCCESS)
        failed  = sum(1 for r in results if r.status == TranslationStatus.FAILED)
        skipped = sum(1 for r in results if r.status == TranslationStatus.SKIPPED)
        logger.info(
            f"Translation complete: {success} success, {failed} failed, {skipped} skipped",
            extra={"stage_name": "translation_orchestration"},
        )
        return results

    # ------------------------------------------------------------------
    # Ordering
    # ------------------------------------------------------------------

    def _safe_sort(
        self,
        dependency_graph: nx.DiGraph,
        ast_index: Dict[str, ASTNode],
    ) -> List[str]:
        work = dependency_graph.copy()

        if not nx.is_directed_acyclic_graph(work):
            for cycle in nx.simple_cycles(work):
                if work.has_edge(cycle[-1], cycle[0]):
                    work.remove_edge(cycle[-1], cycle[0])

        try:
            ordered = list(nx.topological_sort(work))
        except Exception:
            ordered = list(work.nodes())

        seen = set(ordered)
        for nid in ast_index:
            if nid not in seen:
                ordered.append(nid)

        return ordered

    # ------------------------------------------------------------------
    # Single-node translation
    # ------------------------------------------------------------------

    async def _translate_node(
        self,
        node: ASTNode,
        dependency_graph: nx.DiGraph,
        ast_index: Dict[str, ASTNode],
        target_language: str,
    ) -> TranslationResult:
        node_id = node.id
        logger.info(f"Translating: {node.name} ({node_id})", extra={"stage_name": "translation_orchestration"})

        # Derive a clean output filename from the source file
        output_filename = self._derive_output_filename(node)

        # Cache check
        source_hash = hashlib.sha256(node.raw_source.encode()).hexdigest()
        if self.settings.CACHE_ENABLED:
            cached = self.translation_store.get_by_hash(source_hash)
            if cached:
                logger.info(f"Cache hit: {node.name}")
                return TranslationResult(
                    module_name=node_id,
                    status=TranslationStatus.SKIPPED,
                    translated_code=cached.translated_code,
                    source_file=node.file_path,
                    output_filename=output_filename,
                    source_hash=source_hash,
                )

        source_context = self._build_source_context(node, dependency_graph, ast_index)
        system_prompt, user_prompt = self._build_prompts(
            source_code=source_context,
            node_name=node.name,
            node_type=node.node_type,
            target_language=target_language,
        )

        try:
            response = self.llm_service.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=self.settings.MAX_TOKEN_LIMIT,
                temperature=0.2,
                force_json=False,
            )
        except Exception as e:
            from app.llm.exceptions import QuotaExhaustedError
            if isinstance(e, QuotaExhaustedError):
                logger.error(f"Quota exhausted during translation of {node.name}: {e}")
                raise
            logger.error(f"LLM call failed for {node.name}: {e}")
            return TranslationResult(
                module_name=node_id,
                status=TranslationStatus.FAILED,
                source_file=node.file_path,
                output_filename=output_filename,
                errors=[f"LLM error: {e}"],
            )

        translated_code, deps, notes, parse_error = self._parse_response(response.text, node_id)

        if parse_error and not translated_code:
            return TranslationResult(
                module_name=node_id,
                status=TranslationStatus.FAILED,
                source_file=node.file_path,
                output_filename=output_filename,
                errors=[parse_error],
            )

        token_usage = response.token_count or (
            len((system_prompt + user_prompt + translated_code).split()) * 4 // 3
        )

        result = TranslationResult(
            module_name=node_id,
            status=TranslationStatus.SUCCESS,
            translated_code=translated_code,
            source_file=node.file_path,
            output_filename=output_filename,
            dependencies_used=deps,
            token_usage=token_usage,
            warnings=[notes] if notes else [],
            source_hash=source_hash,
        )

        if self.settings.CACHE_ENABLED:
            self.translation_store.store(result)

        return result

    # ------------------------------------------------------------------
    # Filename derivation
    # ------------------------------------------------------------------

    def _derive_output_filename(self, node: ASTNode) -> str:
        """Derive a clean Python module filename from the source file path.

        Rules:
        - Use the original source filename stem (e.g. MYPROG.cbl -> MYPROG)
        - Lowercase it
        - Replace non-alphanumeric chars with underscores
        - Ensure it starts with a letter (prefix 'mod_' if not)
        """
        src = node.file_path or node.module_name if hasattr(node, "module_name") else ""
        stem = Path(src).stem if src else node.name
        # Lowercase and sanitize
        clean = re.sub(r'[^\w]', '_', stem.lower()).strip('_')
        if not clean:
            clean = re.sub(r'[^\w]', '_', node.name.lower()).strip('_') or "module"
        # Must start with a letter
        if clean[0].isdigit():
            clean = "mod_" + clean
        return clean

    # ------------------------------------------------------------------
    # Context building
    # ------------------------------------------------------------------

    def _build_source_context(
        self,
        node: ASTNode,
        dependency_graph: nx.DiGraph,
        ast_index: Dict[str, ASTNode],
    ) -> str:
        MAX_CHARS = self.settings.MAX_TOKEN_LIMIT * 3

        parts = [f"--- FILE: {node.file_path} ---\n{node.raw_source}"]
        used = len(parts[0])

        if node.id in dependency_graph:
            for dep_id in dependency_graph.successors(node.id):
                dep_node = ast_index.get(dep_id)
                if dep_node is None:
                    continue
                chunk = f"\n--- DEPENDENCY: {dep_node.file_path} ---\n{dep_node.raw_source}"
                if used + len(chunk) > MAX_CHARS:
                    break
                parts.append(chunk)
                used += len(chunk)

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Prompt building
    # ------------------------------------------------------------------

    def _build_prompts(
        self,
        source_code: str,
        node_name: str,
        node_type: str,
        target_language: str,
    ) -> Tuple[str, str]:
        try:
            backend_dir = Path(__file__).parent.parent.parent
            prompt_file = backend_dir.parent / "prompts" / "code_translation.txt"
            content = prompt_file.read_text(encoding="utf-8")

            if "SYSTEM:" in content and "USER:" in content:
                parts = content.split("USER:", 1)
                system_part = parts[0].replace("SYSTEM:", "").strip()
                user_part = parts[1].strip()
            else:
                system_part = content.strip()
                user_part = (
                    "Translate the following {node_type} named '{node_name}' to {target_language}.\n\n"
                    "Source code:\n```\n{source_code}\n```\n\nReturn the JSON object now."
                )
        except Exception as e:
            logger.warning(f"Could not load prompt file: {e}, using fallback")
            system_part = (
                "You are a code translation assistant. Translate the provided legacy code to modern Python. "
                "Return ONLY valid JSON with keys: translated_code, dependencies, notes."
            )
            user_part = (
                "Translate the following {node_type} named '{node_name}' to {target_language}.\n\n"
                "Source code:\n```\n{source_code}\n```\n\nReturn the JSON object now."
            )

        formatted_user = user_part.format(
            node_type=node_type,
            node_name=node_name,
            target_language=target_language,
            source_code=source_code,
        )
        return system_part, formatted_user

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def _parse_response(
        self, raw: str, node_id: str
    ) -> Tuple[str, List[str], str, Optional[str]]:
        """Extract translated_code, dependencies, notes from LLM response.

        Returns (translated_code, deps, notes, error_msg).
        error_msg is None on success.
        """
        if not raw or not raw.strip():
            return "", [], "", "Empty LLM response"

        text = raw.strip()

        # Strip markdown fences (handle both opening and closing)
        text = re.sub(r'^```[a-zA-Z]*\s*', '', text)
        text = re.sub(r'\s*```\s*$', '', text)
        text = text.strip()

        # --- Attempt 1: find outermost JSON object ---
        start = text.find("{")
        if start != -1:
            depth = 0
            end = -1
            for i in range(start, len(text)):
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            if end != -1:
                json_str = text[start:end]
                try:
                    parsed = json.loads(json_str)
                    code = parsed.get("translated_code", "")
                    deps = parsed.get("dependencies", [])
                    notes = parsed.get("notes", "")
                    if isinstance(deps, list):
                        deps = [str(d) for d in deps]
                    else:
                        deps = []
                    if code:
                        return code, deps, str(notes), None
                except json.JSONDecodeError:
                    pass

        # --- Attempt 2: regex extract translated_code value ---
        m = re.search(r'"translated_code"\s*:\s*"((?:[^"\\]|\\.)*)"', text, re.DOTALL)
        if m:
            code = m.group(1)
            code = code.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"').replace("\\\\", "\\")
            if code.strip():
                logger.warning(f"Used regex fallback to extract translated_code for {node_id}")
                return code, [], "Extracted via regex fallback", None

        # --- Attempt 3: treat entire response as raw Python ---
        if any(kw in text for kw in ("def ", "class ", "import ", "print(", "#")):
            logger.warning(f"LLM returned raw Python (no JSON) for {node_id}, using as-is")
            return text, [], "LLM returned raw Python without JSON wrapper", None

        logger.error(f"Could not extract translated_code for {node_id}. Raw: {raw[:300]}")
        return "", [], "", f"Could not parse LLM response: {raw[:200]}"

    # ------------------------------------------------------------------
    # Compat methods
    # ------------------------------------------------------------------

    def get_prompt_version(self, prompt_name: str) -> str:
        return self._prompt_version

    def get_translation_statistics(self, results: List[TranslationResult]) -> dict:
        total = len(results)
        success = sum(1 for r in results if r.status == TranslationStatus.SUCCESS)
        failed  = sum(1 for r in results if r.status == TranslationStatus.FAILED)
        skipped = sum(1 for r in results if r.status == TranslationStatus.SKIPPED)
        tokens  = sum(r.token_usage for r in results)
        return {
            "total_modules": total,
            "successful": success,
            "failed": failed,
            "skipped": skipped,
            "success_rate": (success / total * 100) if total else 0.0,
            "total_tokens": tokens,
        }
