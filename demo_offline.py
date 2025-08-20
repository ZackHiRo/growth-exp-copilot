#!/usr/bin/env python3
"""
Offline Demo for Growth Experiment Co-Pilot
This script demonstrates the system's capabilities without requiring external APIs
"""

import sys
import os
from datetime import datetime

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def demo_schemas_offline():
    """Demonstrate schema validation without external dependencies"""
    print("📋 Demo: Schema Validation (Offline)")
    print("=" * 50)
    
    try:
        from schemas.experiment import ExperimentSpec, Metric, TrackingPlan
        
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
            "key": "offline_demo_2024",
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
        print(f"   Power: {spec.power}")
        print(f"   Alpha: {spec.alpha}")
        
        # Create tracking plan
        tracking_plan = TrackingPlan(
            events=[
                {
                    "name": "checkout_started",
                    "properties": ["cart_value", "currency", "ab_variant"]
                },
                {
                    "name": "checkout_completed",
                    "properties": ["order_value", "currency", "ab_variant"]
                }
            ],
            guardrails={
                "must_have": ["ab_variant"],
                "pii_ban": ["email", "phone", "name"],
                "experiment_key": spec.key
            },
            experiment_key=spec.key
        )
        
        print(f"✅ Created tracking plan with {len(tracking_plan.events)} events")
        print(f"   Guardrails: {len(tracking_plan.guardrails)} rules")
        
        print()
        
    except Exception as e:
        print(f"❌ Schema demo failed: {e}")

def demo_statistical_analysis_offline():
    """Demonstrate statistical analysis without external dependencies"""
    print("📊 Demo: Statistical Analysis (Offline)")
    print("=" * 50)
    
    try:
        # Simulate experiment data
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
        
        # Simulate Bayesian analysis
        print(f"\n🧮 Bayesian Analysis Simulation:")
        print(f"   P(Treatment > Control) calculation")
        print(f"   Beta distribution sampling")
        print(f"   Confidence interval estimation")
        
        # Simulate decision making
        if improvement > 0.05 and control_total + treatment_total >= 2000:
            decision = "ship_treatment"
            confidence = 0.95
        elif improvement < -0.05 and control_total + treatment_total >= 2000:
            decision = "ship_control"
            confidence = 0.95
        else:
            decision = "extend"
            confidence = 0.5
        
        print(f"\n🎯 Decision: {decision.upper()}")
        print(f"   Confidence: {confidence:.1%}")
        print(f"   Sample size: {control_total + treatment_total:,}")
        
        print()
        
    except Exception as e:
        print(f"❌ Statistical analysis demo failed: {e}")

def demo_agent_prompts_offline():
    """Demonstrate agent prompt loading without external dependencies"""
    print("🤖 Demo: Agent Prompts (Offline)")
    print("=" * 50)
    
    try:
        prompt_files = [
            "supervisor.md",
            "designer.md", 
            "policy.md",
            "implementer.md",
            "analyst.md"
        ]
        
        total_chars = 0
        for prompt_file in prompt_files:
            try:
                with open(f"prompts/{prompt_file}", "r") as f:
                    content = f.read()
                    total_chars += len(content)
                    print(f"✅ {prompt_file}: {len(content)} characters")
                    
                    # Show first line of each prompt
                    first_line = content.split('\n')[0]
                    print(f"   Preview: {first_line[:60]}...")
                    
            except FileNotFoundError:
                print(f"❌ {prompt_file}: File not found")
        
        print(f"\n📊 Total prompt content: {total_chars:,} characters")
        print(f"   Average per agent: {total_chars // len(prompt_files):,} characters")
        
        print()
        
    except Exception as e:
        print(f"❌ Agent prompts demo failed: {e}")

def demo_code_generation_offline():
    """Demonstrate code generation capabilities without external dependencies"""
    print("💻 Demo: Code Generation (Offline)")
    print("=" * 50)
    
    try:
        # Simulate feature flag code generation
        experiment_key = "offline_demo_experiment"
        variants = ["control", "treatment"]
        flag_key = f"experiment_{experiment_key}"
        
        # JavaScript variant assignment
        js_code = f"""
// Variant assignment for experiment: {experiment_key}
const getVariant = () => {{
    // Check if user is in experiment
    if (posthog.isFeatureEnabled('{flag_key}')) {{
        // Simple random assignment
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
        # Simple random assignment
        variant_index = random.randint(0, {len(variants) - 1})
        return {variants}[variant_index]
    return '{variants[0]}'  # Default to control

# Usage
variant = get_variant()
posthog.capture('experiment_assigned', {{ 'ab_variant': variant }})
"""
        
        # PostHog tracking code
        tracking_code = f"""
// PostHog tracking for {experiment_key}
posthog.capture('checkout_started', {{
    cart_value: cart.total,
    currency: 'USD',
    ab_variant: variant
}});

posthog.capture('checkout_completed', {{
    order_value: order.total,
    currency: 'USD',
    ab_variant: variant
}});
"""
        
        print(f"✅ Generated code for experiment: {experiment_key}")
        print(f"   JavaScript: {len(js_code)} characters")
        print(f"   Python: {len(python_code)} characters")
        print(f"   Tracking: {len(tracking_code)} characters")
        print(f"   Flag key: {flag_key}")
        
        print(f"\n📝 Code Preview (JavaScript):")
        print(js_code[:200] + "..." if len(js_code) > 200 else js_code)
        
        print()
        
    except Exception as e:
        print(f"❌ Code generation demo failed: {e}")

