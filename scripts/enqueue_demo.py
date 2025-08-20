#!/usr/bin/env python3
"""
Script to enqueue demo experiment ideas for testing the system
"""

import asyncio
import sys
import os
import json
import argparse

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aio_pika import connect_robust, Message
from loguru import logger

async def enqueue_experiment_idea(idea_text: str, requester: str = "demo_user", 
                                 repo: str = None, branch: str = None):
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
                "idea_text": idea_text,
                "requester": requester,
                "repo": repo,
                "branch": branch
            }).encode(),
            delivery_mode=2  # Persistent
        )
        
        # Publish message
        await channel.default_exchange.publish(message, routing_key="exp.new")
        
        logger.info(f"✅ Enqueued experiment idea: {idea_text[:50]}...")
        
        await connection.close()
        
    except Exception as e:
        logger.error(f"❌ Failed to enqueue experiment idea: {e}")
        raise

async def enqueue_demo_ideas():
    """Enqueue several demo experiment ideas"""
    demo_ideas = [
        {
            "idea": "Increase checkout conversion by clarifying shipping fees upfront",
            "requester": "demo_user",
            "repo": "demo/ecommerce",
            "branch": "main"
        },
        {
            "idea": "Improve signup completion by reducing form fields from 8 to 5",
            "requester": "demo_user", 
            "repo": "demo/auth",
            "branch": "main"
        },
        {
            "idea": "Boost engagement by changing CTA button color from blue to green",
            "requester": "demo_user",
            "repo": "demo/landing",
            "branch": "main"
        },
        {
            "idea": "Increase revenue by showing social proof (customer reviews) on pricing page",
            "requester": "demo_user",
            "repo": "demo/pricing",
            "branch": "main"
        }
    ]
    
    logger.info("🚀 Enqueueing demo experiment ideas...")
    
    for i, idea_data in enumerate(demo_ideas, 1):
        logger.info(f"Enqueueing idea {i}/{len(demo_ideas)}: {idea_data['idea'][:50]}...")
        
        await enqueue_experiment_idea(
            idea_data["idea"],
            idea_data["requester"],
            idea_data["repo"],
            idea_data["branch"]
        )
        
        # Small delay between enqueues
        await asyncio.sleep(1)
    
    logger.info("✅ All demo ideas enqueued successfully!")

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Enqueue demo experiment ideas")
    parser.add_argument("--idea", help="Single experiment idea to enqueue")
    parser.add_argument("--demo", action="store_true", help="Enqueue all demo ideas")
    parser.add_argument("--requester", default="demo_user", help="Name of the requester")
    parser.add_argument("--repo", help="Repository name")
    parser.add_argument("--branch", default="main", help="Branch name")
    
    args = parser.parse_args()
    
    try:
        if args.idea:
            # Enqueue single idea
            await enqueue_experiment_idea(args.idea, args.requester, args.repo, args.branch)
            logger.info("Single idea enqueued successfully!")
            
        elif args.demo:
            # Enqueue all demo ideas
            await enqueue_demo_ideas()
            
        else:
            # Default: enqueue a sample idea
            sample_idea = "Increase checkout conversion by adding progress indicator"
            await enqueue_experiment_idea(sample_idea, args.requester, args.repo, args.branch)
            logger.info("Sample idea enqueued successfully!")
            
    except Exception as e:
        logger.error(f"Failed to enqueue experiment idea: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
