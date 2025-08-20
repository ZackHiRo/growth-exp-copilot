# Installation Guide: Growth Experiment Co-Pilot

## 🎯 Quick Start (5 minutes)

### 1. Prerequisites Check
```bash
# Check Python version (3.8+ required)
python --version

# Check Docker
docker --version
docker-compose --version

# Check if you have an OpenAI API key
echo $OPENAI_API_KEY
```

### 2. Clone and Setup
```bash
# Navigate to project directory
cd growth-exp-copilot

# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy environment template
cp env.example .env

# Edit .env with your API keys
# At minimum, set OPENAI_API_KEY
nano .env  # or use your preferred editor
```

### 4. Start Infrastructure
```bash
# Start RabbitMQ and Chroma
./start.sh

# Or manually:
cd infra && docker-compose up -d && cd ..
```

### 5. Test the System
```bash
# Run demo to verify everything works
python demo.py

# Start the API server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## 🔧 Detailed Installation

### Step 1: Environment Setup

#### Required Software
- **Python 3.8+**: Download from [python.org](https://python.org)
- **Docker**: Download from [docker.com](https://docker.com)
- **Git**: Usually pre-installed on macOS/Linux

#### Verify Installation
```bash
python --version          # Should be 3.8+
docker --version          # Should show Docker version
docker-compose --version  # Should show compose version
```

### Step 2: Project Setup

#### Clone Repository
```bash
# If you haven't already
git clone <your-repo-url>
cd growth-exp-copilot
```

#### Virtual Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate (choose your OS)
# macOS/Linux:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate

# Verify activation
which python  # Should point to .venv/bin/python
```

#### Install Dependencies
```bash
# Upgrade pip first
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Verify installation
python -c "import autogen, fastapi, aio_pika; print('✅ Dependencies installed')"
```

### Step 3: Configuration

#### Environment Variables
```bash
# Copy template
cp env.example .env

# Edit with your values
nano .env
```

**Required Variables:**
```bash
OPENAI_API_KEY=sk-your-key-here
MODEL_NAME=gpt-4o-mini
```

**Optional Variables (for full functionality):**
```bash
POSTHOG_PROJECT_API_KEY=phc-your-key-here
GITHUB_TOKEN=ghp-your-token-here
SLACK_BOT_TOKEN=xoxb-your-token-here
```

#### API Key Setup

**OpenAI API Key:**
1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign in or create account
3. Go to API Keys section
4. Create new secret key
5. Copy to your .env file

**PostHog API Key (Optional):**
1. Go to your PostHog project
2. Settings → Project API Keys
3. Copy the project API key

**GitHub Token (Optional):**
1. Go to GitHub Settings → Developer settings
2. Personal access tokens → Tokens (classic)
3. Generate new token with repo scope

**Slack Bot Token (Optional):**
1. Go to [api.slack.com](https://api.slack.com)
2. Create new app
3. Add bot user OAuth scope
4. Install app to workspace
5. Copy bot user OAuth token

### Step 4: Infrastructure

#### Start Services
```bash
# Use the startup script (recommended)
./start.sh

# Or manually:
cd infra
docker-compose up -d
cd ..
```

#### Verify Services
```bash
# Check Docker containers
docker-compose -f infra/docker-compose.yml ps

# Check RabbitMQ (should show "Up")
# Check Chroma (should show "Up")

# Access management interfaces:
# RabbitMQ: http://localhost:15672 (guest/guest)
# Chroma: http://localhost:8000
```

### Step 5: Testing

#### Basic Functionality Test
```bash
# Run the demo script
python demo.py

# Expected output:
# ✅ Chroma store operations passed
# ✅ Schema validation passed
# ✅ Integration clients initialized
# ✅ Agent prompts loaded
# ✅ Message flow simulation completed
# ✅ Statistical analysis demo completed
```

#### API Test
```bash
# Start the API server
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# In another terminal, test health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "version": "1.0.0"}
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Python Import Errors
```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### 2. Docker Connection Issues
```bash
# Check if Docker is running
docker info

# Restart Docker Desktop (if on macOS/Windows)
# Restart Docker service (if on Linux)
sudo systemctl restart docker
```

#### 3. Port Conflicts
```bash
# Check what's using port 8000
lsof -i :8000

# Kill process or change port in docker-compose.yml
```

#### 4. OpenAI API Errors
```bash
# Check API key
echo $OPENAI_API_KEY

# Verify key is valid
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

#### 5. RabbitMQ Connection Failed
```bash
# Check container status
docker-compose -f infra/docker-compose.yml ps

# Check logs
docker-compose -f infra/docker-compose.yml logs rabbitmq

# Restart services
docker-compose -f infra/docker-compose.yml restart
```

### Getting Help

1. **Check logs**: Look at terminal output and `logs/app.log`
2. **Verify environment**: Make sure all required variables are set
3. **Check services**: Ensure Docker containers are running
4. **Test components**: Run `python demo.py` to isolate issues

## 🎉 Success Indicators

You'll know everything is working when:

✅ `python demo.py` runs without errors  
✅ `uvicorn app:app --reload` starts successfully  
✅ `curl http://localhost:8000/health` returns healthy status  
✅ RabbitMQ management UI is accessible at http://localhost:15672  
✅ Docker containers show "Up" status  

## 🚀 Next Steps

Once installation is complete:

1. **Start workers**: Run the new experiment and monitoring workers
2. **Create experiments**: Use the API or Slack commands
3. **Monitor results**: Check the dashboard and logs
4. **Customize**: Modify prompts and configuration as needed

## 📞 Support

If you encounter issues:

1. Check this troubleshooting guide
2. Review the logs for error messages
3. Verify all prerequisites are met
4. Open an issue with detailed error information

---

**Happy experimenting! 🧪**
