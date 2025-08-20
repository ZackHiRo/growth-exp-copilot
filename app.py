from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
import os
import json
import asyncio
from aio_pika import connect_robust, Message
from loguru import logger
from memory.chroma_store import ChromaStore
from integrations.slack import SlackClient
from integrations.github import GitHubClient
from integrations.posthog import PostHogClient
from schemas.experiment import ExperimentSpec, ExperimentStatus

# Configure logging
logger.add("logs/app.log", rotation="1 day", retention="7 days")

app = FastAPI(
    title="Growth Experiment Co-Pilot",
    description="Automated A/B testing from ideation to analysis",
    version="1.0.0"
)

# Initialize clients
memory = ChromaStore()
slack = SlackClient()
github = GitHubClient()
posthog = PostHogClient()

# Request models
class ExperimentIdea(BaseModel):
    idea_text: str
    requester: str
    repo: Optional[str] = None
    branch: Optional[str] = None

class SlackSlashCommand(BaseModel):
    command: str
    text: str
    user_id: str
    user_name: str
    channel_id: str
    team_id: str

class ExperimentStatusUpdate(BaseModel):
    experiment_key: str
    status: str
    details: Optional[str] = None

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time(),
        "version": "1.0.0"
    }

# Admin endpoints
@app.get("/admin/experiments")
async def list_experiments():
    """List all experiments in the system"""
    try:
        # This would typically query a database
        # For now, return mock data
        experiments = [
            {
                "key": "checkout_button_color",
                "hypothesis": "Changing checkout button from blue to green will increase conversion",
                "status": "running",
                "created_at": "2024-01-15T10:00:00Z"
            },
            {
                "key": "pricing_display",
                "hypothesis": "Showing price with strikethrough will increase perceived value",
                "status": "completed",
                "created_at": "2024-01-10T14:30:00Z"
            }
        ]
        
        return {"experiments": experiments}
        
    except Exception as e:
        logger.error(f"Failed to list experiments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/experiments/{experiment_key}")
async def get_experiment(experiment_key: str):
    """Get details for a specific experiment"""
    try:
        # Retrieve from memory
        similar_experiments = memory.retrieve_similar_experiments(experiment_key)
        
        if not similar_experiments:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        # Return the most relevant result
        experiment_data = similar_experiments[0]
        
        return {
            "experiment_key": experiment_key,
            "data": experiment_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get experiment {experiment_key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/experiments")
async def create_experiment(idea: ExperimentIdea, background_tasks: BackgroundTasks):
    """Create a new experiment from an idea"""
    try:
        # Enqueue the experiment idea for processing
        await enqueue_experiment_idea(idea)
        
        # Add background task to send confirmation
        background_tasks.add_task(
            send_experiment_confirmation,
            idea.idea_text,
            idea.requester
        )
        
        return {
            "message": "Experiment idea queued for processing",
            "idea": idea.idea_text[:100] + "..." if len(idea.idea_text) > 100 else idea.idea_text,
            "requester": idea.requester
        }
        
    except Exception as e:
        logger.error(f"Failed to create experiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/experiments/{experiment_key}/status")
async def update_experiment_status(experiment_key: str, update: ExperimentStatusUpdate):
    """Update experiment status"""
    try:
        # This would typically update a database
        # For now, just log the update
        logger.info(f"Status update for {experiment_key}: {update.status}")
        
        # Send Slack notification
        await slack.post_experiment_update(
            experiment_key,
            update.status,
            update.details
        )
        
        return {"message": "Status updated successfully"}
        
    except Exception as e:
        logger.error(f"Failed to update experiment status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Slack integration
@app.post("/slack/commands")
async def handle_slack_command(request: Request):
    """Handle Slack slash commands"""
    try:
        # Parse form data from Slack
        form_data = await request.form()
        
        command = form_data.get("command", "")
        text = form_data.get("text", "")
        user_id = form_data.get("user_id", "")
        user_name = form_data.get("user_name", "")
        channel_id = form_data.get("channel_id", "")
        
        logger.info(f"Slack command: {command} from {user_name}: {text}")
        
        if command == "/experiment":
            # Handle experiment creation command
            if not text:
                return JSONResponse(content={
                    "text": "Usage: /experiment <your experiment idea>",
                    "response_type": "ephemeral"
                })
            
            # Create experiment idea
            idea = ExperimentIdea(
                idea_text=text,
                requester=user_name,
                repo=None
            )
            
            # Enqueue for processing
            await enqueue_experiment_idea(idea)
            
            return JSONResponse(content={
                "text": f"🚀 Experiment idea queued for processing!\n\n*Your idea:* {text}\n\nI'll design the experiment and create a PR for you.",
                "response_type": "in_channel"
            })
        
        elif command == "/status":
            # Handle status check command
            if not text:
                return JSONResponse(content={
                    "text": "Usage: /status <experiment_key>",
                    "response_type": "ephemeral"
                })
            
            # Get experiment status
            similar_experiments = memory.retrieve_similar_experiments(text)
            
            if not similar_experiments:
                return JSONResponse(content={
                    "text": f"❌ Experiment '{text}' not found",
                    "response_type": "ephemeral"
                })
            
            # Return status
            experiment_data = similar_experiments[0]
            return JSONResponse(content={
                "text": f"📊 *Experiment Status: {text}*\n\n{experiment_data['content'][:200]}...",
                "response_type": "ephemeral"
            })
        
        else:
            return JSONResponse(content={
                "text": "Unknown command. Available commands:\n• /experiment <idea> - Create new experiment\n• /status <key> - Check experiment status",
                "response_type": "ephemeral"
            })
            
    except Exception as e:
        logger.error(f"Failed to handle Slack command: {e}")
        return JSONResponse(content={
            "text": "❌ An error occurred while processing your command",
            "response_type": "ephemeral"
        })

# Utility functions
async def enqueue_experiment_idea(idea: ExperimentIdea):
    """Enqueue an experiment idea to RabbitMQ"""
    try:
        # Connect to RabbitMQ
        connection = await connect_robust(os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/"))
        channel = await connection.channel()
        
        # Declare queue
        queue = await channel.declare_queue("exp.new", durable=True)
        
        # Create message
        message = Message(
            body=json.dumps({
                "idea_text": idea.idea_text,
                "requester": idea.requester,
                "repo": idea.repo,
                "branch": idea.branch
            }).encode(),
            delivery_mode=2  # Persistent
        )
        
        # Publish message
        await channel.default_exchange.publish(message, routing_key="exp.new")
        
        logger.info(f"Enqueued experiment idea from {idea.requester}")
        
        await connection.close()
        
    except Exception as e:
        logger.error(f"Failed to enqueue experiment idea: {e}")
        raise

async def send_experiment_confirmation(idea_text: str, requester: str):
    """Send confirmation message to Slack"""
    try:
        await slack.send_message(
            f"✅ Experiment idea received from {requester}:\n\n{idea_text[:200]}...\n\nProcessing will begin shortly.",
            channel="#experiments"  # You can make this configurable
        )
    except Exception as e:
        logger.error(f"Failed to send confirmation: {e}")

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Growth Experiment Co-Pilot...")
    
    # Seed memory with example data if empty
    try:
        # Check if memory is empty and seed if needed
        similar_experiments = memory.retrieve_similar_experiments("test")
        if not similar_experiments:
            logger.info("Seeding memory with example data...")
            memory.seed_with_examples()
    except Exception as e:
        logger.warning(f"Failed to seed memory: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Growth Experiment Co-Pilot...")

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
