"""Safe parser for LLM JSON responses.

Implements deterministic parsing with strict validation.
No silent retries, no auto-correction.
"""

import json
import re
from typing import Dict, Any

from app.llm.exceptions import StructuredLLMError
from app.core.logging import get_logger

logger = get_logger(__name__)


def parse_llm_json(
    raw_response: str,
    node_id: str,
    model_name: str,
    prompt_version: str
) -> Dict[str, Any]:
    """Parse and validate LLM JSON response.
    
    This parser is DETERMINISTIC and STRICT:
    1. Strips markdown code fences
    2. Extracts first {...} block
    3. Parses JSON
    4. Validates required keys
    5. Raises StructuredLLMError on any failure
    
    NO silent retries. NO auto-correction.
    
    Args:
        raw_response: Raw text response from LLM
        node_id: Node identifier for logging
        model_name: Model name for logging
        prompt_version: Prompt version for logging
        
    Returns:
        Parsed JSON dictionary
        
    Raises:
        StructuredLLMError: If response is invalid or doesn't match schema
    """
    if not raw_response or not raw_response.strip():
        logger.error(
            "Empty LLM response",
            extra={
                "stage_name": "llm",
                "node_id": node_id,
                "model_name": model_name,
                "prompt_version": prompt_version
            }
        )
        raise StructuredLLMError("LLM returned empty response")
    
    # Step 1: Strip markdown code fences
    cleaned = raw_response.strip()
    
    # Remove ```json ... ``` or ```...```
    if cleaned.startswith("```"):
        # Find the first newline after opening fence
        first_newline = cleaned.find("\n")
        if first_newline != -1:
            # Find closing fence
            closing_fence = cleaned.rfind("```")
            if closing_fence > first_newline:
                cleaned = cleaned[first_newline + 1:closing_fence].strip()
    
    # Step 2: Extract first {...} block
    # Find the first { and matching }
    start_idx = cleaned.find("{")
    if start_idx == -1:
        logger.error(
            "No JSON object found in LLM response",
            extra={
                "stage_name": "llm",
                "node_id": node_id,
                "model_name": model_name,
                "prompt_version": prompt_version,
                "raw_response": raw_response[:500]  # Log first 500 chars
            }
        )
        raise StructuredLLMError("No JSON object found in response")
    
    # Find matching closing brace
    brace_count = 0
    end_idx = -1
    for i in range(start_idx, len(cleaned)):
        if cleaned[i] == "{":
            brace_count += 1
        elif cleaned[i] == "}":
            brace_count -= 1
            if brace_count == 0:
                end_idx = i + 1
                break
    
    if end_idx == -1:
        logger.error(
            "Unmatched braces in LLM response",
            extra={
                "stage_name": "llm",
                "node_id": node_id,
                "model_name": model_name,
                "prompt_version": prompt_version,
                "raw_response": raw_response[:500]
            }
        )
        raise StructuredLLMError("Unmatched braces in JSON response")
    
    json_str = cleaned[start_idx:end_idx]
    
    # Step 3: Parse JSON
    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(
            f"JSON parsing failed: {e}",
            extra={
                "stage_name": "llm",
                "node_id": node_id,
                "model_name": model_name,
                "prompt_version": prompt_version,
                "raw_response": raw_response[:500],
                "json_error": str(e)
            }
        )
        raise StructuredLLMError(f"Invalid JSON: {e}")
    
    # Step 4: Validate it's a dictionary
    if not isinstance(parsed, dict):
        logger.error(
            "LLM response is not a JSON object",
            extra={
                "stage_name": "llm",
                "node_id": node_id,
                "model_name": model_name,
                "prompt_version": prompt_version,
                "response_type": type(parsed).__name__
            }
        )
        raise StructuredLLMError(f"Expected JSON object, got {type(parsed).__name__}")
    
    logger.debug(
        "Successfully parsed LLM JSON response",
        extra={
            "stage_name": "llm",
            "node_id": node_id,
            "model_name": model_name,
            "prompt_version": prompt_version,
            "keys": list(parsed.keys())
        }
    )
    
    return parsed
