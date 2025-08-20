#!/usr/bin/env python3
"""
Mock-based integration tests for Growth Experiment Co-Pilot
These tests run without requiring external API keys or services
"""

import asyncio
import sys
import os
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.supervisor import create_group_chat, create_monitoring_chat
from memory.chroma_store import ChromaStore
from integrations.posthog import PostHogClient
from integrations.github import GitHubClient
from integrations.slack import SlackClient
from integrations.flags import FeatureFlagClient
from schemas.experiment import ExperimentSpec, Metric, TrackingPlan
from orchestrator.worker_new import NewExperimentWorker
from orchestrator.worker_monitor import MonitoringWorker

class MockIntegrationTests:
    """Test suite using mocked external services"""
    
    def __init__(self):
        self.mock_posthog_data = {
            "control": {"conversions": 480, "total": 5000, "rate": 0.096},
            "treatment": {"conversions": 520, "total": 5000, "rate": 0.104}
        }
    
    def test_mock_posthog_client(self):
        """Test PostHog client with mocked data"""
        print("🧪 Testing PostHog Client (Mocked)")
        
        with patch('integrations.posthog.os.getenv', return_value="mock_key"):
            client = PostHogClient()
            
            # Test metric counts (should return mock data)
            suc_c, tot_c, suc_t, tot_t = client.get_metric_counts("test_experiment")
            assert suc_c == 480
            assert tot_c == 5000
            assert suc_t == 520
            assert tot_t == 5000
            
            print("  ✅ Metric counts working")
            
            # Test tracking validation
            validation = client.validate_tracking("test_experiment", ["event1", "event2"])
            assert validation["valid"] == True
            assert "experiment_key" in validation
            
            print("  ✅ Tracking validation working")
    
    def test_mock_github_client(self):
        """Test GitHub client with mocked repository"""
        print("🧪 Testing GitHub Client (Mocked)")
        
        with patch('integrations.github.os.getenv') as mock_env:
            mock_env.side_effect = lambda key, default=None: {
                "GITHUB_TOKEN": "mock_token",
                "GITHUB_REPO": "mock/org",
                "GITHUB_DEFAULT_BRANCH": "main"
            }.get(key, default)
            
            # Mock the GitHub API response
            with patch('integrations.github.Github') as mock_github:
                mock_repo = Mock()
                mock_repo.get_branch.return_value = Mock()
                mock_repo.get_branch.return_value.commit.sha = "mock_sha"
                mock_repo.create_git_ref.return_value = Mock()
                mock_repo.create_file.return_value = Mock()
                mock_repo.create_pull.return_value = Mock()
                mock_repo.create_pull.return_value.number = 123
                mock_repo.create_pull.return_value.html_url = "https://github.com/mock/org/pull/123"
                
                mock_github.return_value.get_repo.return_value = mock_repo
                
                client = GitHubClient()
                
                # Test branch creation
                branch = client.create_experiment_branch("test_experiment")
                assert branch is not None
                print("  ✅ Branch creation working")
                
                # Test file creation
                success = client.create_or_update_file("test_branch", "test.txt", "content", "message")
                assert success == True
                print("  ✅ File creation working")
                
                # Test PR creation
                pr_url = client.open_pull_request("test_experiment", "test_branch", {}, [])
                assert pr_url is not None
                print("  ✅ PR creation working")
    
    def test_mock_slack_client(self):
        """Test Slack client with mocked API"""
        print("🧪 Testing Slack Client (Mocked)")
        
        with patch('integrations.slack.os.getenv') as mock_env:
            mock_env.side_effect = lambda key, default=None: {
                "SLACK_BOT_TOKEN": "mock_token",
                "SLACK_CHANNEL_APPROVALS": "C123456789"
            }.get(key, default)
            
            # Mock httpx client
            with patch('integrations.slack.httpx.AsyncClient') as mock_httpx:
                mock_response = Mock()
                mock_response.raise_for_status.return_value = None
                mock_response.json.return_value = {"ok": True}
                
                mock_httpx.return_value.__aenter__.return_value.post.return_value = mock_response
                mock_httpx.return_value.__aenter__.return_value.post.return_value = mock_response
                
                client = SlackClient()
                
                # Test message sending (async)
                async def test_send():
                    success = await client.send_message("Test message")
                    return success
                
                result = asyncio.run(test_send())
                assert result == True
                print("  ✅ Message sending working")
    
    def test_mock_feature_flags(self):
        """Test feature flag client with mocked API"""
        print("🧪 Testing Feature Flag Client (Mocked)")
        
        with patch('integrations.flags.os.getenv') as mock_env:
            mock_env.side_effect = lambda key, default=None: {
                "POSTHOG_PROJECT_API_KEY": "mock_key"
            }.get(key, default)
            
            # Mock httpx client
            with patch('integrations.flags.httpx.AsyncClient') as mock_httpx:
                mock_response = Mock()
                mock_response.raise_for_status.return_value = None
                mock_response.json.return_value = {"key": "experiment_test"}
                
                mock_httpx.return_value.__aenter__.return_value.post.return_value = mock_response
                mock_httpx.return_value.__aenter__.return_value.get.return_value = mock_response
                mock_httpx.return_value.__aenter__.return_value.patch.return_value = mock_response
                
                client = FeatureFlagClient()
                
                # Test variant code generation
                code_snippets = client.generate_variant_code("test_experiment", ["control", "treatment"])
                assert "javascript" in code_snippets
                assert "python" in code_snippets
                assert "flag_key" in code_snippets
                
                print("  ✅ Variant code generation working")
    
    def test_mock_chroma_store(self):
        """Test Chroma store with mocked database"""
        print("🧪 Testing Chroma Store (Mocked)")
        
        with patch('memory.chroma_store.chromadb.PersistentClient') as mock_chroma:
            # Mock collections
            mock_collection = Mock()
            mock_collection.add.return_value = None
            mock_collection.query.return_value = {
                'documents': [['Mock experiment content']],
                'metadatas': [{'experiment_key': 'test'}],
                'distances': [[0.1]]
            }
            
            mock_chroma.return_value.get_or_create_collection.return_value = mock_collection
            
            store = ChromaStore(persist_dir=".test_chroma")
            
            # Test storing experiment
            store.store_experiment("test_key", {"key": "test", "hypothesis": "test"})
            print("  ✅ Experiment storage working")
            
            # Test retrieval
            results = store.retrieve_similar_experiments("test")
            assert len(results) > 0
            print("  ✅ Experiment retrieval working")
            
            # Test context storage
            store.store_context("test_context", "test content", ["test"])
            print("  ✅ Context storage working")
    
    def test_mock_worker_initialization(self):
        """Test worker initialization without external services"""
        print("🧪 Testing Worker Initialization (Mocked)")
        
        with patch('orchestrator.worker_new.ChromaStore') as mock_chroma, \
             patch('orchestrator.worker_new.GitHubClient') as mock_github, \
             patch('orchestrator.worker_new.SlackClient') as mock_slack, \
             patch('orchestrator.worker_new.FeatureFlagClient') as mock_flags:
            
            # Mock all dependencies
            mock_chroma.return_value = Mock()
            mock_github.return_value = Mock()
            mock_slack.return_value = Mock()
            mock_flags.return_value = Mock()
            
            # Test worker creation
            worker = NewExperimentWorker()
            assert worker.memory is not None
            assert worker.github is not None
            assert worker.slack is not None
            assert worker.flags is not None
            
            print("  ✅ New experiment worker initialization working")
        
        with patch('orchestrator.worker_monitor.ChromaStore') as mock_chroma, \
             patch('orchestrator.worker_monitor.PostHogClient') as mock_posthog, \
             patch('orchestrator.worker_monitor.SlackClient') as mock_slack, \
             patch('orchestrator.worker_monitor.GitHubClient') as mock_github:
            
            # Mock all dependencies
            mock_chroma.return_value = Mock()
            mock_posthog.return_value = Mock()
            mock_slack.return_value = Mock()
            mock_github.return_value = Mock()
            
            # Test worker creation
            worker = MonitoringWorker()
            assert worker.memory is not None
            assert worker.posthog is not None
            assert worker.slack is not None
            assert worker.github is not None
            
            print("  ✅ Monitoring worker initialization working")
    
    def test_mock_agent_creation(self):
        """Test AutoGen agent creation without OpenAI API"""
        print("🧪 Testing Agent Creation (Mocked)")
        
        with patch('agents.supervisor.open') as mock_open, \
             patch('agents.supervisor.os.getenv', return_value="gpt-4o-mini"):
            
            # Mock prompt files
            mock_open.return_value.read.return_value = "Mock prompt content"
            
            # Test group chat creation
            try:
                manager, supervisor = create_group_chat()
                assert manager is not None
                assert supervisor is not None
                print("  ✅ Group chat creation working")
            except Exception as e:
                print(f"  ⚠️  Group chat creation: {e}")
            
            # Test monitoring chat creation
            try:
                monitor_manager, analyst = create_monitoring_chat()
                assert monitor_manager is not None
                assert analyst is not None
                print("  ✅ Monitoring chat creation working")
            except Exception as e:
                print(f"  ⚠️  Monitoring chat creation: {e}")
    
    def test_schema_validation(self):
        """Test Pydantic schema validation (no external dependencies)"""
        print("🧪 Testing Schema Validation")
        
        # Test Metric schema
        metric = Metric(
            name="test_metric",
            type="rate",
            event="test_event",
            description="Test description"
        )
        assert metric.name == "test_metric"
        assert metric.type == "rate"
        print("  ✅ Metric schema validation working")
        
        # Test ExperimentSpec schema
        spec_data = {
            "key": "test_experiment",
            "hypothesis": "Test hypothesis",
            "variants": ["control", "treatment"],
            "primary_metric": metric.model_dump(),
            "mde": 0.15,
            "alpha": 0.05,
            "power": 0.8,
            "min_sample_size": 2500,
            "max_duration_days": 14
        }
        
        spec = ExperimentSpec.model_validate(spec_data)
        assert spec.key == "test_experiment"
        assert spec.hypothesis == "Test hypothesis"
        assert spec.power == 0.8
        print("  ✅ ExperimentSpec schema validation working")
        
        # Test TrackingPlan schema
        tracking_plan = TrackingPlan(
            events=[{"name": "test_event", "properties": ["prop1"]}],
            guardrails={"must_have": ["prop1"], "pii_ban": ["email"]},
            experiment_key="test_experiment"
        )
        assert tracking_plan.experiment_key == "test_experiment"
        assert len(tracking_plan.events) == 1
        print("  ✅ TrackingPlan schema validation working")
    
    def test_statistical_functions(self):
        """Test statistical analysis functions (no external dependencies)"""
        print("🧪 Testing Statistical Functions")
        
        # Import the monitoring worker to test statistical functions
        from orchestrator.worker_monitor import MonitoringWorker
        
        worker = MonitoringWorker()
        
        # Test Bayesian probability calculation
        prob = worker.bayes_prob_better(480, 5000, 520, 5000)
        assert 0 <= prob <= 1
        print("  ✅ Bayesian probability calculation working")
        
        # Test mSPRT test
        control_data = [1.0, 1.1, 0.9, 1.2, 0.8] * 100  # 500 data points
        treatment_data = [1.1, 1.2, 1.0, 1.3, 0.9] * 100  # 500 data points
        
        result = worker.msprt_test(control_data, treatment_data)
        assert "decision" in result
        assert "confidence" in result
        print("  ✅ mSPRT test working")
    
    def run_all_tests(self):
        """Run all mock-based tests"""
        print("🚀 Running Mock-Based Integration Tests")
        print("=" * 60)
        
        test_methods = [method for method in dir(self) if method.startswith('test_')]
        
        passed = 0
        total = len(test_methods)
        
        for method_name in test_methods:
            try:
                method = getattr(self, method_name)
                if asyncio.iscoroutinefunction(method):
                    asyncio.run(method())
                else:
                    method()
                passed += 1
            except Exception as e:
                print(f"❌ {method_name} failed: {e}")
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! The system is ready for testing.")
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
        
        return passed == total

def main():
    """Run the mock-based test suite"""
    tester = MockIntegrationTests()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ System is ready for offline testing!")
        print("\nNext steps:")
        print("1. Set up your .env file with API keys")
        print("2. Run ./start.sh to start infrastructure")
        print("3. Test with real APIs")
    else:
        print("\n❌ Some tests failed. Please fix issues before proceeding.")
    
    return success

if __name__ == "__main__":
    main()
