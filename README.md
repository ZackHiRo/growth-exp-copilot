# Growth Experiment Co-Pilot 🚀

An automated A/B testing system that transforms experiment ideas into production-ready implementations using AI agents, statistical analysis, and seamless integrations.

## 🎯 What It Does

The Growth Experiment Co-Pilot automates the entire A/B testing lifecycle:

1. **Ideation** → AI agents design statistically sound experiments
2. **Implementation** → Automatic code generation and GitHub PR creation
3. **Monitoring** → Real-time metric tracking and statistical analysis
4. **Decision** → AI-powered recommendations for shipping/stopping experiments

## 🏗️ Architecture

```
Slack / REST → RabbitMQ → AutoGen Agents → GitHub PRs → PostHog Monitoring → Decisions
```

- **AutoGen Agents**: Supervisor, Designer, Policy, Implementer, Analyst
- **Message Queue**: RabbitMQ for reliable job processing
- **Memory**: Chroma vector database for experiment context
- **Integrations**: PostHog, GitHub, Slack, Feature Flags

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- Docker & Docker Compose
- OpenAI API key
- PostHog project API key (optional)
- GitHub token (optional)
- Slack bot token (optional)

### 2. Setup Infrastructure

```bash
# Start RabbitMQ and Chroma
cd infra
docker-compose up -d

# Verify services are running
docker-compose ps
```

### 3. Install Dependencies

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy environment template
cp env.example .env

# Edit .env with your API keys
OPENAI_API_KEY=your_openai_key_here
POSTHOG_PROJECT_API_KEY=your_posthog_key_here
GITHUB_TOKEN=your_github_token_here
SLACK_BOT_TOKEN=your_slack_token_here
```

### 5. Seed Memory Store

```bash
# Seed with example experiments
python scripts/seed_chroma.py
```

### 6. Start the System

```bash
# Terminal 1: Start FastAPI server
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start new experiment worker
python orchestrator/worker_new.py

# Terminal 3: Start monitoring worker
python orchestrator/worker_monitor.py
```

## 📖 Usage Examples

### Create an Experiment via API

```bash
curl -X POST "http://localhost:8000/admin/experiments" \
  -H "Content-Type: application/json" \
  -d '{
    "idea_text": "Increase checkout conversion by adding progress indicator",
    "requester": "product_manager",
    "repo": "ecommerce/checkout"
  }'
```

### Create an Experiment via Script

```bash
# Single idea
python scripts/enqueue_demo.py --idea "Boost engagement by changing button color"

# Multiple demo ideas
python scripts/enqueue_demo.py --demo
```

### Slack Commands

Configure Slack slash commands:
- `/experiment <idea>` - Create new experiment
- `/status <key>` - Check experiment status

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for AI agents | Required |
| `MODEL_NAME` | OpenAI model to use | `gpt-4o-mini` |
| `RABBITMQ_URL` | RabbitMQ connection string | `amqp://guest:guest@localhost:5672/` |
| `POSTHOG_PROJECT_API_KEY` | PostHog API key for metrics | Optional |
| `POSTHOG_HOST` | PostHog instance URL | `https://app.posthog.com` |
| `GITHUB_TOKEN` | GitHub personal access token | Optional |
| `GITHUB_REPO` | GitHub repository (org/repo) | Optional |
| `SLACK_BOT_TOKEN` | Slack bot user OAuth token | Optional |
| `CHROMA_PERSIST_DIR` | Chroma database directory | `.chroma` |

### AutoGen Agent Configuration

Modify prompts in the `prompts/` directory to customize agent behavior:

- `supervisor.md` - Orchestrates the experiment planning process
- `designer.md` - Creates experiment specifications
- `policy.md` - Validates safety and compliance
- `implementer.md` - Generates code and tracking plans
- `analyst.md` - Analyzes results and makes decisions

## 📊 Monitoring & Analytics

### Experiment Status Endpoints

- `GET /admin/experiments` - List all experiments
- `GET /admin/experiments/{key}` - Get specific experiment details
- `POST /admin/experiments/{key}/status` - Update experiment status

### Health Checks

- `GET /health` - System health status
- RabbitMQ management UI: http://localhost:15672 (guest/guest)
- Chroma API: http://localhost:8000

## 🧪 Testing

### Run Basic Tests

```bash
# Run without pytest
python tests/test_end_to_end.py

# Run with pytest (if installed)
pytest tests/
```

### Test Fixtures

- `tests/fixtures/ideas.json` - Sample experiment ideas
- `tests/fixtures/historical_results.json` - Historical data for backtesting

## 🔒 Security & Compliance

### Built-in Safeguards

- **PII Protection**: Automatic detection and blocking of personal data
- **Statistical Rigor**: Enforces minimum power (0.8) and alpha (0.05)
- **Ethical Review**: Policy agent validates experiment safety
- **Audit Trail**: Complete logging of all decisions and actions

### Privacy Features

- No personal data stored in experiment tracking
- Anonymous user identification only
- Configurable data retention policies

## 🚨 Troubleshooting

### Common Issues

1. **RabbitMQ Connection Failed**
   ```bash
   # Check if RabbitMQ is running
   docker-compose ps
   
   # Restart services
   docker-compose restart
   ```

2. **OpenAI API Errors**
   ```bash
   # Verify API key
   echo $OPENAI_API_KEY
   
   # Check rate limits
   # Consider using gpt-4o-mini for cost optimization
   ```

3. **Chroma Database Issues**
   ```bash
   # Clear and reseed
   rm -rf .chroma
   python scripts/seed_chroma.py
   ```

### Logs

- Application logs: `logs/app.log`
- Worker logs: Check terminal output
- Docker logs: `docker-compose logs`

## 🔮 Roadmap

### Phase 2 Features

- [ ] Web UI dashboard for experiment management
- [ ] Advanced statistical methods (CUPED, stratification)
- [ ] Multi-variant testing support
- [ ] Integration with more analytics platforms
- [ ] Automated rollback capabilities
- [ ] Experiment impact estimation

### Phase 3 Features

- [ ] ML-powered experiment design recommendations
- [ ] Cross-experiment interference detection
- [ ] Automated experiment scheduling
- [ ] Advanced segmentation and targeting
- [ ] Real-time alerting and notifications

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio black isort

# Format code
black .
isort .

# Run tests
pytest tests/ -v
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Microsoft AutoGen](https://github.com/microsoft/autogen) for AI agent framework
- [PostHog](https://posthog.com/) for analytics platform
- [Chroma](https://www.trychroma.com/) for vector database
- [FastAPI](https://fastapi.tiangolo.com/) for web framework

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/growth-exp-copilot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/growth-exp-copilot/discussions)
- **Documentation**: [Wiki](https://github.com/your-org/growth-exp-copilot/wiki)

---

**Built with ❤️ for growth teams who want to move fast and test everything.**
