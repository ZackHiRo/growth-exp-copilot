import chromadb
import os
from typing import List, Dict, Optional
from loguru import logger
import json
from datetime import datetime

class ChromaStore:
    """Chroma-based memory system for storing experiment embeddings and context"""
    
    def __init__(self, persist_dir: str = ".chroma"):
        self.persist_dir = persist_dir
        self.client = chromadb.PersistentClient(path=persist_dir)
        
        # Create collections for different types of data
        self.experiments_collection = self.client.get_or_create_collection(
            name="experiments",
            metadata={"description": "Stored experiment specifications and outcomes"}
        )
        
        self.context_collection = self.client.get_or_create_collection(
            name="context",
            metadata={"description": "General experiment context and learnings"}
        )
    
    def store_experiment(self, experiment_key: str, spec: Dict, outcome: Optional[Dict] = None):
        """Store an experiment specification and optional outcome"""
        try:
            # Create document content
            content = f"""
            Experiment: {experiment_key}
            Hypothesis: {spec.get('hypothesis', 'N/A')}
            Primary Metric: {spec.get('primary_metric', {}).get('name', 'N/A')}
            Variants: {', '.join(spec.get('variants', []))}
            MDE: {spec.get('mde', 'N/A')}
            Sample Size: {spec.get('min_sample_size', 'N/A')}
            """
            
            if outcome:
                content += f"""
                Outcome: {outcome.get('decision', 'N/A')}
                Confidence: {outcome.get('confidence', 'N/A')}
                Final Sample Size: {outcome.get('final_sample_size', 'N/A')}
                """
            
            # Store in experiments collection
            self.experiments_collection.add(
                documents=[content],
                metadatas=[{
                    "experiment_key": experiment_key,
                    "type": "experiment",
                    "created_at": datetime.now().isoformat(),
                    "outcome": outcome is not None
                }],
                ids=[f"exp_{experiment_key}_{datetime.now().timestamp()}"]
            )
            
            logger.info(f"Stored experiment {experiment_key} in Chroma")
            
        except Exception as e:
            logger.error(f"Failed to store experiment {experiment_key}: {e}")
    
    def retrieve_similar_experiments(self, query: str, n_results: int = 5) -> List[Dict]:
        """Retrieve similar experiments based on query"""
        try:
            results = self.experiments_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            similar_experiments = []
            if results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    similar_experiments.append({
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else 0
                    })
            
            return similar_experiments
            
        except Exception as e:
            logger.error(f"Failed to retrieve similar experiments: {e}")
            return []
    
    def store_context(self, context_type: str, content: str, tags: List[str] = None):
        """Store general context and learnings"""
        try:
            self.context_collection.add(
                documents=[content],
                metadatas=[{
                    "type": "context",
                    "context_type": context_type,
                    "tags": tags or [],
                    "created_at": datetime.now().isoformat()
                }],
                ids=[f"ctx_{context_type}_{datetime.now().timestamp()}"]
            )
            
            logger.info(f"Stored context {context_type} in Chroma")
            
        except Exception as e:
            logger.error(f"Failed to store context {context_type}: {e}")
    
    def retrieve_context(self, query: str, context_type: Optional[str] = None, n_results: int = 3) -> List[Dict]:
        """Retrieve relevant context based on query"""
        try:
            # Filter by context type if specified
            where_filter = {"type": "context"}
            if context_type:
                where_filter["context_type"] = context_type
            
            results = self.context_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter
            )
            
            context_results = []
            if results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    context_results.append({
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else 0
                    })
            
            return context_results
            
        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            return []
    
    def seed_with_examples(self):
        """Seed the store with example experiments and context"""
        example_experiments = [
            {
                "key": "checkout_button_color",
                "hypothesis": "Changing checkout button from blue to green will increase conversion by 10%",
                "primary_metric": {"name": "checkout_conversion", "type": "rate", "event": "checkout_completed"},
                "variants": ["control", "treatment"],
                "mde": 0.10,
                "min_sample_size": 3000,
                "outcome": {"decision": "ship_treatment", "confidence": 0.96, "final_sample_size": 5000}
            },
            {
                "key": "pricing_display",
                "hypothesis": "Showing price with strikethrough will increase perceived value and conversion",
                "primary_metric": {"name": "purchase_rate", "type": "rate", "event": "purchase_completed"},
                "variants": ["control", "treatment"],
                "mde": 0.15,
                "min_sample_size": 2500,
                "outcome": {"decision": "ship_control", "confidence": 0.92, "final_sample_size": 4000}
            }
        ]
        
        for exp in example_experiments:
            self.store_experiment(exp["key"], exp, exp.get("outcome"))
        
        # Store some general context
        self.store_context(
            "best_practices",
            "Always include ab_variant property in tracking. Use consistent naming for events. Test tracking before launching.",
            tags=["tracking", "best_practices", "implementation"]
        )
        
        logger.info("Seeded Chroma store with example data")
