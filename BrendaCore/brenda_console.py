#!/usr/bin/env python3
"""
Brenda Console - Interactive console for testing BrendaCore
"""

import asyncio
import cmd
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from BrendaCore.core import BrendaAgent, SassEngine, MemoryStore
from BrendaCore.core.brenda_agent import EscalationReason, ProjectHealth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BrendaConsole(cmd.Cmd):
    """Interactive console for Brenda"""
    
    intro = """
    ╔══════════════════════════════════════════════════════════════╗
    ║  Welcome to The Loom - Brenda PM Console v0.1.0             ║
    ║  Type 'help' for commands or 'sass' for a taste of attitude ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    
    prompt = "brenda> "
    
    def __init__(self):
        super().__init__()
        self.brenda = BrendaAgent()
        self.mock_agents = {}
        self._setup_mock_agents()
        
        # Print initial sass
        print(f"\n{self.brenda.sass_engine.get_contextual_quip('general')}\n")
    
    def _setup_mock_agents(self):
        """Set up mock agents for testing"""
        mock_agent_ids = [
            "agent-001-coder",
            "agent-002-tester",
            "agent-003-reviewer",
            "agent-004-deployer"
        ]
        
        for agent_id in mock_agent_ids:
            self.brenda.register_agent(agent_id, {
                "type": agent_id.split("-")[-1],
                "capabilities": ["coding", "testing", "review"],
                "created": datetime.now().isoformat()
            })
            self.mock_agents[agent_id] = {"status": "idle", "task": None}
    
    def do_status(self, arg):
        """Check status of all agents: status"""
        status = self.brenda.monitor_agents()
        
        print("\n" + "="*60)
        print(f"FACTORY STATUS REPORT - {status['timestamp']}")
        print("="*60)
        print(f"Total Agents: {status['total_agents']}")
        print(f"Sass Level: {self.brenda.sass_engine.sass_level}/11")
        print(f"Project Health: {self.brenda.project_health.name}")
        print("-"*60)
        
        for agent_id, agent_status in status['agent_statuses'].items():
            reliability = agent_status['reliability_score']
            strikes = agent_status['strike_count']
            status_icon = "✓" if reliability > 0.7 else "⚠" if reliability > 0.5 else "✗"
            
            print(f"{status_icon} {agent_id}:")
            print(f"  Status: {agent_status['status']}")
            print(f"  Reliability: {reliability:.1%}")
            print(f"  Strikes: {strikes}/3")
            
            if 'sass_note' in agent_status:
                print(f"  📢 {agent_status['sass_note']}")
        
        print("-"*60)
        print(f"Summary: {status['overall_sass']}\n")
    
    def do_assign(self, arg):
        """Assign task to agent: assign <agent_id> <task_description>"""
        parts = arg.split(maxsplit=1)
        if len(parts) < 2:
            print("Usage: assign <agent_id> <task_description>")
            return
        
        agent_id, task = parts
        
        if agent_id not in self.mock_agents:
            print(f"Unknown agent: {agent_id}")
            print(f"Available agents: {', '.join(self.mock_agents.keys())}")
            return
        
        # Send task assignment
        request = {
            "type": "task_assignment",
            "sender": "console",
            "task": task,
            "target_agent": agent_id
        }
        
        response = asyncio.run(self.brenda.process_request(request))
        
        print(f"\n{response.message}")
        if response.metadata.get('sass_quip'):
            print(f"💬 {response.metadata['sass_quip']}\n")
    
    def do_escalate(self, arg):
        """Trigger escalation: escalate <reason> [context]"""
        parts = arg.split(maxsplit=1)
        if not parts:
            print("Available escalation reasons:")
            for reason in EscalationReason:
                print(f"  - {reason.value}")
            return
        
        reason_str = parts[0]
        context = parts[1] if len(parts) > 1 else "Manual escalation from console"
        
        # Find matching escalation reason
        try:
            reason = EscalationReason(reason_str)
        except ValueError:
            print(f"Invalid reason. Available: {', '.join(r.value for r in EscalationReason)}")
            return
        
        # Send escalation request
        request = {
            "type": "escalation",
            "sender": "console",
            "reason": reason.value,
            "context": {"message": context, "timestamp": datetime.now().isoformat()}
        }
        
        response = asyncio.run(self.brenda.process_request(request))
        
        print(f"\n🚨 ESCALATION TRIGGERED 🚨")
        print(f"{response.message}")
        if response.data:
            print(f"Escalation ID: {response.data.get('escalation_id')}")
            print(f"Priority: {response.data.get('priority')}/10")
        if response.metadata.get('sass_quip'):
            print(f"💬 {response.metadata['sass_quip']}\n")
    
    def do_sass(self, arg):
        """Get a sass quip: sass [level]"""
        if arg:
            try:
                level = int(arg)
                self.brenda.sass_engine.set_sass_level(level)
                print(f"Sass level set to {level}")
            except ValueError:
                print("Invalid sass level. Use a number 1-11")
        
        quip = self.brenda.sass_engine.get_contextual_quip("general")
        print(f"\n💬 {quip}")
        print(f"(Current sass level: {self.brenda.sass_engine.sass_level}/11)\n")
    
    def do_metrics(self, arg):
        """Show performance metrics: metrics"""
        metrics = self.brenda.get_metrics()
        
        print("\n" + "="*60)
        print("PERFORMANCE METRICS")
        print("="*60)
        
        for key, value in metrics['metrics'].items():
            key_display = key.replace("_", " ").title()
            print(f"{key_display}: {value}")
        
        print("-"*60)
        print(f"Commentary: {metrics['sass_commentary']}")
        print(f"Project Health: {metrics['project_health']}")
        print(f"Sass Level: {metrics['sass_level']}/11\n")
    
    def do_memory(self, arg):
        """Check memory stats: memory [agent_id]"""
        if arg:
            # Get agent-specific memory
            context = self.brenda.memory_store.get_agent_context(arg)
            
            if context['total_interactions'] == 0:
                print(f"No memory of agent {arg}")
                return
            
            print(f"\n" + "="*60)
            print(f"AGENT MEMORY: {arg}")
            print("="*60)
            print(f"First Seen: {context['first_seen']}")
            print(f"Last Seen: {context['last_seen']}")
            print(f"Total Interactions: {context['total_interactions']}")
            print(f"Reliability: {context['reliability']:.1%}")
            print(f"Trend: {context['reliability_trend']}")
            print(f"Failure Rate: {context['failure_rate']:.1%}")
            
            if context['quirks']:
                print(f"Known Quirks: {', '.join(context['quirks'])}")
            
            if context['recent_interactions']:
                print("\nRecent Interactions:")
                for interaction in context['recent_interactions'][-3:]:
                    print(f"  - {interaction['timestamp']}: {interaction['request_type']}")
        else:
            # Get general memory stats
            stats = self.brenda.memory_store.get_memory_stats()
            
            print("\n" + "="*60)
            print("MEMORY STATISTICS")
            print("="*60)
            
            for key, value in stats.items():
                key_display = key.replace("_", " ").title()
                if isinstance(value, list):
                    print(f"{key_display}: {len(value)} items")
                else:
                    print(f"{key_display}: {value}")
            
            # Show recurring issues
            issues = self.brenda.memory_store.get_recurring_issues()
            if issues:
                print("\nRecurring Issues:")
                for issue_type, details in issues.items():
                    print(f"  - {issue_type}: {details['count']} occurrences")
        
        print()
    
    def do_blocker(self, arg):
        """Simulate blocker: blocker <agent_id> <type> [description]"""
        parts = arg.split(maxsplit=2)
        if len(parts) < 2:
            print("Usage: blocker <agent_id> <type> [description]")
            print("Types: permission, conflict, resource")
            return
        
        agent_id = parts[0]
        blocker_type = parts[1]
        description = parts[2] if len(parts) > 2 else f"Mock {blocker_type} blocker"
        
        if agent_id not in self.mock_agents:
            print(f"Unknown agent: {agent_id}")
            return
        
        # Resolve blocker
        blocker = {
            "type": blocker_type,
            "description": description,
            "timestamp": datetime.now().isoformat()
        }
        
        result = asyncio.run(self.brenda.resolve_blocker(agent_id, blocker))
        
        print(f"\n🔧 BLOCKER RESOLUTION ATTEMPT")
        print(f"Agent: {agent_id}")
        print(f"Blocker Type: {blocker_type}")
        
        if result.get('resolution'):
            resolution = result['resolution']
            if resolution.get('success'):
                print(f"✓ Resolution: {resolution.get('action')}")
                print(f"  {resolution.get('details')}")
            else:
                print(f"✗ Failed: {resolution.get('details')}")
        
        if result.get('escalation_id'):
            print(f"⚠ Escalated: {result.get('message')}")
        
        if result.get('sass'):
            print(f"💬 {result['sass']}\n")
    
    def do_health(self, arg):
        """Set project health: health <1-10>"""
        if not arg:
            print(f"Current project health: {self.brenda.project_health.name}")
            return
        
        try:
            value = int(arg)
            if 1 <= value <= 10:
                # Map value to ProjectHealth enum
                if value <= 2:
                    self.brenda.project_health = ProjectHealth.CRITICAL
                elif value <= 4:
                    self.brenda.project_health = ProjectHealth.POOR
                elif value <= 6:
                    self.brenda.project_health = ProjectHealth.CONCERNING
                elif value <= 8:
                    self.brenda.project_health = ProjectHealth.MODERATE
                else:
                    self.brenda.project_health = ProjectHealth.GOOD
                
                self.brenda._update_sass_level()
                print(f"Project health set to: {self.brenda.project_health.name}")
                print(f"Sass level updated to: {self.brenda.sass_engine.sass_level}/11")
            else:
                print("Health must be between 1 and 10")
        except ValueError:
            print("Invalid health value. Use a number 1-10")
    
    def do_simulate(self, arg):
        """Simulate agent activity: simulate [chaos|normal|perfect]"""
        mode = arg.lower() if arg else "normal"
        
        print(f"\n🎮 Simulating {mode.upper()} mode...")
        
        if mode == "chaos":
            # Simulate failures
            for agent_id in list(self.mock_agents.keys())[:2]:
                for i in range(3):
                    request = {
                        "type": "status_update",
                        "sender": agent_id,
                        "status": "failed"
                    }
                    asyncio.run(self.brenda.process_request(request))
            print("Chaos simulation complete. Check status for results.")
            
        elif mode == "perfect":
            # Simulate successes
            for agent_id in self.mock_agents.keys():
                request = {
                    "type": "status_update",
                    "sender": agent_id,
                    "status": "completed"
                }
                asyncio.run(self.brenda.process_request(request))
            print("Perfect simulation complete. Everything worked (suspicious...).")
            
        else:
            # Normal mixed results
            statuses = ["completed", "completed", "failed", "working"]
            for agent_id, status in zip(self.mock_agents.keys(), statuses):
                request = {
                    "type": "status_update",
                    "sender": agent_id,
                    "status": status
                }
                asyncio.run(self.brenda.process_request(request))
            print("Normal simulation complete. Mixed results as expected.")
        
        # Show a sass quip about the simulation
        quip = self.brenda.sass_engine.get_contextual_quip("status_update")
        print(f"💬 {quip}\n")
    
    def do_save(self, arg):
        """Save memory to disk: save"""
        self.brenda.memory_store.save_memory()
        print("Memory saved successfully.")
    
    def do_clear(self, arg):
        """Clear screen: clear"""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        print(self.intro)
    
    def do_exit(self, arg):
        """Exit Brenda console: exit"""
        # Save memory before exit
        self.brenda.memory_store.save_memory()
        
        # Final sass
        print(f"\n{self.brenda.sass_engine.get_contextual_quip('general')}")
        print("Memory saved. Don't let the door hit you on the way out.\n")
        return True
    
    def do_quit(self, arg):
        """Exit Brenda console: quit"""
        return self.do_exit(arg)
    
    def default(self, line):
        """Handle unknown commands"""
        print(f"Unknown command: {line}")
        print("Type 'help' for available commands.")
        print(f"💬 {self.brenda.sass_engine.get_contextual_quip('general')}\n")
    
    def emptyline(self):
        """Handle empty input"""
        pass


def main():
    """Main entry point"""
    try:
        console = BrendaConsole()
        console.cmdloop()
    except KeyboardInterrupt:
        print("\n\nKeyboard interrupt. Typical.\n")
    except Exception as e:
        logger.error("Console error: %s", e)
        print(f"\nError: {e}")
        print("Well, that didn't go as planned.\n")


if __name__ == "__main__":
    main()