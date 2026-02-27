"""Example usage of Gemini API client."""

from app.llm import GeminiClient, estimate_tokens
from app.llm.exceptions import TokenLimitExceededError, GeminiRequestError


def demonstrate_basic_generation():
    """Demonstrate basic text generation."""
    print("=== Basic Generation ===\n")
    
    try:
        client = GeminiClient()
        
        prompt = "Explain what a compiler is in one sentence."
        
        print(f"Prompt: {prompt}")
        print(f"Estimated tokens: {estimate_tokens(prompt)}\n")
        
        response = client.generate(prompt)
        
        print(f"Response:")
        print(f"  Text: {response.text[:200]}...")
        print(f"  Token estimate: {response.token_estimate}")
        print(f"  Cached: {response.cached}")
        print(f"  Latency: {response.latency_ms}ms")
        print(f"  Request ID: {response.request_id}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n=== Basic Generation Complete ===")


def demonstrate_with_metadata():
    """Demonstrate generation with metadata."""
    print("\n\n=== Generation with Metadata ===\n")
    
    try:
        client = GeminiClient()
        
        prompt = "What is dependency injection?"
        metadata = {
            "module_name": "Calculator",
            "phase_name": "translation",
            "token_hint": 500
        }
        
        print(f"Prompt: {prompt}")
        print(f"Metadata: {metadata}\n")
        
        response = client.generate(prompt, metadata=metadata)
        
        print(f"Response:")
        print(f"  Text: {response.text[:200]}...")
        print(f"  Request ID: {response.request_id}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n=== Metadata Generation Complete ===")


def demonstrate_caching():
    """Demonstrate response caching."""
    print("\n\n=== Response Caching ===\n")
    
    try:
        client = GeminiClient()
        
        prompt = "What is a binary tree?"
        
        # First call - not cached
        print("First call (not cached):")
        response1 = client.generate(prompt)
        print(f"  Cached: {response1.cached}")
        print(f"  Latency: {response1.latency_ms}ms")
        
        # Second call - should be cached
        print("\nSecond call (should be cached):")
        response2 = client.generate(prompt)
        print(f"  Cached: {response2.cached}")
        print(f"  Latency: {response2.latency_ms}ms")
        
        # Verify same response
        print(f"\nSame response: {response1.text == response2.text}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n=== Caching Complete ===")


def demonstrate_token_estimation():
    """Demonstrate token estimation."""
    print("\n\n=== Token Estimation ===\n")
    
    samples = [
        "Hello",
        "Hello world",
        "This is a longer sentence with more words.",
        "def calculate(a, b):\n    return a + b",
        "public class Calculator {\n    public int add(int a, int b) {\n        return a + b;\n    }\n}"
    ]
    
    print("Token estimates:")
    for sample in samples:
        tokens = estimate_tokens(sample)
        print(f"  {len(sample):3d} chars -> {tokens:3d} tokens: {sample[:40]}...")
    
    print("\n=== Token Estimation Complete ===")


def demonstrate_token_limit():
    """Demonstrate token limit enforcement."""
    print("\n\n=== Token Limit Enforcement ===\n")
    
    try:
        client = GeminiClient()
        
        # Create a very long prompt
        long_prompt = "a" * 500000  # 500k characters = ~125k tokens
        
        print(f"Prompt length: {len(long_prompt)} characters")
        print(f"Estimated tokens: {estimate_tokens(long_prompt)}")
        print("\nAttempting to generate...")
        
        response = client.generate(long_prompt)
        print("Success (unexpected)")
        
    except TokenLimitExceededError as e:
        print(f"Token limit exceeded (expected): {e}")
    except Exception as e:
        print(f"Other error: {e}")
    
    print("\n=== Token Limit Test Complete ===")


def demonstrate_error_handling():
    """Demonstrate error handling."""
    print("\n\n=== Error Handling ===\n")
    
    try:
        client = GeminiClient()
        
        # This will work if API key is valid
        response = client.generate("Test prompt")
        print(f"Success: {response.text[:50]}...")
        
    except TokenLimitExceededError as e:
        print(f"Token limit error: {e}")
    except GeminiRequestError as e:
        print(f"API request error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    print("\n=== Error Handling Complete ===")


def demonstrate_response_serialization():
    """Demonstrate response serialization."""
    print("\n\n=== Response Serialization ===\n")
    
    try:
        client = GeminiClient()
        
        response = client.generate("What is Python?")
        
        # Convert to dict
        response_dict = response.to_dict()
        
        print("Response as dictionary:")
        for key, value in response_dict.items():
            if key == "text":
                print(f"  {key}: {str(value)[:50]}...")
            else:
                print(f"  {key}: {value}")
        
        # Can be serialized to JSON
        import json
        json_str = json.dumps(response_dict, indent=2)
        print(f"\nJSON serialization successful: {len(json_str)} characters")
        
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n=== Serialization Complete ===")


def demonstrate_cache_clearing():
    """Demonstrate cache clearing."""
    print("\n\n=== Cache Clearing ===\n")
    
    try:
        client = GeminiClient()
        
        # Generate some responses
        client.generate("Question 1")
        client.generate("Question 2")
        
        print(f"Cache size: {len(client.cache)} entries")
        
        # Clear cache
        client.clear_cache()
        print(f"Cache cleared")
        print(f"Cache size: {len(client.cache)} entries")
        
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n=== Cache Clearing Complete ===")


if __name__ == "__main__":
    print("NOTE: These examples require a valid GEMINI_API_KEY in .env file\n")
    
    demonstrate_basic_generation()
    demonstrate_with_metadata()
    demonstrate_caching()
    demonstrate_token_estimation()
    demonstrate_token_limit()
    demonstrate_error_handling()
    demonstrate_response_serialization()
    demonstrate_cache_clearing()
    
    print("\n\n=== All Demonstrations Complete ===")
