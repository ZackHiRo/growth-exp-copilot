#!/usr/bin/env python3
"""
Script to seed the Chroma memory store with example experiment data
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.chroma_store import ChromaStore
from loguru import logger

async def main():
    """Seed the Chroma store with example data"""
    try:
        logger.info("Starting Chroma store seeding...")
        
        # Initialize the store
        store = ChromaStore()
        
        # Seed with examples
        store.seed_with_examples()
        
        logger.info("Chroma store seeded successfully!")
        
        # Verify the data was stored
        similar_experiments = store.retrieve_similar_experiments("checkout")
        if similar_experiments:
            logger.info(f"Found {len(similar_experiments)} similar experiments")
            for exp in similar_experiments[:2]:
                logger.info(f"- {exp['content'][:100]}...")
        
        context_results = store.retrieve_context("best practices")
        if context_results:
            logger.info(f"Found {len(context_results)} context entries")
            for ctx in context_results[:2]:
                logger.info(f"- {ctx['content'][:100]}...")
        
    except Exception as e:
        logger.error(f"Failed to seed Chroma store: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
