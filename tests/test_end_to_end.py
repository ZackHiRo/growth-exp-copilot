#!/usr/bin/env python3
"""
End-to-end tests for the Growth Experiment Co-Pilot
"""

import asyncio
import sys
import os
import json
import pytest
from unittest.mock import Mock, patch, AsyncMock

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.supervisor import create_group_chat, create_monitoring_chat
from memory.chroma_store import ChromaStore
from integrations.posthog import PostHogClient
from integrations.github import GitHubClient
from integrations.slack import SlackClient
from integrations.flags import FeatureFlagClient
from schemas.experiment import ExperimentSpec, Metric

class TestGrowthExperimentCoPilot:
    """Test suite for the Growth Experiment Co-Pilot"""
    
    @pytest.fixture
    def sample_experiment_spec(self):
        """Sample experiment specification for testing"""
        return {
            "key": "test_checkout_conversion",
            "hypothesis": "Adding progress indicator will increase checkout completion by 15%",
            "variants": ["control", "treatment"],
            "primary_metric": {
                "name": "checkout_completion_rate",
                "type": "rate",
                "event": "checkout_completed"
            },
            "secondary_metrics": [
                {
                    "name": "cart_abandonment_rate",
                    "type": "rate",
                    "event": "cart_abandoned"
                }
            ],
            "segment_filters": {"country": "US"},
            "mde": 0.15,
            "alpha": 0.05,
            "power": 0.8,
            "min_sample_size": 2500,
            "max_duration_days": 14
        }
    
    @pytest.fixture
    def sample_tracking_plan(self):
        """Sample tracking plan for testing"""
        return {
            "events": [
                {
                    "name": "checkout_started",
                    "properties": ["cart_value", "currency", "ab_variant"]
                },
                {
                    "name": "checkout_completed",
                    "properties": ["order_value", "currency", "ab_variant"]
                }
            ],
            "guardrails": {
                "must_have": ["ab_variant"],
                "pii_ban": ["email", "phone", "name"],
                "experiment_key": "test_checkout_conversion"
            }
        }
    
    def test_experiment_spec_validation(self, sample_experiment_spec):
        """Test that experiment specifications are properly validated"""
        try:
            spec = ExperimentSpec.model_validate(sample_experiment_spec)
            assert spec.key == "test_checkout_conversion"
            assert spec.hypothesis == "Adding progress indicator will increase checkout completion by 15%"
            assert spec.primary_metric.type == "rate"
            assert spec.power == 0.8
            assert spec.alpha == 0.05
            assert spec.min_sample_size == 2500
            print("✅ Experiment spec validation passed")
        except Exception as e:
            pytest.fail(f"Experiment spec validation failed: {e}")
    
    def test_metric_validation(self):
        """Test metric validation"""
        try:
            metric = Metric(
                name="test_metric",
                type="rate",
                event="test_event"
            )
            assert metric.name == "test_metric"
            assert metric.type == "rate"
            assert metric.event == "test_event"
            print("✅ Metric validation passed")
        except Exception as e:
            pytest.fail(f"Metric validation failed: {e}")
    
    @pytest.mark.asyncio
    async def test_chroma_store_operations(self):
        """Test Chroma store operations"""
        try:
            store = ChromaStore(persist_dir=".test_chroma")
            
            # Test storing experiment
            test_spec = {"key": "test", "hypothesis": "test hypothesis"}
            store.store_experiment("test_key", test_spec)
            
            # Test retrieval
            results = store.retrieve_similar_experiments("test")
            assert len(results) > 0
            
            # Test storing context
            store.store_context("test_context", "test content", ["test"])
            
            # Test context retrieval
            context_results = store.retrieve_context("test")
            assert len(context_results) > 0
            
            print("✅ Chroma store operations passed")
            
        except Exception as e:
            pytest.fail(f"Chroma store operations failed: {e}")
    
    @pytest.mark.asyncio
    async def test_posthog_client(self):
        """Test PostHog client functionality"""
        try:
            client = PostHogClient()
            
            # Test metric counts (mock data)
            suc_c, tot_c, suc_t, tot_t = client.get_metric_counts("test_experiment")
            assert suc_c == 480
            assert tot_c == 5000
            assert suc_t == 520
            assert tot_t == 5000
            
            print("✅ PostHog client tests passed")
            
        except Exception as e:
            pytest.fail(f"PostHog client tests failed: {e}")
    
    @pytest.mark.asyncio
    async def test_github_client_initialization(self):
        """Test GitHub client initialization"""
        try:
            # Test without credentials (should handle gracefully)
            with patch.dict(os.environ, {}, clear=True):
                client = GitHubClient()
                assert client.repo is None
            
            print("✅ GitHub client initialization tests passed")
            
        except Exception as e:
            pytest.fail(f"GitHub client initialization tests failed: {e}")
    
    @pytest.mark.asyncio
    async def test_slack_client_initialization(self):
        """Test Slack client initialization"""
        try:
            # Test without credentials (should handle gracefully)
            with patch.dict(os.environ, {}, clear=True):
                client = SlackClient()
                # Should not crash
                assert True
            
            print("✅ Slack client initialization tests passed")
            
        except Exception as e:
            pytest.fail(f"Slack client initialization tests failed: {e}")
    
    @pytest.mark.asyncio
    async def test_feature_flag_client(self):
        """Test feature flag client functionality"""
        try:
            client = FeatureFlagClient()
            
            # Test variant code generation
            variants = ["control", "treatment"]
            code_snippets = client.generate_variant_code("test_experiment", variants)
            
            assert "javascript" in code_snippets
            assert "python" in code_snippets
            assert "flag_key" in code_snippets
            assert "experiment_test_experiment" in code_snippets["flag_key"]
            
            print("✅ Feature flag client tests passed")
            
        except Exception as e:
            pytest.fail(f"Feature flag client tests failed: {e}")
    
    def test_agent_creation(self):
        """Test that AutoGen agents can be created"""
        try:
            # Test group chat creation
            manager, supervisor = create_group_chat()
            assert manager is not None
            assert supervisor is not None
            
            # Test monitoring chat creation
            monitor_manager, analyst = create_monitoring_chat()
            assert monitor_manager is not None
            assert analyst is not None
            
            print("✅ Agent creation tests passed")
            
        except Exception as e:
            pytest.fail(f"Agent creation tests failed: {e}")
    
    def test_tracking_plan_validation(self, sample_tracking_plan):
        """Test tracking plan structure"""
        try:
            # Check required fields
            assert "events" in sample_tracking_plan
            assert "guardrails" in sample_tracking_plan
            
            # Check events structure
            events = sample_tracking_plan["events"]
            assert len(events) > 0
            assert "name" in events[0]
            assert "properties" in events[0]
            
            # Check guardrails
            guardrails = sample_tracking_plan["guardrails"]
            assert "must_have" in guardrails
            assert "pii_ban" in guardrails
            
            print("✅ Tracking plan validation passed")
            
        except Exception as e:
            pytest.fail(f"Tracking plan validation failed: {e}")

def run_basic_tests():
    """Run basic tests without pytest"""
    print("🧪 Running Growth Experiment Co-Pilot tests...\n")
    
    test_suite = TestGrowthExperimentCoPilot()
    
    # Run synchronous tests
    test_suite.test_experiment_spec_validation(test_suite.sample_experiment_spec())
    test_suite.test_metric_validation()
    test_suite.test_tracking_plan_validation(test_suite.sample_tracking_plan())
    test_suite.test_agent_creation()
    test_suite.test_feature_flag_client()
    
    print("\n✅ Basic tests completed successfully!")
    print("Note: Some async tests require proper environment setup")

if __name__ == "__main__":
    run_basic_tests()
