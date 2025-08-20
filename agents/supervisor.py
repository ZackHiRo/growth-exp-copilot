from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
import os
from loguru import logger

def load_prompt(filename: str) -> str:
    """Load prompt from prompts directory"""
    try:
        with open(f"prompts/{filename}", "r") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Prompt file {filename} not found")
        return ""

def create_agents():
    """Create and configure all AutoGen agents"""
    
    # LLM configuration
    llm_cfg = {
        "config_list": [{"model": os.getenv("MODEL_NAME", "gpt-4o-mini")}],
        "temperature": 0
    }
    
    # Supervisor - orchestrates the conversation
    supervisor = AssistantAgent(
        name="Supervisor",
        system_message=load_prompt("supervisor.md"),
        llm_config=llm_cfg,
        human_input_mode="NEVER"
    )
    
    # Designer - creates experiment specifications
    designer = AssistantAgent(
        name="Designer",
        system_message=load_prompt("designer.md"),
        llm_config=llm_cfg,
        human_input_mode="NEVER"
    )
    
    # Policy - validates safety and compliance
    policy = AssistantAgent(
        name="Policy",
        system_message=load_prompt("policy.md"),
        llm_config=llm_cfg,
        human_input_mode="NEVER"
    )
    
    # Implementer - generates code and tracking plans
    implementer = AssistantAgent(
        name="Implementer",
        system_message=load_prompt("implementer.md"),
        llm_config=llm_cfg,
        human_input_mode="NEVER"
    )
    
    # Analyst - analyzes results (used later in monitoring)
    analyst = AssistantAgent(
        name="Analyst",
        system_message=load_prompt("analyst.md"),
        llm_config=llm_cfg,
        human_input_mode="NEVER"
    )
    
    return supervisor, designer, policy, implementer, analyst

def create_group_chat():
    """Create the group chat for experiment planning"""
    supervisor, designer, policy, implementer, analyst = create_agents()
    
    # Create group chat for experiment planning (Designer -> Policy -> Implementer)
    gc = GroupChat(
        agents=[supervisor, designer, policy, implementer],
        messages=[],
        max_round=12
    )
    
    # Create manager to handle the conversation
    manager = GroupChatManager(
        groupchat=gc,
        llm_config={"config_list": [{"model": os.getenv("MODEL_NAME", "gpt-4o-mini")}]}
    )
    
    return manager, supervisor

def create_monitoring_chat():
    """Create a simple chat for the analyst to make decisions"""
    supervisor, designer, policy, implementer, analyst = create_agents()
    
    # Simple chat between supervisor and analyst for monitoring decisions
    gc = GroupChat(
        agents=[supervisor, analyst],
        messages=[],
        max_round=3
    )
    
    manager = GroupChatManager(
        groupchat=gc,
        llm_config={"config_list": [{"model": os.getenv("MODEL_NAME", "gpt-4o-mini")}]}
    )
    
    return manager, analyst
