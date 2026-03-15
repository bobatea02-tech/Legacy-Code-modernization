#!/usr/bin/env python3
"""
Connectivity Test Script
Tests frontend-backend connectivity for the Legacy Code Modernization Engine
"""

import requests
import sys
import time

# Configuration
BACKEND_URL = "http://localhost:8000"
API_BASE_URL = "http://localhost:8000/api"

def test_backend_root():
    """Test backend root endpoint"""
    print("Testing backend root endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=5)
        if response.status_code == 200:
            print(f"✓ Root endpoint accessible: {response.json()}")
            return True
        else:
            print(f"✗ Root endpoint returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Failed to connect to root endpoint: {e}")
        return False

def test_health_endpoint():
    """Test health endpoint"""
    print("\nTesting health endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✓ Health endpoint accessible: {response.json()}")
            return True
        else:
            print(f"✗ Health endpoint returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Failed to connect to health endpoint: {e}")
        return False

def test_api_health_endpoint():
    """Test API health endpoint"""
    print("\nTesting API health endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✓ API health endpoint accessible: {response.json()}")
            return True
        else:
            print(f"✗ API health endpoint returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Failed to connect to API health endpoint: {e}")
        return False

def test_api_docs():
    """Test API documentation endpoint"""
    print("\nTesting API documentation...")
    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print(f"✓ API docs accessible at {API_BASE_URL}/docs")
            return True
        else:
            print(f"✗ API docs returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Failed to connect to API docs: {e}")
        return False

def test_cors():
    """Test CORS configuration"""
    print("\nTesting CORS configuration...")
    try:
        headers = {
            'Origin': 'http://localhost:5173',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        response = requests.options(f"{API_BASE_URL}/health", headers=headers, timeout=5)
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
        }
        
        if cors_headers['Access-Control-Allow-Origin']:
            print(f"✓ CORS configured: {cors_headers}")
            return True
        else:
            print(f"✗ CORS not properly configured")
            return False
    except Exception as e:
        print(f"✗ Failed to test CORS: {e}")
        return False

def main():
    """Run all connectivity tests"""
    print("=" * 60)
    print("LEGACY CODE MODERNIZATION ENGINE - CONNECTIVITY TEST")
    print("=" * 60)
    
    print(f"\nBackend URL: {BACKEND_URL}")
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Frontend URL: http://localhost:5173")
    
    print("\n" + "=" * 60)
    print("RUNNING TESTS")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Backend Root", test_backend_root()))
    results.append(("Health Endpoint", test_health_endpoint()))
    results.append(("API Health Endpoint", test_api_health_endpoint()))
    results.append(("API Documentation", test_api_docs()))
    results.append(("CORS Configuration", test_cors()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All connectivity tests passed!")
        print("\nNext steps:")
        print("1. Start the frontend: cd frontend && npm run dev")
        print("2. Open http://localhost:5173 in your browser")
        print("3. The frontend should now connect to the backend successfully")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the backend server.")
        print("\nTroubleshooting:")
        print("1. Ensure the backend is running: cd backend && python main.py")
        print("2. Check that port 8000 is not blocked by firewall")
        print("3. Verify .env file has correct LLM_API_KEY")
        return 1

if __name__ == "__main__":
    sys.exit(main())
