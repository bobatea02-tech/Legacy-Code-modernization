"""Tests for CacheService."""

import pytest
import tempfile
from pathlib import Path

from app.core.cache_service import CacheService


@pytest.fixture
def temp_cache_dir():
    """Create temporary cache directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_cache_service_initialization():
    """Test cache service initialization."""
    cache = CacheService(enabled=True)
    assert cache.enabled is True
    assert cache._memory_cache == {}


def test_cache_service_disabled():
    """Test cache service when disabled."""
    cache = CacheService(enabled=False)
    
    cache.set("key1", {"data": "value"})
    result = cache.get("key1")
    
    assert result is None


def test_cache_get_set_memory():
    """Test memory cache get/set."""
    cache = CacheService(enabled=True)
    
    data = {"text": "response", "token_count": 100}
    cache.set("key1", data)
    
    result = cache.get("key1")
    assert result == data


def test_cache_get_cache_key():
    """Test cache key generation."""
    cache = CacheService()
    
    key1 = cache.get_cache_key("system", "user", "model")
    key2 = cache.get_cache_key("system", "user", "model")
    key3 = cache.get_cache_key("system", "different", "model")
    
    assert key1 == key2
    assert key1 != key3


def test_cache_file_persistence(temp_cache_dir):
    """Test file-based cache persistence."""
    cache = CacheService(cache_dir=temp_cache_dir, enabled=True)
    
    data = {"text": "response", "token_count": 100}
    cache.set("key1", data)
    
    # Create new cache instance with same directory
    cache2 = CacheService(cache_dir=temp_cache_dir, enabled=True)
    result = cache2.get("key1")
    
    assert result == data


def test_cache_clear(temp_cache_dir):
    """Test cache clearing."""
    cache = CacheService(cache_dir=temp_cache_dir, enabled=True)
    
    cache.set("key1", {"data": "value1"})
    cache.set("key2", {"data": "value2"})
    
    cache.clear()
    
    assert cache.get("key1") is None
    assert cache.get("key2") is None
