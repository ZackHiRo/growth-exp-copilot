#!/usr/bin/env python3
"""
Offline Test Runner for Growth Experiment Co-Pilot
Runs tests without requiring external APIs or services
"""

import sys
import os
import subprocess
from datetime import datetime

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n🧪 {description}")
    print(f"Command: {cmd}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ SUCCESS")
            if result.stdout:
                print("Output:")
                print(result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
        else:
            print("❌ FAILED")
            if result.stderr:
                print("Error:")
                print(result.stderr[:500] + "..." if len(result.stderr) > 500 else result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def run_python_test(script_path, description):
    """Run a Python test script"""
    if os.path.exists(script_path):
        return run_command(f"python {script_path}", description)
    else:
        print(f"⚠️  Script not found: {script_path}")
        return False

def check_dependencies():
    """Check if basic dependencies are available"""
    print("🔍 Checking Dependencies")
    print("=" * 50)
    
    # Check Python version
    python_version = sys.version_info
    print(f"Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version >= (3, 8):
        print("✅ Python version OK (3.8+)")
    else:
        print("❌ Python version too old (need 3.8+)")
        return False
    
    # Check if we can import basic modules
    try:
        import json
        print("✅ json module available")
    except ImportError:
        print("❌ json module not available")
        return False
    
    try:
        import datetime
        print("✅ datetime module available")
    except ImportError:
        print("❌ datetime module not available")
        return False
    
    return True

def run_schema_tests():
    """Run basic schema validation tests"""
    print("\n📋 Running Schema Tests")
    print("=" * 50)
    
    try:
        # Test basic imports
        sys.path.append('.')
        from schemas.experiment import ExperimentSpec, Metric, TrackingPlan
        
        # Test Metric creation
        metric = Metric(
            name="test_metric",
            type="rate",
            event="test_event"
        )
        assert metric.name == "test_metric"
        print("✅ Metric schema validation passed")
        
        # Test ExperimentSpec creation
        spec_data = {
            "key": "test_experiment",
            "hypothesis": "Test hypothesis",
            "variants": ["control", "treatment"],
            "primary_metric": metric.model_dump(),
            "mde": 0.15,
            "alpha": 0.05,
            "power": 0.8,
            "min_sample_size": 2500,
            "max_duration_days": 14
        }
        
        spec = ExperimentSpec.model_validate(spec_data)
        assert spec.key == "test_experiment"
        print("✅ ExperimentSpec schema validation passed")
        
        # Test TrackingPlan creation
        tracking_plan = TrackingPlan(
            events=[{"name": "test_event", "properties": ["prop1"]}],
            guardrails={"must_have": ["prop1"], "pii_ban": ["email"]},
            experiment_key="test_experiment"
        )
        assert tracking_plan.experiment_key == "test_experiment"
        print("✅ TrackingPlan schema validation passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema tests failed: {e}")
        return False

def run_file_structure_tests():
    """Test that all required files exist"""
    print("\n📁 Running File Structure Tests")
    print("=" * 50)
    
    required_dirs = [
        "agents", "integrations", "memory", "orchestrator",
        "prompts", "schemas", "scripts", "tests", "infra"
    ]
    
    required_files = [
        "app.py", "requirements.txt", "README.md", "start.sh",
        "agents/supervisor.py", "schemas/experiment.py",
        "integrations/posthog.py", "integrations/github.py",
        "integrations/slack.py", "integrations/flags.py"
    ]
    
    all_good = True
    
    # Check directories
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✅ Directory exists: {directory}/")
        else:
            print(f"❌ Directory missing: {directory}/")
            all_good = False
    
    # Check files
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ File exists: {file_path}")
        else:
            print(f"❌ File missing: {file_path}")
            all_good = False
    
    return all_good

def run_mock_tests():
    """Run the mock integration tests"""
    print("\n🤖 Running Mock Integration Tests")
    print("=" * 50)
    
    test_script = "tests/test_mock_integrations.py"
    if os.path.exists(test_script):
        return run_python_test(test_script, "Mock Integration Tests")
    else:
        print(f"⚠️  Mock test script not found: {test_script}")
        return False

def run_offline_demo():
    """Run the offline demo"""
    print("\n🎬 Running Offline Demo")
    print("=" * 50)
    
    demo_script = "demo_offline.py"
    if os.path.exists(demo_script):
        return run_python_test(demo_script, "Offline Demo")
    else:
        print(f"⚠️  Offline demo script not found: {demo_script}")
        return False

def main():
    """Run all offline tests"""
    print("🚀 Growth Experiment Co-Pilot - Offline Test Runner")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Running tests without external dependencies...")
    
    # Track test results
    tests_passed = 0
    tests_total = 0
    
    # Check dependencies
    tests_total += 1
    if check_dependencies():
        tests_passed += 1
    
    # Run schema tests
    tests_total += 1
    if run_schema_tests():
        tests_passed += 1
    
    # Run file structure tests
    tests_total += 1
    if run_file_structure_tests():
        tests_passed += 1
    
    # Run mock tests
    tests_total += 1
    if run_mock_tests():
        tests_passed += 1
    
    # Run offline demo
    tests_total += 1
    if run_offline_demo():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print(f"📊 Test Results: {tests_passed}/{tests_total} tests passed")
    
    if tests_passed == tests_total:
        print("🎉 All tests passed! The system is ready for use.")
        print("\nNext steps:")
        print("1. Set up your .env file with API keys")
        print("2. Start infrastructure: ./start.sh")
        print("3. Test with real APIs: python demo.py")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        print("\nCommon issues:")
        print("- Missing Python dependencies (run: pip install -r requirements.txt)")
        print("- Missing files (check git clone was complete)")
        print("- Python version too old (need 3.8+)")
    
    return tests_passed == tests_total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
