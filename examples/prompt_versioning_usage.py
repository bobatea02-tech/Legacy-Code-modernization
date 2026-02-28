"""Example usage of the Prompt Versioning System.

This demonstrates how to use the PromptVersionManager to manage
LLM prompt templates with version control.
"""

from app.prompt_versioning import (
    PromptVersionManager,
    PromptNotFoundError,
    DuplicateVersionError
)


def example_basic_usage():
    """Example: Basic prompt registration and retrieval."""
    print("=" * 60)
    print("Example 1: Basic Usage")
    print("=" * 60)
    
    # Create manager
    manager = PromptVersionManager()
    
    # Register a prompt template
    prompt_content = """Translate the following {source_language} code to {target_language}:

{code}

Provide only the translated code without explanations."""
    
    prompt = manager.register_prompt(
        name="code_translation",
        version="1.0.0",
        content=prompt_content,
        metadata={
            "author": "AI Team",
            "purpose": "Code translation",
            "model": "gemini-pro"
        }
    )
    
    print(f"\nRegistered: {prompt.name} v{prompt.version}")
    print(f"Checksum: {prompt.checksum[:16]}...")
    print(f"Created: {prompt.created_at}")
    
    # Retrieve the prompt
    retrieved = manager.get_prompt("code_translation", "1.0.0")
    print(f"\nRetrieved: {retrieved.name} v{retrieved.version}")
    print(f"Content preview: {retrieved.content[:50]}...")


def example_version_evolution():
    """Example: Evolving prompts through versions."""
    print("\n" + "=" * 60)
    print("Example 2: Version Evolution")
    print("=" * 60)
    
    manager = PromptVersionManager()
    
    # Version 1.0.0 - Basic translation
    v1_content = "Translate {code} from {source} to {target}."
    manager.register_prompt("translation", "1.0.0", v1_content)
    print("\nRegistered v1.0.0 - Basic translation")
    
    # Version 1.1.0 - Added context
    v1_1_content = """Translate {code} from {source} to {target}.
Consider the following context: {context}"""
    manager.register_prompt("translation", "1.1.0", v1_1_content)
    print("Registered v1.1.0 - Added context support")
    
    # Version 2.0.0 - Complete rewrite
    v2_content = """You are an expert code translator.

Source Language: {source}
Target Language: {target}
Context: {context}

Code to translate:
{code}

Provide idiomatic translation with proper error handling."""
    manager.register_prompt("translation", "2.0.0", v2_content)
    print("Registered v2.0.0 - Complete rewrite")
    
    # List all versions
    versions = manager.list_versions("translation")
    print(f"\nAll versions: {versions}")
    
    # Get latest
    latest = manager.get_latest("translation")
    print(f"Latest version: {latest.version}")


def example_rollback():
    """Example: Rolling back to previous version."""
    print("\n" + "=" * 60)
    print("Example 3: Rollback")
    print("=" * 60)
    
    manager = PromptVersionManager()
    
    # Register multiple versions
    manager.register_prompt("api_docs", "1.0.0", "Version 1 content")
    manager.register_prompt("api_docs", "2.0.0", "Version 2 content")
    manager.register_prompt("api_docs", "3.0.0", "Version 3 content (buggy)")
    
    print("\nRegistered versions: 1.0.0, 2.0.0, 3.0.0")
    
    # Latest is 3.0.0
    latest = manager.get_latest("api_docs")
    print(f"Current latest: {latest.version}")
    
    # Rollback to 2.0.0
    manager.set_active_version("api_docs", "2.0.0")
    print("\nRolled back to v2.0.0")
    
    # Now latest is 2.0.0
    latest = manager.get_latest("api_docs")
    print(f"New latest: {latest.version}")
    print(f"Content: {latest.content}")


def example_checksum_validation():
    """Example: Checksum validation for integrity."""
    print("\n" + "=" * 60)
    print("Example 4: Checksum Validation")
    print("=" * 60)
    
    manager = PromptVersionManager()
    
    # Register prompt
    content = "Original prompt content"
    prompt = manager.register_prompt("secure_prompt", "1.0.0", content)
    
    print(f"\nOriginal checksum: {prompt.checksum[:16]}...")
    print(f"Validation: {prompt.validate_checksum()}")
    
    # Simulate corruption
    prompt.content = "Corrupted content"
    print(f"\nAfter corruption:")
    print(f"Validation: {prompt.validate_checksum()}")


