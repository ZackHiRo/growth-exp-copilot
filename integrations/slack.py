import os
import json
from typing import Dict, Optional
from loguru import logger
import httpx
from datetime import datetime

class SlackClient:
    """Slack client for experiment notifications and updates"""
    
    def __init__(self):
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.channel_approvals = os.getenv("SLACK_CHANNEL_APPROVALS")
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")  # Alternative to bot token
        
        if not self.bot_token and not self.webhook_url:
            logger.warning("Slack credentials not configured")
    
    async def _send_webhook_message(self, message: str, channel: str = None) -> bool:
        """Send message using webhook (fallback method)"""
        if not self.webhook_url:
            return False
        
        try:
            payload = {
                "text": message,
                "channel": channel or self.channel_approvals
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook_url, json=payload)
                response.raise_for_status()
                
            logger.info("Sent Slack message via webhook")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Slack webhook message: {e}")
            return False
    
    async def _send_bot_message(self, message: str, channel: str = None) -> bool:
        """Send message using bot token"""
        if not self.bot_token:
            return False
        
        try:
            target_channel = channel or self.channel_approvals
            if not target_channel:
                logger.error("No Slack channel specified")
                return False
            
            url = "https://slack.com/api/chat.postMessage"
            headers = {
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "channel": target_channel,
                "text": message,
                "as_user": False
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                
                result = response.json()
                if not result.get("ok"):
                    logger.error(f"Slack API error: {result.get('error')}")
                    return False
            
            logger.info(f"Sent Slack message to {target_channel}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Slack bot message: {e}")
            return False
    
    async def send_message(self, message: str, channel: str = None) -> bool:
        """Send a message to Slack using available method"""
        # Try bot token first, then webhook
        if await self._send_bot_message(message, channel):
            return True
        
        return await self._send_webhook_message(message, channel)
    
    async def post_experiment_update(self, experiment_key: str, status: str, 
                                   details: str = None, pr_url: str = None) -> bool:
        """Post an experiment status update to Slack"""
        message = f"""
🚀 *Experiment Update: {experiment_key}*
Status: {status}
"""
        
        if details:
            message += f"Details: {details}\n"
        
        if pr_url:
            message += f"PR: {pr_url}\n"
        
        message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return await self.send_message(message)
    
    async def post_experiment_decision(self, experiment_key: str, decision: str, 
                                     confidence: float, sample_size: int) -> bool:
        """Post experiment decision results to Slack"""
        emoji_map = {
            "ship_treatment": "✅",
            "ship_control": "❌", 
            "extend": "⏳",
            "stop": "🛑"
        }
        
        emoji = emoji_map.get(decision, "📊")
        
        message = f"""
{emoji} *Experiment Decision: {experiment_key}*
Decision: {decision.replace('_', ' ').title()}
Confidence: {confidence:.1%}
Sample Size: {sample_size:,}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return await self.send_message(message)
    
    async def post_pr_created(self, experiment_key: str, pr_url: str, 
                             branch: str) -> bool:
        """Post notification when PR is created"""
        message = f"""
🔧 *PR Created for Experiment: {experiment_key}*
Branch: `{branch}`
PR: {pr_url}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return await self.send_message(message)
    
    async def post_tracking_validation(self, experiment_key: str, is_valid: bool, 
                                     issues: list = None) -> bool:
        """Post tracking validation results"""
        status_emoji = "✅" if is_valid else "❌"
        status_text = "PASSED" if is_valid else "FAILED"
        
        message = f"""
{status_emoji} *Tracking Validation: {experiment_key}*
Status: {status_text}
"""
        
        if issues:
            message += f"Issues Found:\n"
            for issue in issues:
                message += f"• {issue}\n"
        
        message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return await self.send_message(message)
    
    async def post_error_alert(self, error_type: str, error_message: str, 
                              context: str = None) -> bool:
        """Post error alerts to Slack"""
        message = f"""
🚨 *Error Alert: {error_type}*
Error: {error_message}
"""
        
        if context:
            message += f"Context: {context}\n"
        
        message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return await self.send_message(message)
    
    def format_experiment_summary(self, experiment_data: Dict) -> str:
        """Format experiment data for Slack display"""
        spec = experiment_data.get('spec', {})
        
        summary = f"""
📊 *Experiment Summary: {spec.get('key', 'Unknown')}*
Hypothesis: {spec.get('hypothesis', 'N/A')}
Primary Metric: {spec.get('primary_metric', {}).get('name', 'N/A')}
Variants: {', '.join(spec.get('variants', []))}
MDE: {spec.get('mde', 'N/A')}
Sample Size: {spec.get('min_sample_size', 'N/A'):,}
Duration: {spec.get('max_duration_days', 'N/A')} days
Status: {spec.get('status', 'N/A')}
"""
        
        return summary
