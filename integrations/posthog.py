import os
import httpx
import json
from typing import Dict, List, Tuple, Optional
from loguru import logger
from datetime import datetime, timedelta

class PostHogClient:
    """PostHog API client for experiment metrics"""
    
    def __init__(self):
        self.api_key = os.getenv("POSTHOG_PROJECT_API_KEY")
        self.host = os.getenv("POSTHOG_HOST", "https://app.posthog.com")
        self.base_url = f"{self.host}/api"
        
        if not self.api_key:
            logger.warning("POSTHOG_PROJECT_API_KEY not set")
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make a request to PostHog API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            url = f"{self.base_url}/{endpoint}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"PostHog API request failed: {e}")
            return None
    
    async def get_events(self, event_name: str, start_date: str, end_date: str, 
                        filters: Dict = None) -> List[Dict]:
        """Get events from PostHog"""
        params = {
            "event": event_name,
            "date_from": start_date,
            "date_to": end_date,
            "limit": 10000
        }
        
        if filters:
            params["properties"] = json.dumps(filters)
        
        result = await self._make_request("events", params)
        return result.get("results", []) if result else []
    
    async def get_insights(self, query: Dict) -> Optional[Dict]:
        """Get insights using PostHog Query API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            url = f"{self.base_url}/insights/trend/"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=query)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"PostHog Insights API request failed: {e}")
            return None
    
    def get_metric_counts(self, experiment_key: str, days_back: int = 7) -> Tuple[int, int, int, int]:
        """
        Get metric counts for experiment variants
        Returns: (success_control, total_control, success_treatment, total_treatment)
        """
        # This is a placeholder implementation
        # In production, you would:
        # 1. Query PostHog for events with ab_variant property
        # 2. Filter by experiment_key
        # 3. Aggregate by variant and metric
        
        logger.info(f"Getting metric counts for experiment {experiment_key}")
        
        # Mock data for development
        # Replace with actual PostHog queries
        return 480, 5000, 520, 5000
    
    async def get_experiment_metrics(self, experiment_key: str, metric_name: str, 
                                   days_back: int = 7) -> Dict:
        """Get comprehensive metrics for an experiment"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Query for control variant
        control_events = await self.get_events(
            metric_name,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
            {"ab_variant": "control", "experiment_key": experiment_key}
        )
        
        # Query for treatment variant
        treatment_events = await self.get_events(
            metric_name,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
            {"ab_variant": "treatment", "experiment_key": experiment_key}
        )
        
        # Aggregate metrics
        control_count = len(control_events)
        treatment_count = len(treatment_events)
        
        # Calculate success rates (assuming binary outcome)
        control_success = sum(1 for e in control_events if e.get("success", False))
        treatment_success = sum(1 for e in treatment_events if e.get("success", False))
        
        return {
            "control": {
                "total": control_count,
                "success": control_success,
                "rate": control_success / control_count if control_count > 0 else 0
            },
            "treatment": {
                "total": treatment_count,
                "success": treatment_success,
                "rate": treatment_success / treatment_count if treatment_count > 0 else 0
            },
            "experiment_key": experiment_key,
            "metric": metric_name,
            "period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        }
    
    def validate_tracking(self, experiment_key: str, required_events: List[str]) -> Dict:
        """Validate that required events are being tracked"""
        # This would check if events are actually being received
        # For now, return mock validation
        validation_result = {
            "experiment_key": experiment_key,
            "valid": True,
            "missing_events": [],
            "tracking_quality": "good",
            "last_seen": datetime.now().isoformat()
        }
        
        logger.info(f"Tracking validation for {experiment_key}: {validation_result}")
        return validation_result
