#!/usr/bin/env python3
"""
System Diagnostic Script
Checks all prerequisites and configurations for the Legacy Code Modernization Engine
"""

import sys
import os
from pathlib import Path
import subprocess

def check_python():
    """Check Python version"""
    print("Checking Python installation...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} installed")
        return True
    else:
        print(f"✗ Python 3.8+ required, found {version.major}.{version.minor}.{version.micro}")
        return False

def check_node():
    """Check Node.js installation"""
    print("\nChecking Node.js installation...")
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✓ Node.js {version} installed")
            return True
        else:
            print("✗ Node.js not found")
            return False
    except FileNotFoundError:
        print("✗ Node.js not found")
        return False

def check_npm():
    """Check npm installation"""
    print("\nChecking npm installation...")
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✓ npm {version} installed")
            return True
        else:
            print("✗ npm not found")
            return False
    except FileNotFoundError:
        print("✗ npm not found")
        return False

def check_backend_env():
    """Check backend .env file"""
    print("\nChecking backend configuration...")
    env_path = Path("backend/.env")
    
    if not env_path.exists():
        print("✗ backend/.env file not found")
        return False
    
    print("✓ backend/.env file exists")
    
    # Check for required variables
    with open(env_path, 'r') as f:
        content = f.read()
    
    required_vars = ['LLM_API_KEY', 'LLM_PROVIDER']
    missing = []
    
    for var in required_vars:
        if var not in content:
            missing.append(var)
    
    if missing:
        print(f"✗ Missing required variables: {', '.join(missing)}")
        return False
    
    print("✓ All required environment variables present")
    return True

def check_frontend_env():
    """Check frontend .env file"""
    print("\nChecking frontend configuration...")
    env_path = Path("frontend/.env")
    
    if not env_path.exists():
        print("✗ frontend/.env file not found")
        return False
    
    print("✓ frontend/.env file exists")
    
    # Check for required variables
    with open(env_path, 'r') as f:
        content = f.read()
    
    if 'VITE_API_BASE_URL' not in content:
        print("✗ VITE_API_BASE_URL not found in .env")
        return False
    
    # Check if it has the correct value
    if 'VITE_API_BASE_URL=http://localhost:8000/api' in content:
        print("✓ VITE_API_BASE_URL correctly configured with /api suffix")
        return True
    elif 'VITE_API_BASE_URL=http://localhost:8000' in content and '/api' not in content:
        print("⚠ VITE_API_BASE_URL missing /api suffix")
        print("  Expected: VITE_API_BASE_URL=http://localhost:8000/api")
        return False
    else:
        print("✓ VITE_API_BASE_URL is configured")
        return True

def check_backend_dependencies():
    """Check backend Python dependencies"""
    print("\nChecking backend dependencies...")
    try:
        import fastapi
        import uvicorn
        import pydantic
        print("✓ Core backend dependencies installed (fastapi, uvicorn, pydantic)")
        return True
    except ImportError as e:
        print(f"✗ Missing backend dependencies: {e}")
        print("  Run: cd backend && pip install -r requirements.txt")
        return False

def check_frontend_dependencies():
    """Check frontend node_modules"""
    print("\nChecking frontend dependencies...")
    node_modules = Path("frontend/node_modules")
    
    if not node_modules.exists():
        print("✗ frontend/node_modules not found")
        print("  Run: cd frontend && npm install")
        return False
    
    print("✓ frontend/node_modules exists")
    return True

def check_ports():
    """Check if required ports are available"""
    print("\nChecking port availability...")
    import socket
    
    ports = {
        8000: "Backend (FastAPI)",
        5173: "Frontend (Vite)"
    }
    
    all_available = True
    
    for port, service in ports.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f"⚠ Port {port} ({service}) is already in use")
            all_available = False
        else:
            print(f"✓ Port {port} ({service}) is available")
    
    return all_available

def check_file_structure():
    """Check if required files and directories exist"""
    print("\nChecking file structure...")
    
    required_paths = [
        "backend/main.py",
        "backend/app/api/main.py",
        "backend/app/api/pipeline_routes.py",
        "backend/requirements.txt",
        "frontend/package.json",
        "frontend/src/services/api.ts",
        "frontend/vite.config.ts"
    ]
    
    all_exist = True
    
    for path in required_paths:
        if Path(path).exists():
            print(f"✓ {path}")
        else:
            print(f"✗ {path} not found")
            all_exist = False
    
    return all_exist

def main():
    """Run all diagnostic checks"""
    print("=" * 70)
    print("LEGACY CODE MODERNIZATION ENGINE - SYSTEM DIAGNOSTIC")
    print("=" * 70)
    
    results = []
    
    # Run all checks
    results.append(("Python Installation", check_python()))
    results.append(("Node.js Installation", check_node()))
    results.append(("npm Installation", check_npm()))
    results.append(("File Structure", check_file_structure()))
    results.append(("Backend Configuration", check_backend_env()))
    results.append(("Frontend Configuration", check_frontend_env()))
    results.append(("Backend Dependencies", check_backend_dependencies()))
    results.append(("Frontend Dependencies", check_frontend_dependencies()))
    results.append(("Port Availability", check_ports()))
    
    # Summary
    print("\n" + "=" * 70)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {check_name}")
    
    print(f"\nTotal: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n✓ System is ready!")
        print("\nNext steps:")
        print("1. Start backend: python start_backend.bat (or cd backend && python main.py)")
        print("2. Start frontend: start_frontend.bat (or cd frontend && npm run dev)")
        print("3. Test connectivity: python test_connectivity.py")
        print("4. Open http://localhost:5173 in your browser")
        return 0
    else:
        print("\n✗ System has issues that need to be resolved.")
        print("\nPlease fix the failed checks above before starting the system.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
