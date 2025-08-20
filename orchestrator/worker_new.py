import asyncio
import json
import os
import re
import yaml
from typing import Dict, List, Optional
from aio_pika import connect_robust, IncomingMessage
from loguru import logger
from agents.supervisor import create_group_chat
from integrations.github import GitHubClient
from integrations.slack import SlackClient
from integrations.flags import FeatureFlagClient
from schemas.experiment import ExperimentSpec
from memory.chroma_store import ChromaStore

class NewExperimentWorker:
    """Worker that processes new experiment ideas and creates specifications"""
    
    def __init__(self):
        self.memory = ChromaStore()
        self.github = GitHubClient()
        self.slack = SlackClient()
        self.flags = FeatureFlagClient()
    
    def extract_yaml_block(self, text: str, block_name: str) -> Optional[str]:
        """Extract YAML content from a fenced code block"""
        pattern = rf"```{block_name}\n(.*?)\n```"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else None
    
    def extract_json_block(self, text: str, block_name: str) -> Optional[Dict]:
        """Extract JSON content from a fenced code block"""
        pattern = rf"```{block_name}\n(.*?)\n```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from {block_name} block")
                return None
        return None
    
    def extract_code_blocks(self, text: str) -> List[Dict]:
        """Extract code snippets from the conversation"""
        # Look for code blocks with file paths
        pattern = r"```(\w+):([^\n]+)\n(.*?)\n```"
        matches = re.findall(pattern, text, re.DOTALL)
        
        code_snippets = []
        for language, file_path, content in matches:
            code_snippets.append({
                "language": language,
                "file_path": file_path.strip(),
                "content": content.strip()
            })
        
        # If no file paths found, look for generic code blocks
        if not code_snippets:
            pattern = r"```(\w+)\n(.*?)\n```"
            matches = re.findall(pattern, text, re.DOTALL)
            
            for language, content in matches:
                if language not in ["yaml", "json"]:  # Skip YAML/JSON blocks
                    code_snippets.append({
                        "language": language,
                        "file_path": f"experiments/implementation.{language}",
                        "content": content.strip()
                    })
        
        return code_snippets
    
    async def process_experiment_idea(self, idea_text: str, requester: str, 
                                   repo: str = None) -> Dict:
        """Process a new experiment idea through the AutoGen workflow"""
        try:
            # Retrieve similar experiments from memory
            similar_experiments = self.memory.retrieve_similar_experiments(idea_text)
            
            # Create the group chat
            manager, supervisor = create_group_chat()
            
            # Prepare the initial prompt
            context = ""
            if similar_experiments:
                context = "Similar experiments found:\n"
                for exp in similar_experiments[:3]:  # Top 3 most similar
                    context += f"- {exp['content'][:200]}...\n"
            
            initial_prompt = f"""
{context}

New Experiment Idea:
{idea_text}

Requester: {requester}
Repository: {repo or 'Not specified'}

Please design and implement this experiment following the established process.
"""
            
            logger.info(f"Starting AutoGen conversation for idea: {idea_text[:100]}...")
            
            # Start the conversation
            result = await supervisor.a_initiate_chat(
                manager,
                message=initial_prompt
            )
            
            # Extract the outputs from the conversation
            chat_history = result.chat_history if hasattr(result, 'chat_history') else []
            last_message = chat_history[-1] if chat_history else ""
            
            # Extract the required outputs
            spec_yaml = self.extract_yaml_block(last_message, "experiment_spec.yaml")
            tracking_json = self.extract_json_block(last_message, "tracking_plan.json")
            code_snippets = self.extract_code_blocks(last_message)
            
            if not spec_yaml:
                raise ValueError("No experiment specification YAML found in conversation")
            
            if not tracking_json:
                raise ValueError("No tracking plan JSON found in conversation")
            
            # Parse the experiment specification
            try:
                spec = ExperimentSpec.model_validate(yaml.safe_load(spec_yaml))
            except Exception as e:
                logger.error(f"Failed to parse experiment spec: {e}")
                raise ValueError(f"Invalid experiment specification: {e}")
            
            # Store the experiment in memory
            self.memory.store_experiment(spec.key, spec.model_dump())
            
            # Create feature flag if specified
            flag_key = None
            if spec.flag_key:
                flag_key = await self.flags.create_experiment_flag(
                    spec.key, spec.variants
                )
            
            # Create GitHub PR
            pr_url = None
            if self.github.repo:
                pr_url = await self.github.create_experiment_pr(
                    spec.key, tracking_json, code_snippets
                )
            
            # Send Slack notification
            await self.slack.post_experiment_update(
                spec.key, "specification_complete", 
                f"Experiment designed with {len(code_snippets)} code files",
                pr_url
            )
            
            if pr_url:
                await self.slack.post_pr_created(spec.key, pr_url, "experiment-branch")
            
            return {
                "experiment_key": spec.key,
                "spec": spec.model_dump(),
                "tracking_plan": tracking_json,
                "code_snippets": code_snippets,
                "pr_url": pr_url,
                "flag_key": flag_key
            }
            
        except Exception as e:
            logger.error(f"Failed to process experiment idea: {e}")
            await self.slack.post_error_alert(
                "Experiment Processing Error",
                str(e),
                f"Idea: {idea_text[:100]}..."
            )
            raise
    
    async def on_new_experiment(self, msg: IncomingMessage):
        """Handle new experiment messages from RabbitMQ"""
        async with msg.process():
            try:
                payload = json.loads(msg.body.decode())
                idea_text = payload.get("idea_text")
                requester = payload.get("requester", "unknown")
                repo = payload.get("repo")
                
                logger.info(f"Processing new experiment idea from {requester}")
                
                # Process the experiment
                result = await self.process_experiment_idea(idea_text, requester, repo)
                
                # Enqueue monitoring job
                monitor_payload = {
                    "experiment_key": result["experiment_key"],
                    "status": "ready_to_monitor"
                }
                
                await msg.channel.default_exchange.publish(
                    msg.reply(json.dumps(monitor_payload).encode()),
                    routing_key="exp.monitor"
                )
                
                logger.info(f"Experiment {result['experiment_key']} processed successfully")
                
            except Exception as e:
                logger.error(f"Error processing experiment message: {e}")
                # Reject the message
                await msg.reject(requeue=False)
    
    async def run(self):
        """Run the worker"""
        try:
            # Connect to RabbitMQ
            connection = await connect_robust(os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/"))
            channel = await connection.channel()
            
            # Declare queue
            queue = await channel.declare_queue("exp.new", durable=True)
            
            logger.info("New experiment worker started, waiting for messages...")
            
            # Start consuming messages
            await queue.consume(self.on_new_experiment)
            
            # Keep the worker running
            await asyncio.Future()
            
        except Exception as e:
            logger.error(f"Worker error: {e}")
            raise

async def main():
    """Main entry point"""
    worker = NewExperimentWorker()
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
