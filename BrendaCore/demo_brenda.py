#!/usr/bin/env python3
"""
BrendaCore Demo Script
Quick demonstration of Brenda's capabilities
"""

import time
import sys
from core import BrendaAgent

def print_header():
    print("\n" + "="*60)
    print("  BRENDACORE DEMO - Your Sassy AI Project Manager")
    print("="*60 + "\n")

def demo_sass_levels(brenda):
    """Demonstrate sass level changes"""
    print("\n📊 DEMO: Sass Level Progression\n")
    
    levels = [1, 5, 8, 11]
    for level in levels:
        brenda.sass_engine.set_sass_level(level)
        response = brenda.respond_to_human(f"How's the project going?")
        print(f"Sass Level {level}: {response.message}\n")
        time.sleep(1)

def demo_agent_management(brenda):
    """Demonstrate agent management"""
    print("\n🤖 DEMO: Agent Management\n")
    
    # Register some agents
    agents = [
        ("qa-bot", "quality", "Testing automation bot"),
        ("doc-writer", "documentation", "Documentation generator"),
        ("deploy-bot", "deployment", "Deployment automation")
    ]
    
    for agent_id, agent_type, description in agents:
        response = brenda.register_agent(agent_id, agent_type, {"description": description})
        print(f"Registered: {agent_id}")
        print(f"Brenda says: {response.message}\n")
        time.sleep(1)
    
    # Assign a task
    print("\n📋 Assigning task to agents...")
    response = brenda.assign_task(
        task_id="demo-001",
        description="Fix the critical bug in production",
        agent_ids=["qa-bot", "deploy-bot"],
        priority=9
    )
    print(f"Task assigned: {response.message}\n")

def demo_crisis_mode(brenda):
    """Demonstrate crisis mode"""
    print("\n🚨 DEMO: Crisis Mode Activation\n")
    
    # Set to crisis level
    brenda.sass_engine.set_sass_level(11)
    
    # Trigger crisis responses
    crisis_queries = [
        "The production server is down!",
        "We lost all the data!",
        "The client is furious!"
    ]
    
    for query in crisis_queries:
        response = brenda.respond_to_human(query)
        print(f"Human: {query}")
        print(f"Brenda: {response.message}\n")
        time.sleep(1)

def demo_memory_persistence(brenda):
    """Demonstrate memory system"""
    print("\n🧠 DEMO: Memory System\n")
    
    # Add some interactions
    interactions = [
        ("Where's the documentation?", "probably where you left it"),
        ("Can you help with testing?", "I can help by telling you to test better"),
        ("The deadline is tomorrow!", "And whose fault is that?")
    ]
    
    for human_msg, brenda_response in interactions:
        brenda.memory.add_interaction("human", human_msg, {"timestamp": time.time()})
        brenda.memory.add_interaction("brenda", brenda_response, {"sass_level": 7})
    
    # Show recent interactions
    recent = brenda.memory.get_recent_interactions(3)
    print(f"Recent interactions in memory: {len(recent)}")
    for interaction in recent:
        print(f"  - {interaction['role']}: {interaction['content'][:50]}...")

def main():
    """Run the demo"""
    print_header()
    
    # Initialize Brenda
    print("🚀 Initializing BrendaCore...\n")
    brenda = BrendaAgent()
    
    # Run demo scenarios
    demos = [
        ("Sass Levels", demo_sass_levels),
        ("Agent Management", demo_agent_management),
        ("Crisis Mode", demo_crisis_mode),
        ("Memory System", demo_memory_persistence)
    ]
    
    for demo_name, demo_func in demos:
        print(f"\n{'='*60}")
        input(f"Press Enter to demo: {demo_name}")
        try:
            demo_func(brenda)
        except Exception as e:
            print(f"Demo error: {e}")
            continue
    
    print("\n" + "="*60)
    print("  DEMO COMPLETE - Questions?")
    print("="*60 + "\n")
    
    # Save memory before exit
    brenda.memory.save_to_file()
    print("Memory saved. Brenda out. *mic drop*")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Brenda is not amused.")
        sys.exit(0)