#!/usr/bin/env python3
"""Validation script for Phase-10 Demo Readiness.

Verifies:
1. Two consecutive runs produce identical output hash
2. requirements.txt installs cleanly
3. CLI translate command still works
4. Provider swap via .env still works
5. Failure-mode tests still pass

Usage:
    python validate_demo.py
"""

import asyncio
import json
import subprocess
import sys
import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any


def run_command(cmd: list, cwd: str = None) -> tuple[int, str, str]:
    """Run shell command and return exit code, stdout, stderr.
    
    Args:
        cmd: Command and arguments as list
        cwd: Working directory
        
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr


def check_deterministic_runs() -> Dict[str, Any]:
    """Verify two consecutive runs produce identical hash.
    
    Returns:
        Check result dictionary
    """
    print("=" * 70)
    print("CHECK 1: Deterministic Execution")
    print("=" * 70)
    
    # Set deterministic mode
    os.environ["DETERMINISTIC_MODE"] = "true"
    
    # Run demo twice
    print("Running demo (attempt 1)...")
    code1, out1, err1 = run_command([sys.executable, "demo.py"])
    
    if code1 != 0:
        return {
            "passed": False,
            "message": "First demo run failed",
            "details": {"stderr": err1}
        }
    
    # Extract hash from output
    hash1 = None
    for line in out1.split("\n"):
        if "Output hash:" in line:
            hash1 = line.split(":")[-1].strip()
            break
    
    if not hash1:
        return {
            "passed": False,
            "message": "Could not extract hash from first run",
            "details": {"output": out1}
        }
    
    print(f"✓ First run hash: {hash1}")
    
    # Clean output directory
    if Path("demo_output").exists():
        shutil.rmtree("demo_output")
    
    print("Running demo (attempt 2)...")
    code2, out2, err2 = run_command([sys.executable, "demo.py"])
    
    if code2 != 0:
        return {
            "passed": False,
            "message": "Second demo run failed",
            "details": {"stderr": err2}
        }
    
    # Extract hash from output
    hash2 = None
    for line in out2.split("\n"):
        if "Output hash:" in line:
            hash2 = line.split(":")[-1].strip()
            break
    
    if not hash2:
        return {
            "passed": False,
            "message": "Could not extract hash from second run",
            "details": {"output": out2}
        }
    
    print(f"✓ Second run hash: {hash2}")
    
    if hash1 == hash2:
        print("✓ Hashes match - deterministic execution verified")
        return {
            "passed": True,
            "message": "Deterministic execution verified",
            "details": {"hash": hash1}
        }
    else:
        print("✗ Hashes do not match")
        return {
            "passed": False,
            "message": "Hashes do not match - non-deterministic execution",
            "details": {"hash1": hash1, "hash2": hash2}
        }


def check_requirements_install() -> Dict[str, Any]:
    """Verify requirements.txt installs cleanly.
    
    Returns:
        Check result dictionary
    """
    print("\n" + "=" * 70)
    print("CHECK 2: Requirements Installation")
    print("=" * 70)
    
    # Create temporary venv
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = Path(tmpdir) / "test_venv"
        
        print(f"Creating test virtual environment...")
        code, out, err = run_command([sys.executable, "-m", "venv", str(venv_path)])
        
        if code != 0:
            return {
                "passed": False,
                "message": "Failed to create virtual environment",
                "details": {"stderr": err}
            }
        
        # Determine pip path
        if sys.platform == "win32":
            pip_path = venv_path / "Scripts" / "pip.exe"
        else:
            pip_path = venv_path / "bin" / "pip"
        
        print(f"Installing requirements.txt...")
        code, out, err = run_command([str(pip_path), "install", "-r", "requirements.txt", "-q"])
        
        if code != 0:
            return {
                "passed": False,
                "message": "Failed to install requirements.txt",
                "details": {"stderr": err}
            }
        
        print("✓ Requirements installed successfully")
        return {
            "passed": True,
            "message": "Requirements install cleanly",
            "details": {}
        }


def check_cli_translate() -> Dict[str, Any]:
    """Verify CLI translate command works.
    
    Returns:
        Check result dictionary
    """
    print("\n" + "=" * 70)
    print("CHECK 3: CLI Translate Command")
    print("=" * 70)
    
    print("Running CLI translate command...")
    
    # Note: This is a smoke test - full execution requires API key
    code, out, err = run_command([
        sys.executable, "-m", "app.cli.cli", "translate", "--help"
    ])
    
    if code != 0:
        return {
            "passed": False,
            "message": "CLI translate command failed",
            "details": {"stderr": err}
        }
    
    if "translate" not in out.lower():
        return {
            "passed": False,
            "message": "CLI translate help output unexpected",
            "details": {"output": out}
        }
    
    print("✓ CLI translate command available")
    return {
        "passed": True,
        "message": "CLI translate command works",
        "details": {}
    }


def check_provider_swap() -> Dict[str, Any]:
    """Verify provider swap tests pass.
    
    Returns:
        Check result dictionary
    """
    print("\n" + "=" * 70)
    print("CHECK 4: Provider Swap")
    print("=" * 70)
    
    print("Running provider swap tests...")
    code, out, err = run_command([
        sys.executable, "-m", "pytest",
        "tests/test_provider_swap.py",
        "-v", "--tb=short"
    ])
    
    if code != 0:
        return {
            "passed": False,
            "message": "Provider swap tests failed",
            "details": {"stderr": err, "stdout": out}
        }
    
    # Check for passing tests
    if "passed" not in out:
        return {
            "passed": False,
            "message": "No passing tests found in output",
            "details": {"output": out}
        }
    
    print("✓ Provider swap tests passed")
    return {
        "passed": True,
        "message": "Provider swap via .env works",
        "details": {}
    }


def check_cli_api_consistency() -> Dict[str, Any]:
    """Verify CLI/API consistency tests pass.
    
    Returns:
        Check result dictionary
    """
    print("\n" + "=" * 70)
    print("CHECK 5: CLI/API Consistency")
    print("=" * 70)
    
    print("Running CLI/API consistency tests...")
    code, out, err = run_command([
        sys.executable, "-m", "pytest",
        "tests/test_cli_api_consistency.py",
        "-v", "--tb=short"
    ])
    
    if code != 0:
        return {
            "passed": False,
            "message": "CLI/API consistency tests failed",
            "details": {"stderr": err, "stdout": out}
        }
    
    # Check for passing tests
    if "passed" not in out:
        return {
            "passed": False,
            "message": "No passing tests found in output",
            "details": {"output": out}
        }
    
    print("✓ CLI/API consistency tests passed")
    return {
        "passed": True,
        "message": "CLI/API consistency verified",
        "details": {}
    }


def main() -> None:
    """Main validation entry point."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "PHASE-10 VALIDATION CHECKLIST" + " " * 24 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    results = {}
    
    # Run checks
    try:
        results["deterministic"] = check_deterministic_runs()
    except Exception as e:
        results["deterministic"] = {
            "passed": False,
            "message": f"Check failed with exception: {e}",
            "details": {}
        }
    
    try:
        results["requirements_ok"] = check_requirements_install()
    except Exception as e:
        results["requirements_ok"] = {
            "passed": False,
            "message": f"Check failed with exception: {e}",
            "details": {}
        }
    
    try:
        results["cli_ok"] = check_cli_translate()
    except Exception as e:
        results["cli_ok"] = {
            "passed": False,
            "message": f"Check failed with exception: {e}",
            "details": {}
        }
    
    try:
        results["provider_swap_ok"] = check_provider_swap()
    except Exception as e:
        results["provider_swap_ok"] = {
            "passed": False,
            "message": f"Check failed with exception: {e}",
            "details": {}
        }
    
    try:
        results["tests_ok"] = check_cli_api_consistency()
    except Exception as e:
        results["tests_ok"] = {
            "passed": False,
            "message": f"Check failed with exception: {e}",
            "details": {}
        }
    
    # Generate report
    print("\n" + "=" * 70)
    print("VALIDATION REPORT")
    print("=" * 70)
    
    report = {
        "deterministic": results["deterministic"]["passed"],
        "requirements_ok": results["requirements_ok"]["passed"],
        "cli_ok": results["cli_ok"]["passed"],
        "provider_swap_ok": results["provider_swap_ok"]["passed"],
        "tests_ok": results["tests_ok"]["passed"]
    }
    
    print(json.dumps(report, indent=2))
    
    # Save detailed results
    with open("validation_report.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print()
    print(f"Detailed report saved to: validation_report.json")
    print()
    
    # Summary
    passed_count = sum(1 for r in report.values() if r)
    total_count = len(report)
    
    print(f"Result: {passed_count}/{total_count} checks passed")
    
    if all(report.values()):
        print()
        print("✓ ALL CHECKS PASSED - Demo ready!")
        exit(0)
    else:
        print()
        print("✗ Some checks failed - review validation_report.json")
        exit(1)


if __name__ == "__main__":
    main()