def example_metadata_tracking():
    """Example: Using metadata for tracking."""
    print("\n" + "=" * 60)
    print("Example 5: Metadata Tracking")
    print("=" * 60)
    
    manager = PromptVersionManager()
    
    # Register with rich metadata
    metadata = {
        "author": "John Doe",
        "team": "AI Engineering",
        "purpose": "Code translation for Java to Python",
        "model": "gemini-pro",
        "temperature": 0.7,
        "max_tokens": 2048,
        "tags": ["translation", "java", "python"],
        "jira_ticket": "AI-123"
    }
    
    prompt = manager.register_prompt(
        name="java_to_python",
        version="1.0.0",
        content="Translate Java code to Python...",
        metadata=metadata
    )
    
    print(f"\nPrompt: {prompt.name} v{prompt.version}")
    print(f"Author: {prompt.metadata['author']}")
    print(f"Team: {prompt.metadata['team']}")
    print(f"Model: {prompt.metadata['model']}")
    print(f"Tags: {', '.join(prompt.metadata['tags'])}")
    print(f"JIRA: {prompt.metadata['jira_ticket']}")


def example_error_handling():
    """Example: Error handling."""
    print("\n" + "=" * 60)
    print("Example 6: Error Handling")
    print("=" * 60)
    
    manager = PromptVersionManager()
    
    # Register a prompt
    manager.register_prompt("test", "1.0.0", "Content")
    
    # Try to register duplicate version
    print("\nAttempting to register duplicate version...")
    try:
        manager.register_prompt("test", "1.0.0", "Different content")
    except DuplicateVersionError as e:
        print(f"✓ Caught DuplicateVersionError: {e}")
    
    # Try to get non-existent prompt
    print("\nAttempting to get non-existent prompt...")
    try:
        manager.get_prompt("nonexistent", "1.0.0")
    except PromptNotFoundError as e:
        print(f"✓ Caught PromptNotFoundError: {e}")


def example_json_serialization():
    """Example: JSON serialization for storage."""
    print("\n" + "=" * 60)
    print("Example 7: JSON Serialization")
    print("=" * 60)
    
    import json
    
    manager = PromptVersionManager()
    
    # Register prompt
    prompt = manager.register_prompt(
        name="serialization_test",
        version="1.0.0",
        content="Test content",
        metadata={"key": "value"}
    )
    
    # Convert to dict
    prompt_dict = prompt.to_dict()
    
    # Serialize to JSON
    json_str = json.dumps(prompt_dict, indent=2)
    
    print("\nJSON representation:")
    print(json_str)
    
    # Can be stored in database, sent over API, etc.
    print("\n✓ Prompt is fully JSON-serializable")


def example_pipeline_integration():
    """Example: Integration with pipeline."""
    print("\n" + "=" * 60)
    print("Example 8: Pipeline Integration")
    print("=" * 60)
    
    manager = PromptVersionManager()
    
    # Register prompts for different pipeline stages
    prompts = {
        "code_translation": "Translate {code} from {source} to {target}.",
        "context_optimization": "Optimize context for {node_name}.",
        "validation": "Validate translated code: {code}",
        "documentation": "Generate documentation for: {code}"
    }
    
    for name, content in prompts.items():
        manager.register_prompt(name, "1.0.0", content)
        print(f"✓ Registered: {name}")
    
    # List all prompts
    all_prompts = manager.list_prompts()
    print(f"\nTotal prompts registered: {len(all_prompts)}")
    print(f"Prompts: {', '.join(all_prompts)}")
    
    # Retrieve for use in pipeline
    translation_prompt = manager.get_latest("code_translation")
    print(f"\nUsing prompt: {translation_prompt.name} v{translation_prompt.version}")
    print(f"Content: {translation_prompt.content}")


if __name__ == "__main__":
    example_basic_usage()
    example_version_evolution()
    example_rollback()
    example_checksum_validation()
    example_metadata_tracking()
    example_error_handling()
    example_json_serialization()
    example_pipeline_integration()
    
    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)
