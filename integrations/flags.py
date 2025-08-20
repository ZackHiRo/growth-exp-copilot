import os
import json
from typing import Dict, List, Optional
from loguru import logger
import httpx
from datetime import datetime

class FeatureFlagClient:
    """Feature flag client for experiment variant management"""
    
    def __init__(self):
        self.provider = os.getenv("FLAG_PROVIDER", "posthog")  # posthog, launchdarkly, etc.
        self.api_key = os.getenv("POSTHOG_PROJECT_API_KEY")  # Using PostHog as default
        
        if not self.api_key:
            logger.warning("Feature flag API key not configured")
    
    async def create_experiment_flag(self, experiment_key: str, variants: List[str], 
                                   rollout_percentage: float = 50.0) -> Optional[str]:
        """Create a feature flag for an experiment"""
        if self.provider == "posthog":
            return await self._create_posthog_flag(experiment_key, variants, rollout_percentage)
        else:
            logger.warning(f"Feature flag provider {self.provider} not implemented")
            return None
    
    async def _create_posthog_flag(self, experiment_key: str, variants: List[str], 
                                 rollout_percentage: float) -> Optional[str]:
        """Create a feature flag in PostHog"""
        try:
            url = f"{os.getenv('POSTHOG_HOST', 'https://app.posthog.com')}/api/feature_flags/"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Create flag configuration
            payload = {
                "name": f"experiment_{experiment_key}",
                "key": f"experiment_{experiment_key}",
                "filters": {
                    "groups": [
                        {
                            "properties": [],
                            "rollout_percentage": rollout_percentage
                        }
                    ]
                },
                "deleted": False,
                "active": True,
                "ensure_experience_continuity": True
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                
                result = response.json()
                flag_key = result.get("key")
                
                logger.info(f"Created PostHog feature flag: {flag_key}")
                return flag_key
                
        except Exception as e:
            logger.error(f"Failed to create PostHog feature flag: {e}")
            return None
    
    async def update_flag_rollout(self, flag_key: str, rollout_percentage: float) -> bool:
        """Update the rollout percentage for a feature flag"""
        if self.provider == "posthog":
            return await self._update_posthog_flag_rollout(flag_key, rollout_percentage)
        else:
            logger.warning(f"Feature flag provider {self.provider} not implemented")
            return False
    
    async def _update_posthog_flag_rollout(self, flag_key: str, rollout_percentage: float) -> bool:
        """Update rollout percentage in PostHog"""
        try:
            # First get the current flag
            url = f"{os.getenv('POSTHOG_HOST', 'https://app.posthog.com')}/api/feature_flags/{flag_key}/"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                # Get current flag
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                current_flag = response.json()
                
                # Update rollout percentage
                current_flag["filters"]["groups"][0]["rollout_percentage"] = rollout_percentage
                
                # Update the flag
                response = await client.patch(url, headers=headers, json=current_flag)
                response.raise_for_status()
                
                logger.info(f"Updated PostHog flag {flag_key} rollout to {rollout_percentage}%")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update PostHog flag rollout: {e}")
            return False
    
    async def disable_flag(self, flag_key: str) -> bool:
        """Disable a feature flag"""
        if self.provider == "posthog":
            return await self._disable_posthog_flag(flag_key)
        else:
            logger.warning(f"Feature flag provider {self.provider} not implemented")
            return False
    
    async def _disable_posthog_flag(self, flag_key: str) -> bool:
        """Disable a feature flag in PostHog"""
        try:
            url = f"{os.getenv('POSTHOG_HOST', 'https://app.posthog.com')}/api/feature_flags/{flag_key}/"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {"active": False}
            
            async with httpx.AsyncClient() as client:
                response = await client.patch(url, headers=headers, json=payload)
                response.raise_for_status()
                
                logger.info(f"Disabled PostHog feature flag: {flag_key}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to disable PostHog feature flag: {e}")
            return False
    
    async def get_flag_status(self, flag_key: str) -> Dict:
        """Get the current status of a feature flag"""
        if self.provider == "posthog":
            return await self._get_posthog_flag_status(flag_key)
        else:
            logger.warning(f"Feature flag provider {self.provider} not implemented")
            return {}
    
    async def _get_posthog_flag_status(self, flag_key: str) -> Dict:
        """Get feature flag status from PostHog"""
        try:
            url = f"{os.getenv('POSTHOG_HOST', 'https://app.posthog.com')}/api/feature_flags/{flag_key}/"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                flag_data = response.json()
                
                return {
                    "key": flag_data.get("key"),
                    "name": flag_data.get("name"),
                    "active": flag_data.get("active", False),
                    "rollout_percentage": flag_data.get("filters", {}).get("groups", [{}])[0].get("rollout_percentage", 0),
                    "created_at": flag_data.get("created_at"),
                    "updated_at": flag_data.get("updated_at")
                }
                
        except Exception as e:
            logger.error(f"Failed to get PostHog flag status: {e}")
            return {}
    
    def generate_variant_code(self, experiment_key: str, variants: List[str]) -> Dict[str, str]:
        """Generate code snippets for variant assignment"""
        flag_key = f"experiment_{experiment_key}"
        
        # JavaScript/TypeScript variant assignment
        js_code = f"""
// Variant assignment for experiment: {experiment_key}
const getVariant = () => {{
    // Check if user is in experiment
    if (posthog.isFeatureEnabled('{flag_key}')) {{
        // Simple random assignment (can be made deterministic based on user ID)
        const random = Math.random();
        const variantIndex = Math.floor(random * {len(variants)});
        return {variants};
    }}
    return '{variants[0]}'; // Default to control
}};

// Usage
const variant = getVariant();
posthog.register({{ ab_variant: variant }});
"""
        
        # Python variant assignment
        python_code = f"""
import random
from posthog import PostHog

def get_variant(experiment_key='{experiment_key}'):
    # Check if user is in experiment
    if posthog.is_feature_enabled('{flag_key}'):
        # Simple random assignment (can be made deterministic based on user ID)
        variant_index = random.randint(0, {len(variants) - 1})
        return {variants}[variant_index]
    return '{variants[0]}'  # Default to control

# Usage
variant = get_variant()
posthog.capture('experiment_assigned', {{ 'ab_variant': variant }})
"""
        
        return {
            "javascript": js_code,
            "python": python_code,
            "flag_key": flag_key
        }
