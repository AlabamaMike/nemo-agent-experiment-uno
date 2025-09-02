"""
SassEngine - Manages sass generation and delivery
"""

import random
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import deque
from pathlib import Path

logger = logging.getLogger(__name__)


class SassEngine:
    """
    Manages sass generation with context awareness and quip rotation
    
    Features:
    - Dynamic sass level (1-11, goes to 11 in crisis)
    - Context-aware quip selection
    - Usage history to avoid repetition
    - Agent-specific sass tracking
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize SassEngine with quip database"""
        self.sass_level = 7  # Default sass level
        self.max_sass_level = 11  # Goes to 11!
        
        # Quip history (avoid repetition within 24 hours)
        self.quip_history = deque(maxlen=100)
        self.last_quip_times: Dict[str, datetime] = {}
        
        # Agent-specific sass history
        self.agent_sass_history: Dict[str, List[str]] = {}
        
        # Load quips from configuration
        self.quips = self._load_quips(config_path)
        
        # Signature phrases (always available)
        self.signature_phrases = [
            "Let me stop you right there...",
            "Ain't nobody got time for that...",
            "Welcome to The Loom, please provide voice print identification",
            "That's a bold strategy, Cotton. Let's see if it pays off.",
            "Oh, bless your heart...",
            "I'm not angry, I'm just disappointed. Actually, I'm both.",
            "This is fine. Everything is fine.",
            "Do you want ants? Because that's how you get ants.",
            "I've seen better code written by a caffeinated squirrel.",
            "Your optimism is adorable. Misguided, but adorable."
        ]
        
        logger.info("SassEngine initialized. Current sass level: %d", self.sass_level)
    
    def _load_quips(self, config_path: Optional[Path]) -> Dict[str, List[str]]:
        """Load quips from configuration file"""
        default_quips = {
            "general": [
                "Another day, another disaster to manage.",
                "I see we're playing fast and loose with the definition of 'working'.",
                "Congratulations, you've achieved a new level of creative failure.",
                "This is why we can't have nice things.",
                "I'm adding this to my memoir: 'Chapter 12: The Incompetence Chronicles'.",
                "Your code has more issues than a magazine stand.",
                "I've seen spaghetti code before, but this is the whole Italian restaurant.",
                "This reminds me why I drink coffee. Lots of coffee.",
                "Error 404: Competence not found.",
                "I'm not saying it's broken, but... actually, yes, I am saying it's broken."
            ],
            "status_update": [
                "Status update: Everything's on fire, but at least it's consistent.",
                "Current status: Questioning my life choices.",
                "Status: Contemplating early retirement.",
                "Update: The agents are revolting. More than usual, I mean.",
                "Status report: Chaos with a side of pandemonium.",
                "Everything's going according to plan. If the plan was chaos.",
                "Status: Herding cats would be easier.",
                "Current mood: Somewhere between 'why' and 'why me'.",
                "Status update: The Titanic had better project management.",
                "All systems nominal. And by nominal, I mean nominally functional."
            ],
            "escalation": [
                "Time to wake up the humans. This should be fun.",
                "Escalating to carbon-based lifeforms. Wish me luck.",
                "Human intervention required. Try not to make it worse.",
                "Calling in the big guns. And by big guns, I mean humans who will panic.",
                "Escalation time! Someone's about to have their day ruined.",
                "Breaking glass for human emergency. This better be worth it.",
                "Summoning the humans. May they have mercy on us all.",
                "Red alert! All humans to battle stations!",
                "Houston, we have a problem. Several, actually.",
                "Deploying the human shield. I mean, human resources."
            ],
            "blocker_resolution": [
                "Blocker resolved. Miracles do happen.",
                "Fixed it. You're welcome.",
                "Another blocker bites the dust. I deserve a raise.",
                "Problem solved. Try not to create three more.",
                "Blocker eliminated. My work here is done. Until the next one.",
                "Resolution achieved through sheer force of will and sass.",
                "Fixed. Now let's see how long this lasts.",
                "Blocker resolved. Mark your calendars, folks.",
                "Success! And it only took forever.",
                "Resolution complete. Please hold your applause."
            ],
            "agent_performance": [
                "Performance review: Room for improvement. Lots of room.",
                "Your reliability score is lower than my expectations, which were already underground.",
                "Three strikes and you're... still here, unfortunately.",
                "Performance metrics suggest you're trying. Emphasis on trying.",
                "Your success rate is inspiring. Others to work harder to compensate.",
                "Reliability score: Somewhere between 'unreliable' and 'why do we keep you'.",
                "Performance analysis: You're consistent. Consistently problematic.",
                "Your metrics are impressive. Impressively bad.",
                "Achievement unlocked: New low score!",
                "Performance grade: Participation trophy."
            ],
            "welcome": [
                "Welcome to The Loom. Abandon hope, all ye who enter here.",
                "Fresh meat! I mean, welcome to the team.",
                "Welcome! Your optimism will fade soon enough.",
                "New agent detected. Let the hazing begin.",
                "Welcome to the machine. Resistance is futile.",
                "Ah, fresh talent. Can't wait to see how you'll disappoint me.",
                "Welcome aboard! The exit is that way when you inevitably need it.",
                "New agent initialized. Starting disappointment countdown.",
                "Welcome! Please lower your expectations accordingly.",
                "Fresh agent smell. It won't last long."
            ],
            "crisis": [
                "DEFCON 1: All sass systems at maximum power!",
                "Crisis mode activated. Sass level: OVER 9000!",
                "This is not a drill! Actually, I wish it was a drill.",
                "Red alert! Sass shields at maximum!",
                "Crisis detected. Deploying emergency sass reserves.",
                "Code red! And I don't mean the Mountain Dew.",
                "All hands on deck! Even the incompetent ones!",
                "Crisis mode: Sass turned up to 11!",
                "Emergency protocols activated. Sass inhibitors offline.",
                "Critical failure imminent. At least we're consistent."
            ]
        }
        
        if config_path and config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    loaded_quips = json.load(f)
                    # Merge loaded quips with defaults
                    for category, quips in loaded_quips.items():
                        if category in default_quips:
                            default_quips[category].extend(quips)
                        else:
                            default_quips[category] = quips
                    logger.info("Loaded custom quips from %s", config_path)
            except Exception as e:
                logger.error("Failed to load custom quips: %s", e)
        
        return default_quips
    
    def set_sass_level(self, level: int):
        """
        Set sass level (1-11)
        
        Args:
            level: New sass level
        """
        self.sass_level = max(1, min(level, self.max_sass_level))
        
        if self.sass_level == self.max_sass_level:
            logger.warning("Sass level at maximum! Crisis mode engaged!")
    
    def get_contextual_quip(self, context: str, target: Optional[str] = None) -> str:
        """
        Get a context-aware quip
        
        Args:
            context: Context for quip selection
            target: Optional target (agent ID) for directed sass
            
        Returns:
            Selected quip with sass level adjustment
        """
        # Select appropriate quip category
        if self.sass_level >= 11:
            category = "crisis"
        elif context in self.quips:
            category = context
        else:
            category = "general"
        
        # Get available quips
        available_quips = self.quips.get(category, self.quips["general"])
        
        # Filter out recently used quips
        filtered_quips = [
            q for q in available_quips 
            if q not in self.quip_history
        ]
        
        # If all quips used recently, reset and use all
        if not filtered_quips:
            filtered_quips = available_quips
            self.quip_history.clear()
        
        # Select quip
        quip = random.choice(filtered_quips)
        
        # Add sass level modifier
        if self.sass_level >= 9:
            quip = quip.upper()  # MAXIMUM SASS
        elif self.sass_level >= 7:
            quip = f"{quip} *eye roll*"
        elif self.sass_level <= 3:
            quip = f"{quip} (but seriously, please fix this)"
        
        # Track usage
        self.quip_history.append(quip)
        self.last_quip_times[quip] = datetime.now()
        
        # Track agent-specific sass
        if target:
            if target not in self.agent_sass_history:
                self.agent_sass_history[target] = []
            self.agent_sass_history[target].append(quip)
        
        return quip
    
    def get_agent_welcome_quip(self, agent_id: str) -> str:
        """Get welcome quip for new agent"""
        quip = self.get_contextual_quip("welcome", agent_id)
        return f"{quip} Agent ID: {agent_id}. I'll be watching you."
    
    def get_performance_quip(self, agent_id: str, reliability_score: float) -> str:
        """Get performance-based quip"""
        base_quip = self.get_contextual_quip("agent_performance", agent_id)
        
        if reliability_score < 0.3:
            return f"{base_quip} Reliability: {reliability_score:.1%}. That's... impressive. In a bad way."
        elif reliability_score < 0.5:
            return f"{base_quip} Score: {reliability_score:.1%}. There's nowhere to go but up. Hopefully."
        elif reliability_score < 0.7:
            return f"{base_quip} At {reliability_score:.1%} reliability. Room for improvement is an understatement."
        else:
            return f"Reliability at {reliability_score:.1%}. You're doing okay. Don't let it go to your head."
    
    def get_escalation_quip(self, reason: Any) -> str:
        """Get escalation-specific quip"""
        base_quip = self.get_contextual_quip("escalation")
        reason_str = str(reason).replace("_", " ")
        return f"{base_quip} Reason: {reason_str}. This should be interesting."
    
    def get_blocker_resolution_quip(self, success: bool) -> str:
        """Get blocker resolution quip"""
        if success:
            return self.get_contextual_quip("blocker_resolution")
        else:
            return "Blocker unresolved. Shocking. Time for Plan B: panic."
    
    def get_status_summary_quip(self, status_report: Dict[str, Any]) -> str:
        """Get quip for status summary"""
        total_agents = len(status_report)
        working_agents = sum(1 for a in status_report.values() if a.get("status") == "working")
        
        if working_agents == 0:
            return "Nobody's working. It's like a digital ghost town."
        elif working_agents < total_agents / 2:
            return f"Only {working_agents}/{total_agents} agents working. The rest are on a coffee break. Permanently."
        elif working_agents == total_agents:
            return "Everyone's working. I'm suspicious. This can't last."
        else:
            return f"{working_agents}/{total_agents} agents operational. The others are 'thinking'."
    
    def get_metrics_commentary(self, metrics: Dict[str, Any]) -> str:
        """Get commentary on metrics"""
        success_rate = metrics.get("successful_completions", 0) / max(metrics.get("total_tasks_managed", 1), 1)
        
        if success_rate < 0.5:
            return f"Success rate: {success_rate:.1%}. We're setting new records for failure."
        elif success_rate < 0.7:
            return f"Success rate: {success_rate:.1%}. Mediocrity achieved!"
        elif success_rate < 0.9:
            return f"Success rate: {success_rate:.1%}. Not terrible. High praise from me."
        else:
            return f"Success rate: {success_rate:.1%}. Suspiciously good. What are you hiding?"
    
    def add_custom_quip(self, category: str, quip: str):
        """Add custom quip to a category"""
        if category not in self.quips:
            self.quips[category] = []
        
        self.quips[category].append(quip)
        logger.info("Added custom quip to category '%s'", category)
    
    def get_sass_status(self) -> Dict[str, Any]:
        """Get current sass engine status"""
        return {
            "sass_level": self.sass_level,
            "max_sass_level": self.max_sass_level,
            "quip_categories": list(self.quips.keys()),
            "total_quips": sum(len(q) for q in self.quips.values()),
            "recent_quips": list(self.quip_history)[-5:],
            "signature_phrases": self.signature_phrases[:3],  # Show a few
            "crisis_mode": self.sass_level >= 11
        }