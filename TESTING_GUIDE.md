# Testing Guide: Growth Experiment Co-Pilot

## 🎯 Overview

This guide covers all the ways to test the Growth Experiment Co-Pilot system, from offline testing without any external APIs to full integration testing with real services.

## 🚫 Testing Without External APIs

### **Option 1: Basic Schema Tests** (No Dependencies)
```bash
# Test just the data models and schemas
python -c "
from schemas.experiment import ExperimentSpec, Metric
metric = Metric(name='test', type='rate', event='test_event')
spec = ExperimentSpec(key='test', hypothesis='test', variants=['control'], primary_metric=metric.model_dump())
print('✅ Schema validation working')
"
```

### **Option 2: Offline Demo** (No APIs Required)
```bash
# Run the comprehensive offline demo
python demo_offline.py

# This demonstrates:
# - Schema validation
# - Statistical analysis simulation
# - Agent prompt loading
# - Code generation examples
# - Workflow simulation
# - Project structure overview
```

### **Option 3: Mock Integration Tests** (Comprehensive Testing)
```bash
# Run tests with mocked external services
python tests/test_mock_integrations.py

# This tests:
# - All integration clients (PostHog, GitHub, Slack, Feature Flags)
# - Memory store operations
# - Worker initialization
# - Agent creation
# - Statistical functions
# - Schema validation
```

### **Option 4: Offline Test Runner** (Complete Test Suite)
```bash
# Run all offline tests in sequence
python run_tests_offline.py

# This runs:
# - Dependency checks
# - Schema validation
# - File structure verification
# - Mock integration tests
# - Offline demo
```

## 🧪 Test Categories

### **1. Schema Tests** (Always Work)
- **What**: Tests Pydantic data models and validation
- **Dependencies**: None (built-in Python modules only)
- **Command**: `python -c "from schemas.experiment import ExperimentSpec; print('OK')"`
- **Use Case**: Verify data structure definitions

### **2. Mock Tests** (Recommended for Development)
- **What**: Tests all components with mocked external services
- **Dependencies**: Python standard library + unittest.mock
- **Command**: `python tests/test_mock_integrations.py`
- **Use Case**: Verify component logic without external APIs

### **3. Offline Demos** (Showcase System Capabilities)
- **What**: Demonstrates system features with simulated data
- **Dependencies**: None (pure simulation)
- **Command**: `python demo_offline.py`
- **Use Case**: Understand system capabilities and workflow

### **4. Integration Tests** (Require Real APIs)
- **What**: Tests with actual external services
- **Dependencies**: API keys, external services running
- **Command**: `python tests/test_end_to_end.py`
- **Use Case**: Verify real-world functionality

## 🔧 Setting Up Offline Testing

### **Prerequisites**
```bash
# Check Python version (3.8+ required)
python --version

# Verify you're in the project directory
ls -la
# Should show: app.py, requirements.txt, agents/, integrations/, etc.
```

### **Quick Start (No Installation)**
```bash
# Test basic functionality immediately
python demo_offline.py

# Run comprehensive offline tests
python run_tests_offline.py
```

### **With Dependencies Installed**
```bash
# Install requirements (optional for offline testing)
pip install -r requirements.txt

# Run mock tests (more comprehensive)
python tests/test_mock_integrations.py
```

## 📊 What Each Test Covers

### **Schema Tests**
✅ **ExperimentSpec**: Complete experiment definition  
✅ **Metric**: Metric types and validation  
✅ **TrackingPlan**: Event tracking configuration  
✅ **Data validation**: Pydantic model validation  

### **Mock Integration Tests**
✅ **PostHog Client**: Metrics and tracking simulation  
✅ **GitHub Client**: Repository and PR operations  
✅ **Slack Client**: Messaging and notifications  
✅ **Feature Flags**: Experiment variant management  
✅ **Memory Store**: Chroma database operations  
✅ **Workers**: Background job processing  
✅ **Agents**: AutoGen agent creation  

### **Offline Demo**
✅ **Complete workflow simulation**  
✅ **Statistical analysis examples**  
✅ **Code generation preview**  
✅ **Project structure overview**  
✅ **System capabilities showcase**  

## 🚨 Common Testing Scenarios

### **Scenario 1: "I want to see what the system does"**
```bash
# Run the offline demo
python demo_offline.py
```

### **Scenario 2: "I want to verify the code works"**
```bash
# Run mock tests
python tests/test_mock_integrations.py
```

### **Scenario 3: "I want to check everything is set up correctly"**
```bash
# Run complete offline test suite
python run_tests_offline.py
```

### **Scenario 4: "I want to test with real APIs"**
```bash
# Set up environment first
cp env.example .env
# Edit .env with your API keys

# Start infrastructure
./start.sh

# Run integration tests
python tests/test_end_to_end.py
```

## 🔍 Troubleshooting Offline Tests

### **Import Errors**
```bash
# Make sure you're in the project directory
pwd
# Should show: /path/to/growth-exp-copilot

# Check Python path
python -c "import sys; print(sys.path)"
```

### **File Not Found Errors**
```bash
# Verify project structure
ls -la
# Should show all directories: agents/, integrations/, etc.

# Check specific files
ls -la schemas/experiment.py
ls -la tests/test_mock_integrations.py
```

### **Python Version Issues**
```bash
# Check Python version
python --version
# Should be 3.8 or higher

# If using Python 3, try:
python3 --version
python3 demo_offline.py
```

## 📈 Testing Progression

### **Phase 1: Offline Validation** (No APIs)
```bash
python demo_offline.py                    # Understand system
python run_tests_offline.py              # Verify setup
```

### **Phase 2: Mock Testing** (Simulated APIs)
```bash
python tests/test_mock_integrations.py   # Test components
```

### **Phase 3: Infrastructure Testing** (Local Services)
```bash
./start.sh                               # Start RabbitMQ/Chroma
# Test local infrastructure
```

### **Phase 4: Integration Testing** (Real APIs)
```bash
# Configure API keys in .env
python tests/test_end_to_end.py         # Test with real services
```

## 🎯 Success Indicators

### **Offline Tests**
- ✅ `python demo_offline.py` runs without errors
- ✅ `python run_tests_offline.py` shows all tests passing
- ✅ Schema validation works
- ✅ File structure is complete

### **Mock Tests**
- ✅ All integration clients initialize
- ✅ Statistical functions work
- ✅ Memory operations succeed
- ✅ Agent creation works

### **Integration Tests**
- ✅ External services connect
- ✅ Real API calls succeed
- ✅ End-to-end workflows complete

## 🚀 Next Steps After Testing

### **If All Offline Tests Pass**
1. Set up your `.env` file with API keys
2. Start infrastructure with `./start.sh`
3. Test with real APIs using `python demo.py`

### **If Some Tests Fail**
1. Check the error messages above
2. Verify Python version (3.8+)
3. Ensure all project files are present
4. Check for missing dependencies

### **For Development**
1. Use mock tests during development
2. Run offline tests before commits
3. Use integration tests for final validation

## 📚 Additional Resources

- **README.md**: Project overview and setup
- **INSTALLATION_GUIDE.md**: Step-by-step installation
- **PROJECT_STATUS.md**: Current implementation status
- **Code comments**: Inline documentation throughout

---

**Happy testing! 🧪**

The system is designed to be fully testable offline, so you can verify everything works before setting up external APIs.
