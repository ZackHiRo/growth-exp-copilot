#!/usr/bin/env python3
"""
Demo script for the Growth Experiment Co-Pilot
This script demonstrates the key features of the system
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory.chroma_store import ChromaStore
from integrations.posthog import PostHogClient
from integrations.github import GitHubClient
from integrations.slack import SlackClient
from integrations.flags import FeatureFlagClient
from schemas.experiment import ExperimentSpec, Metric

async def demo_chroma_store():
    """Demonstrate Chroma memory store functionality"""
    print("🧠 Demo: Chroma Memory Store")
    print("=" * 50)
    
    try:
        store = ChromaStore()
        
        # Seed with examples
        store.seed_with_examples()
        print("✅ Seeded memory store with example data")
        
        # Retrieve similar experiments
        results = store.retrieve_similar_experiments("checkout conversion")
        print(f"✅ Found {len(results)} similar experiments")
        
        for i, result in enumerate(results[:2], 1):
            print(f"  {i}. {result['content'][:100]}...")
        
        print()
        
    except Exception as e:
        print(f"❌ Chroma store demo failed: {e}")

def demo_schemas():
    """Demonstrate Pydantic schema validation"""
    print("📋 Demo: Schema Validation")
    print("=" * 50)
    
    try:
        # Create a metric
        metric = Metric(
            name="checkout_conversion_rate",
            type="rate",
            event="checkout_completed",
            description="Percentage of users who complete checkout"
        )
        print(f"✅ Created metric: {metric.name}")
        
        # Create experiment spec
        spec_data = {
            "key": "demo_checkout_2024",
            "hypothesis": "Adding progress indicator will increase checkout completion by 15%",
            "variants": ["control", "treatment"],
            "primary_metric": metric.model_dump(),
            "mde": 0.15,
            "alpha": 0.05,
            "power": 0.8,
            "min_sample_size": 2500,
            "max_duration_days": 14
        }
        
        spec = ExperimentSpec.model_validate(spec_data)
        print(f"✅ Created experiment: {spec.key}")
        print(f"   Hypothesis: {spec.hypothesis}")
        print(f"   Sample size: {spec.min_sample_size:,}")
        print(f"   Duration: {spec.max_duration_days} days")
        
        print()
        
    except Exception as e:
        print(f"❌ Schema demo failed: {e}")

async def demo_integrations():
    """Demonstrate integration clients"""
    print("🔌 Demo: Integration Clients")
    print("=" * 50)
    
    try:
        # PostHog client
        posthog = PostHogClient()
        suc_c, tot_c, suc_t, tot_t = posthog.get_metric_counts("demo_experiment")
        print(f"✅ PostHog client: Control {suc_c}/{tot_c}, Treatment {suc_t}/{tot_t}")
        
        # GitHub client
        github = GitHubClient()
        if github.repo:
            print(f"✅ GitHub client: Connected to {github.repo_name}")
        else:
            print("⚠️  GitHub client: No credentials configured")
        
        # Slack client
        slack = SlackClient()
        print("✅ Slack client: Initialized")
        
        # Feature flags client
        flags = FeatureFlagClient()
        code_snippets = flags.generate_variant_code("demo_experiment", ["control", "treatment"])
        print(f"✅ Feature flags: Generated code for {len(code_snippets)} languages")
        
        print()
        
    except Exception as e:
        print(f"❌ Integrations demo failed: {e}")

def demo_agent_prompts():
    """Demonstrate agent prompt loading"""
    print("🤖 Demo: Agent Prompts")
    print("=" * 50)
    
    try:
        prompt_files = [
            "supervisor.md",
            "designer.md", 
            "policy.md",
            "implementer.md",
            "analyst.md"
        ]
        
        for prompt_file in prompt_files:
            try:
                with open(f"prompts/{prompt_file}", "r") as f:
                    content = f.read()
                    print(f"✅ {prompt_file}: {len(content)} characters")
            except FileNotFoundError:
                print(f"❌ {prompt_file}: File not found")
        
        print()
        
    except Exception as e:
        print(f"❌ Agent prompts demo failed: {e}")

async def demo_rabbitmq_simulation():
    """Simulate RabbitMQ message flow"""
    print("🐰 Demo: RabbitMQ Message Flow")
    print("=" * 50)
    
    try:
        # Simulate experiment idea
        idea = {
            "idea_text": "Increase engagement by adding social proof elements",
            "requester": "demo_user",
            "repo": "demo/landing",
            "branch": "main"
        }
        
        print("📤 Simulating message enqueue:")
        print(f"   Idea: {idea['idea_text'][:50]}...")
        print(f"   Requester: {idea['requester']}")
        print(f"   Repo: {idea['repo']}")
        
        # Simulate processing
        print("\n⚙️  Simulating processing:")
        print("   1. Designer creates experiment spec")
        print("   2. Policy validates safety")
        print("   3. Implementer generates code")
        print("   4. GitHub PR created")
        print("   5. Monitoring begins")
        
        print("\n✅ Message flow simulation completed")
        print()
        
    except Exception as e:
        print(f"❌ RabbitMQ demo failed: {e}")

def demo_statistical_analysis():
    """Demonstrate statistical analysis capabilities"""
    print("📊 Demo: Statistical Analysis")
    print("=" * 50)
    
    try:
        # Sample data
        control_conversions = 480
        control_total = 5000
        treatment_conversions = 520
        treatment_total = 5000
        
        control_rate = control_conversions / control_total
        treatment_rate = treatment_conversions / treatment_total
        
        improvement = (treatment_rate - control_rate) / control_rate
        
        print(f"📈 Sample Experiment Results:")
        print(f"   Control: {control_conversions}/{control_total} = {control_rate:.1%}")
        print(f"   Treatment: {treatment_conversions}/{treatment_total} = {treatment_rate:.1%}")
        print(f"   Improvement: {improvement:.1%}")
        
        # Statistical thresholds
        print(f"\n🎯 Decision Framework:")
        print(f"   Minimum sample size: 2,000")
        print(f"   Confidence threshold: 95%")
        print(f"   Power requirement: ≥80%")
        print(f"   Alpha level: 5%")
        
        print("\n✅ Statistical analysis demo completed")
        print()
        
    except Exception as e:
        print(f"❌ Statistical analysis demo failed: {e}")

async def main():
    """Run all demos"""
    print("🎉 Growth Experiment Co-Pilot Demo")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run demos
    await demo_chroma_store()
    demo_schemas()
    await demo_integrations()
    demo_agent_prompts()
    await demo_rabbitmq_simulation()
    demo_statistical_analysis()
    
    print("🎊 Demo completed successfully!")
    print("\nTo run the full system:")
    print("1. ./start.sh                    # Start infrastructure")
    print("2. uvicorn app:app --reload      # Start API server")
    print("3. python orchestrator/worker_new.py      # Start new experiment worker")
    print("4. python orchestrator/worker_monitor.py  # Start monitoring worker")
    print("\nHappy experimenting! 🧪")

if __name__ == "__main__":
    asyncio.run(main())
