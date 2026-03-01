"""Tests for PromptBundle schema."""

import pytest

from app.prompt_versioning.schema import PromptBundle


def test_prompt_bundle_creation():
    """Test PromptBundle creation."""
    bundle = PromptBundle(
        system_prompt="You are a helpful assistant",
        user_prompt="Translate this code",
        version="1.0.0",
        metadata={"author": "test"}
    )
    
    assert bundle.system_prompt == "You are a helpful assistant"
    assert bundle.user_prompt == "Translate this code"
    assert bundle.version == "1.0.0"
    assert bundle.metadata == {"author": "test"}


def test_prompt_bundle_to_dict():
    """Test PromptBundle to_dict conversion."""
    bundle = PromptBundle(
        system_prompt="system",
        user_prompt="user",
        version="1.0.0",
        metadata={}
    )
    
    result = bundle.to_dict()
    
    assert result == {
        "system_prompt": "system",
        "user_prompt": "user",
        "version": "1.0.0",
        "metadata": {}
    }


def test_prompt_bundle_empty_metadata():
    """Test PromptBundle with empty metadata."""
    bundle = PromptBundle(
        system_prompt="system",
        user_prompt="user",
        version="1.0.0",
        metadata={}
    )
    
    assert bundle.metadata == {}
