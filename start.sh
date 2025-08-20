#!/bin/bash

# Growth Experiment Co-Pilot Startup Script
# This script starts all required services

set -e

echo "🚀 Starting Growth Experiment Co-Pilot..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please copy env.example to .env and configure your API keys."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Start infrastructure services
echo "📦 Starting infrastructure services..."
cd infra
docker-compose up -d
cd ..

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
if ! docker-compose -f infra/docker-compose.yml ps | grep -q "Up"; then
    echo "❌ Infrastructure services failed to start. Check docker-compose logs."
    exit 1
fi

echo "✅ Infrastructure services started successfully!"

# Seed memory store if needed
echo "🧠 Seeding memory store..."
python scripts/seed_chroma.py

echo ""
echo "🎉 Growth Experiment Co-Pilot is ready!"
echo ""
echo "Next steps:"
echo "1. Start the FastAPI server:"
echo "   uvicorn app:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "2. Start the new experiment worker:"
echo "   python orchestrator/worker_new.py"
echo ""
echo "3. Start the monitoring worker:"
echo "   python orchestrator/worker_monitor.py"
echo ""
echo "4. Open http://localhost:8000/docs for API documentation"
echo "5. Open http://localhost:15672 for RabbitMQ management (guest/guest)"
echo ""
echo "Happy experimenting! 🧪"
