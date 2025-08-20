import asyncio
import json
import os
import numpy as np
from typing import Dict, List, Tuple, Optional
from aio_pika import connect_robust, IncomingMessage
from loguru import logger
from integrations.posthog import PostHogClient
from integrations.slack import SlackClient
from integrations.github import GitHubClient
from memory.chroma_store import ChromaStore
from agents.supervisor import create_monitoring_chat
import re

class MonitoringWorker:
    """Worker that monitors running experiments and makes decisions"""
    
    def __init__(self):
        self.posthog = PostHogClient()
        self.slack = SlackClient()
        self.github = GitHubClient()
        self.memory = ChromaStore()
        self.monitoring_interval = 600  # 10 minutes
    
    def bayes_prob_better(self, suc_a: int, tot_a: int, suc_b: int, tot_b: int, 
                          sims: int = 20000) -> float:
        """Calculate Bayesian probability that treatment is better than control"""
        try:
            # Beta-Binomial approach with uniform priors
            a1, b1 = suc_a + 1, (tot_a - suc_a) + 1
            a2, b2 = suc_b + 1, (tot_b - suc_b) + 1
            
            # Sample from beta distributions
            sa = np.random.beta(a1, b1, sims)
            sb = np.random.beta(a2, b2, sims)
            
            # Calculate probability treatment > control
            prob = float((sb > sa).mean())
            
            return prob
            
        except Exception as e:
            logger.error(f"Bayesian calculation failed: {e}")
            return 0.5  # Neutral probability on error
    
    def msprt_test(self, control_data: List[float], treatment_data: List[float], 
                   alpha: float = 0.05) -> Dict:
        """Modified Sequential Probability Ratio Test for mean metrics"""
        try:
            if len(control_data) < 10 or len(treatment_data) < 10:
                return {"decision": "extend", "confidence": 0.5, "reason": "insufficient_data"}
            
            # Calculate means and standard errors
            control_mean = np.mean(control_data)
            treatment_mean = np.mean(treatment_data)
            
            control_se = np.std(control_data) / np.sqrt(len(control_data))
            treatment_se = np.std(treatment_data) / np.sqrt(len(treatment_data))
            
            # Pooled standard error
            pooled_se = np.sqrt(control_se**2 + treatment_se**2)
            
            # Effect size
            effect_size = (treatment_mean - control_mean) / pooled_se
            
            # Critical values for alpha = 0.05
            critical_value = 1.96
            
            if effect_size > critical_value:
                return {"decision": "ship_treatment", "confidence": 0.95, "reason": "significant_positive"}
            elif effect_size < -critical_value:
                return {"decision": "ship_control", "confidence": 0.95, "reason": "significant_negative"}
            else:
                return {"decision": "extend", "confidence": 0.5, "reason": "no_significant_difference"}
                
        except Exception as e:
            logger.error(f"mSPRT test failed: {e}")
            return {"decision": "extend", "confidence": 0.5, "reason": "test_error"}
    
    async def analyze_experiment(self, experiment_key: str, spec: Dict) -> Dict:
        """Analyze experiment results and make decision"""
        try:
            # Get metric counts from PostHog
            suc_c, tot_c, suc_t, tot_t = self.posthog.get_metric_counts(experiment_key)
            
            total_sample = tot_c + tot_t
            min_sample = spec.get("min_sample_size", 2000)
            
            # Check if we have enough data
            if total_sample < min_sample:
                return {
                    "decision": "extend",
                    "confidence": 0.5,
                    "sample_size": total_sample,
                    "reason": f"Insufficient sample size ({total_sample} < {min_sample})"
                }
            
            # Determine metric type and run appropriate test
            metric_type = spec.get("primary_metric", {}).get("type", "rate")
            
            if metric_type == "rate":
                # Use Bayesian approach for rate metrics
                prob_better = self.bayes_prob_better(suc_c, tot_c, suc_t, tot_t)
                
                # Decision logic
                if prob_better >= 0.95:
                    decision = "ship_treatment"
                    confidence = prob_better
                    reason = "Strong evidence treatment is better"
                elif prob_better <= 0.05:
                    decision = "ship_control"
                    confidence = 1 - prob_better
                    reason = "Strong evidence control is better"
                else:
                    decision = "extend"
                    confidence = 0.5
                    reason = "Inconclusive results"
                
                return {
                    "decision": decision,
                    "confidence": confidence,
                    "sample_size": total_sample,
                    "reason": reason,
                    "prob_treatment_better": prob_better
                }
            
            elif metric_type == "mean":
                # Use mSPRT for mean metrics
                # This would require getting actual metric values, not just counts
                # For now, use a simplified approach
                control_rate = suc_c / tot_c if tot_c > 0 else 0
                treatment_rate = suc_t / tot_t if tot_t > 0 else 0
                
                if treatment_rate > control_rate * 1.1:  # 10% improvement
                    return {
                        "decision": "ship_treatment",
                        "confidence": 0.9,
                        "sample_size": total_sample,
                        "reason": "Treatment shows improvement"
                    }
                elif treatment_rate < control_rate * 0.9:  # 10% degradation
                    return {
                        "decision": "ship_control",
                        "confidence": 0.9,
                        "sample_size": total_sample,
                        "reason": "Treatment shows degradation"
                    }
                else:
                    return {
                        "decision": "extend",
                        "confidence": 0.5,
                        "sample_size": total_sample,
                        "reason": "No clear difference"
                    }
            
            else:
                return {
                    "decision": "extend",
                    "confidence": 0.5,
                    "sample_size": total_sample,
                    "reason": f"Unknown metric type: {metric_type}"
                }
                
        except Exception as e:
            logger.error(f"Failed to analyze experiment {experiment_key}: {e}")
            return {
                "decision": "extend",
                "confidence": 0.5,
                "sample_size": 0,
                "reason": f"Analysis error: {str(e)}"
            }
    
    async def use_ai_analyst(self, experiment_key: str, spec: Dict, 
                            analysis_result: Dict) -> Dict:
        """Use the AI analyst to review and potentially override the decision"""
        try:
            # Create monitoring chat
            manager, analyst = create_monitoring_chat()
            
            # Prepare the analysis prompt
            prompt = f"""
Experiment: {experiment_key}
Primary Metric: {spec.get('primary_metric', {}).get('name', 'N/A')}
Metric Type: {spec.get('primary_metric', {}).get('type', 'N/A')}

Current Analysis:
- Decision: {analysis_result.get('decision', 'N/A')}
- Confidence: {analysis_result.get('confidence', 'N/A')}
- Sample Size: {analysis_result.get('sample_size', 'N/A')}
- Reason: {analysis_result.get('reason', 'N/A')}

Please review this analysis and provide your recommendation.
"""
            
            # Get AI analysis
            result = await analyst.a_initiate_chat(manager, message=prompt)
            
            # Parse the AI response for decision
            ai_response = result.chat_history[-1] if hasattr(result, 'chat_history') else ""
            
            # Look for decision in the response
            decision_match = re.search(r"DECISION:\s*(\w+)", ai_response, re.IGNORECASE)
            confidence_match = re.search(r"CONFIDENCE:\s*([\d.]+)", ai_response, re.IGNORECASE)
            rationale_match = re.search(r"RATIONALE:\s*(.+)", ai_response, re.IGNORECASE)
            
            if decision_match:
                ai_decision = decision_match.group(1).lower()
                ai_confidence = float(confidence_match.group(1)) if confidence_match else 0.8
                ai_rationale = rationale_match.group(1) if rationale_match else "AI analysis"
                
                # Override if AI confidence is higher
                if ai_confidence > analysis_result.get('confidence', 0):
                    return {
                        "decision": ai_decision,
                        "confidence": ai_confidence,
                        "sample_size": analysis_result.get('sample_size', 0),
                        "reason": f"AI override: {ai_rationale}",
                        "ai_override": True
                    }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"AI analyst failed: {e}")
            return analysis_result
    
    async def handle_experiment_decision(self, experiment_key: str, decision: str, 
                                       confidence: float, sample_size: int, reason: str):
        """Handle the final experiment decision"""
        try:
            # Update experiment status in memory
            outcome = {
                "decision": decision,
                "confidence": confidence,
                "final_sample_size": sample_size,
                "reason": reason,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # Get the experiment spec from memory
            similar_experiments = self.memory.retrieve_similar_experiments(experiment_key)
            if similar_experiments:
                # Update the stored experiment with outcome
                self.memory.store_experiment(experiment_key, {}, outcome)
            
            # Send Slack notification
            await self.slack.post_experiment_decision(
                experiment_key, decision, confidence, sample_size
            )
            
            # Add comment to GitHub PR if available
            if self.github.repo:
                comment = f"""
## Experiment Decision: {experiment_key}

**Decision**: {decision.replace('_', ' ').title()}
**Confidence**: {confidence:.1%}
**Sample Size**: {sample_size:,}
**Reason**: {reason}

*This decision was made automatically by the Growth Experiment Co-Pilot*
"""
                # Try to find and comment on the PR
                # This is a simplified approach - in production you'd track PR numbers
                logger.info(f"Experiment {experiment_key} decision: {decision}")
            
            # Enqueue final decision event
            decision_payload = {
                "experiment_key": experiment_key,
                "decision": decision,
                "confidence": confidence,
                "sample_size": sample_size,
                "reason": reason,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # This would be sent to the exp.decision queue
            logger.info(f"Experiment {experiment_key} completed with decision: {decision}")
            
        except Exception as e:
            logger.error(f"Failed to handle experiment decision: {e}")
    
    async def on_monitor_experiment(self, msg: IncomingMessage):
        """Handle experiment monitoring messages from RabbitMQ"""
        async with msg.process():
            try:
                payload = json.loads(msg.body.decode())
                experiment_key = payload.get("experiment_key")
                
                logger.info(f"Monitoring experiment: {experiment_key}")
                
                # Get experiment spec from memory
                similar_experiments = self.memory.retrieve_similar_experiments(experiment_key)
                if not similar_experiments:
                    logger.warning(f"No experiment spec found for {experiment_key}")
                    return
                
                # Use the first (most relevant) result
                experiment_data = similar_experiments[0]
                spec = experiment_data.get('metadata', {})
                
                # Analyze the experiment
                analysis_result = await self.analyze_experiment(experiment_key, spec)
                
                # Get AI review
                final_result = await self.use_ai_analyst(experiment_key, spec, analysis_result)
                
                # Handle the decision
                await self.handle_experiment_decision(
                    experiment_key,
                    final_result["decision"],
                    final_result["confidence"],
                    final_result["sample_size"],
                    final_result["reason"]
                )
                
                # If extending, re-enqueue for later monitoring
                if final_result["decision"] == "extend":
                    # Wait for monitoring interval, then re-enqueue
                    await asyncio.sleep(self.monitoring_interval)
                    
                    extend_payload = {
                        "experiment_key": experiment_key,
                        "status": "continue_monitoring"
                    }
                    
                    await msg.channel.default_exchange.publish(
                        msg.reply(json.dumps(extend_payload).encode()),
                        routing_key="exp.monitor"
                    )
                
            except Exception as e:
                logger.error(f"Error monitoring experiment: {e}")
                await msg.reject(requeue=False)
    
    async def run(self):
        """Run the monitoring worker"""
        try:
            # Connect to RabbitMQ
            connection = await connect_robust(os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/"))
            channel = await connection.channel()
            
            # Declare queue
            queue = await channel.declare_queue("exp.monitor", durable=True)
            
            logger.info("Monitoring worker started, waiting for messages...")
            
            # Start consuming messages
            await queue.consume(self.on_monitor_experiment)
            
            # Keep the worker running
            await asyncio.Future()
            
        except Exception as e:
            logger.error(f"Monitoring worker error: {e}")
            raise

async def main():
    """Main entry point"""
    worker = MonitoringWorker()
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