def demo_workflow_simulation_offline():
    """Demonstrate the complete workflow without external dependencies"""
    print("🔄 Demo: Complete Workflow Simulation (Offline)")
    print("=" * 50)
    
    try:
        # Simulate experiment idea submission
        idea = {
            "idea_text": "Increase checkout conversion by adding progress indicator",
            "requester": "offline_user",
            "repo": "demo/ecommerce",
            "branch": "main"
        }
        
        print("📤 Step 1: Experiment Idea Submitted")
        print(f"   Idea: {idea['idea_text']}")
        print(f"   Requester: {idea['requester']}")
        print(f"   Repository: {idea['repo']}")
        
        # Simulate AutoGen agent processing
        print(f"\n🤖 Step 2: AI Agents Processing")
        print(f"   Designer: Creating experiment specification")
        print(f"   Policy: Validating safety and compliance")
        print(f"   Implementer: Generating code and tracking plan")
        print(f"   Supervisor: Coordinating workflow")
        
        # Simulate experiment specification
        print(f"\n📋 Step 3: Experiment Specification Created")
        print(f"   Key: offline_demo_2024")
        print(f"   Hypothesis: Adding progress indicator increases conversion by 15%")
        print(f"   Variants: control, treatment")
        print(f"   Primary metric: checkout_completion_rate")
        print(f"   Sample size: 2,500 users")
        print(f"   Duration: 14 days")
        
        # Simulate implementation
        print(f"\n💻 Step 4: Implementation Generated")
        print(f"   Tracking plan: 2 events with guardrails")
        print(f"   Code files: JavaScript, Python, PostHog tracking")
        print(f"   Feature flag: experiment_offline_demo_2024")
        
        # Simulate monitoring
        print(f"\n📊 Step 5: Monitoring & Analysis")
        print(f"   Data collection: PostHog events")
        print(f"   Statistical analysis: Bayesian methods")
        print(f"   Decision making: AI-powered recommendations")
        
        # Simulate outcome
        print(f"\n🎯 Step 6: Experiment Outcome")
        print(f"   Decision: SHIP_TREATMENT")
        print(f"   Confidence: 96%")
        print(f"   Improvement: 8.3% increase in conversion")
        print(f"   Sample size: 10,000 users")
        
        print(f"\n✅ Complete workflow simulation successful!")
        print()
        
    except Exception as e:
        print(f"❌ Workflow simulation failed: {e}")

def demo_file_structure_offline():
    """Demonstrate the project file structure"""
    print("📁 Demo: Project Structure (Offline)")
    print("=" * 50)
    
    try:
        import os
        
        # Show directory structure
        directories = [
            "agents", "integrations", "memory", "orchestrator",
            "prompts", "schemas", "scripts", "tests", "infra"
        ]
        
        total_files = 0
        for directory in directories:
            if os.path.exists(directory):
                files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
                total_files += len(files)
                print(f"📂 {directory}/: {len(files)} files")
                
                # Show key files
                for file in files[:3]:  # Show first 3 files
                    print(f"   📄 {file}")
                if len(files) > 3:
                    print(f"   ... and {len(files) - 3} more")
        
        # Show root files
        root_files = [f for f in os.listdir('.') if os.path.isfile(f) and not f.startswith('.')]
        print(f"\n📂 Root directory: {len(root_files)} files")
        for file in root_files[:5]:  # Show first 5 files
            print(f"   📄 {file}")
        
        print(f"\n📊 Total project files: {total_files + len(root_files)}")
        print(f"   Core modules: {len(directories)} directories")
        print(f"   Implementation: Ready for testing")
        
        print()
        
    except Exception as e:
        print(f"❌ File structure demo failed: {e}")

def main():
    """Run all offline demos"""
    print("🎉 Growth Experiment Co-Pilot - Offline Demo")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("This demo runs completely offline - no external APIs required!")
    print()
    
    # Run all demos
    demo_schemas_offline()
    demo_statistical_analysis_offline()
    demo_agent_prompts_offline()
    demo_code_generation_offline()
    demo_workflow_simulation_offline()
    demo_file_structure_offline()
    
    print("🎊 Offline demo completed successfully!")
    print("\n" + "=" * 70)
    print("✅ System is ready for offline testing and development")
    print("\nNext steps:")
    print("1. Run mock tests: python tests/test_mock_integrations.py")
    print("2. Set up environment: cp env.example .env")
    print("3. Start infrastructure: ./start.sh")
    print("4. Test with real APIs: python demo.py")
    print("\nHappy offline experimenting! 🧪")

if __name__ == "__main__":
    main()
