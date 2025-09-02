"""
MemoryStore - Persistent context management for Brenda
"""

import json
import logging
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from collections import deque, defaultdict
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


@dataclass
class Interaction:
    """Represents a single interaction"""
    timestamp: datetime
    sender: str
    request_type: str
    content: Dict[str, Any]
    response: Optional[Dict[str, Any]] = None
    sass_level: int = 0
    quip: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class AgentMemory:
    """Memory specific to an agent"""
    agent_id: str
    first_seen: datetime
    last_seen: datetime
    total_interactions: int = 0
    failure_count: int = 0
    success_count: int = 0
    quirks: List[str] = None
    reliability_trend: List[float] = None
    
    def __post_init__(self):
        if self.quirks is None:
            self.quirks = []
        if self.reliability_trend is None:
            self.reliability_trend = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'agent_id': self.agent_id,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'total_interactions': self.total_interactions,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'quirks': self.quirks,
            'reliability_trend': self.reliability_trend
        }


@dataclass
class ProjectMemory:
    """Memory for a project"""
    project_id: str
    created: datetime
    last_updated: datetime
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    escalations: List[str] = None
    health_history: List[int] = None
    
    def __post_init__(self):
        if self.escalations is None:
            self.escalations = []
        if self.health_history is None:
            self.health_history = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'project_id': self.project_id,
            'created': self.created.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'total_tasks': self.total_tasks,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'escalations': self.escalations,
            'health_history': self.health_history
        }


class MemoryStore:
    """
    Manages persistent memory and context for Brenda
    
    Features:
    - Interaction history with context window
    - Agent-specific memory and patterns
    - Project memory and trends
    - Pattern recognition for recurring issues
    - Context-aware recall
    """
    
    def __init__(self, storage_path: Optional[Path] = None, max_interactions: int = 1000):
        """
        Initialize MemoryStore
        
        Args:
            storage_path: Path for persistent storage
            max_interactions: Maximum interactions to keep in memory
        """
        self.storage_path = storage_path or Path("brenda_memory.pkl")
        self.max_interactions = max_interactions
        
        # Interaction history
        self.interactions = deque(maxlen=max_interactions)
        
        # Agent memories
        self.agent_memories: Dict[str, AgentMemory] = {}
        
        # Project memories
        self.project_memories: Dict[str, ProjectMemory] = {}
        
        # Pattern detection
        self.recurring_issues: Dict[str, List[Tuple[datetime, str]]] = defaultdict(list)
        self.escalation_patterns: Dict[str, int] = defaultdict(int)
        
        # Context windows
        self.short_term_memory = deque(maxlen=10)  # Last 10 interactions
        self.working_memory: Dict[str, Any] = {}  # Current context
        
        # Load existing memory if available
        self.load_memory()
        
        logger.info("MemoryStore initialized with %d interactions", len(self.interactions))
    
    def add_interaction(self, interaction_data: Dict[str, Any]):
        """
        Add new interaction to memory
        
        Args:
            interaction_data: Interaction details
        """
        interaction = Interaction(
            timestamp=interaction_data.get('timestamp', datetime.now()),
            sender=interaction_data.get('sender', 'unknown'),
            request_type=interaction_data.get('type', 'unknown'),
            content=interaction_data.get('request', {}),
            response=interaction_data.get('response'),
            sass_level=interaction_data.get('sass_level', 0),
            quip=interaction_data.get('quip')
        )
        
        self.interactions.append(interaction)
        self.short_term_memory.append(interaction)
        
        # Update agent memory
        self._update_agent_memory(interaction)
        
        # Detect patterns
        self._detect_patterns(interaction)
        
        logger.debug("Added interaction from %s", interaction.sender)
    
    def _update_agent_memory(self, interaction: Interaction):
        """Update agent-specific memory"""
        agent_id = interaction.sender
        
        if agent_id not in self.agent_memories:
            self.agent_memories[agent_id] = AgentMemory(
                agent_id=agent_id,
                first_seen=interaction.timestamp,
                last_seen=interaction.timestamp
            )
        
        memory = self.agent_memories[agent_id]
        memory.last_seen = interaction.timestamp
        memory.total_interactions += 1
        
        # Track success/failure
        if interaction.response:
            if interaction.response.get('success'):
                memory.success_count += 1
            else:
                memory.failure_count += 1
        
        # Update reliability trend
        if memory.total_interactions > 0:
            reliability = memory.success_count / memory.total_interactions
            memory.reliability_trend.append(reliability)
            
            # Keep only last 20 data points
            if len(memory.reliability_trend) > 20:
                memory.reliability_trend = memory.reliability_trend[-20:]
    
    def _detect_patterns(self, interaction: Interaction):
        """Detect recurring patterns"""
        # Check for recurring issues
        if interaction.request_type == "escalation":
            reason = interaction.content.get('reason', 'unknown')
            self.escalation_patterns[reason] += 1
            self.recurring_issues[reason].append((interaction.timestamp, interaction.sender))
            
            # Keep only recent issues (last 7 days)
            cutoff = datetime.now() - timedelta(days=7)
            self.recurring_issues[reason] = [
                (ts, sender) for ts, sender in self.recurring_issues[reason]
                if ts > cutoff
            ]
    
    def get_agent_context(self, agent_id: str) -> Dict[str, Any]:
        """
        Get context for specific agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent context and history
        """
        if agent_id not in self.agent_memories:
            return {
                'status': 'unknown',
                'first_contact': False,
                'history': []
            }
        
        memory = self.agent_memories[agent_id]
        
        # Get recent interactions with this agent
        recent_interactions = [
            i for i in self.short_term_memory
            if i.sender == agent_id
        ]
        
        # Calculate reliability trend
        reliability_trend = "stable"
        if len(memory.reliability_trend) >= 3:
            recent = memory.reliability_trend[-3:]
            if recent[-1] > recent[0]:
                reliability_trend = "improving"
            elif recent[-1] < recent[0]:
                reliability_trend = "declining"
        
        return {
            'agent_id': agent_id,
            'first_seen': memory.first_seen,
            'last_seen': memory.last_seen,
            'total_interactions': memory.total_interactions,
            'reliability': memory.success_count / max(memory.total_interactions, 1),
            'reliability_trend': reliability_trend,
            'quirks': memory.quirks,
            'recent_interactions': [i.to_dict() for i in recent_interactions],
            'failure_rate': memory.failure_count / max(memory.total_interactions, 1)
        }
    
    def get_project_context(self, project_id: str) -> Dict[str, Any]:
        """
        Get context for specific project
        
        Args:
            project_id: Project identifier
            
        Returns:
            Project context and history
        """
        if project_id not in self.project_memories:
            # Create new project memory
            self.project_memories[project_id] = ProjectMemory(
                project_id=project_id,
                created=datetime.now(),
                last_updated=datetime.now()
            )
        
        memory = self.project_memories[project_id]
        
        # Calculate project health
        if memory.total_tasks > 0:
            success_rate = memory.completed_tasks / memory.total_tasks
            if success_rate < 0.5:
                health = "critical"
            elif success_rate < 0.7:
                health = "poor"
            elif success_rate < 0.9:
                health = "moderate"
            else:
                health = "good"
        else:
            health = "unknown"
        
        return {
            'project_id': project_id,
            'created': memory.created,
            'last_updated': memory.last_updated,
            'total_tasks': memory.total_tasks,
            'completed_tasks': memory.completed_tasks,
            'failed_tasks': memory.failed_tasks,
            'success_rate': memory.completed_tasks / max(memory.total_tasks, 1),
            'health': health,
            'recent_escalations': memory.escalations[-5:],
            'health_trend': memory.health_history[-10:]
        }
    
    def get_recurring_issues(self) -> Dict[str, Any]:
        """Get analysis of recurring issues"""
        analysis = {}
        
        for issue_type, occurrences in self.recurring_issues.items():
            if len(occurrences) >= 3:  # Pattern threshold
                analysis[issue_type] = {
                    'count': len(occurrences),
                    'frequency': f"{len(occurrences)} times in last 7 days",
                    'agents_affected': list(set(sender for _, sender in occurrences)),
                    'last_occurrence': max(ts for ts, _ in occurrences)
                }
        
        return analysis
    
    def get_escalation_patterns(self) -> Dict[str, int]:
        """Get escalation pattern analysis"""
        return dict(self.escalation_patterns)
    
    def recall_similar_situation(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Recall similar past situation
        
        Args:
            context: Current situation context
            
        Returns:
            Similar past situation if found
        """
        request_type = context.get('type')
        sender = context.get('sender')
        
        # Search for similar interactions
        similar_interactions = [
            i for i in self.interactions
            if i.request_type == request_type and i.sender == sender
        ]
        
        if similar_interactions:
            # Return most recent similar
            recent = similar_interactions[-1]
            return {
                'timestamp': recent.timestamp,
                'request': recent.content,
                'response': recent.response,
                'sass_used': recent.quip,
                'outcome': 'success' if recent.response and recent.response.get('success') else 'failure'
            }
        
        return None
    
    def update_working_memory(self, key: str, value: Any):
        """Update working memory with current context"""
        self.working_memory[key] = value
    
    def get_working_memory(self) -> Dict[str, Any]:
        """Get current working memory"""
        return self.working_memory.copy()
    
    def clear_working_memory(self):
        """Clear working memory"""
        self.working_memory.clear()
    
    def save_memory(self):
        """Save memory to persistent storage"""
        try:
            memory_data = {
                'interactions': list(self.interactions),
                'agent_memories': self.agent_memories,
                'project_memories': self.project_memories,
                'recurring_issues': dict(self.recurring_issues),
                'escalation_patterns': dict(self.escalation_patterns)
            }
            
            with open(self.storage_path, 'wb') as f:
                pickle.dump(memory_data, f)
            
            logger.info("Memory saved to %s", self.storage_path)
        except Exception as e:
            logger.error("Failed to save memory: %s", e)
    
    def load_memory(self):
        """Load memory from persistent storage"""
        if not self.storage_path.exists():
            logger.info("No existing memory found")
            return
        
        try:
            with open(self.storage_path, 'rb') as f:
                memory_data = pickle.load(f)
            
            self.interactions = deque(memory_data.get('interactions', []), maxlen=self.max_interactions)
            self.agent_memories = memory_data.get('agent_memories', {})
            self.project_memories = memory_data.get('project_memories', {})
            self.recurring_issues = defaultdict(list, memory_data.get('recurring_issues', {}))
            self.escalation_patterns = defaultdict(int, memory_data.get('escalation_patterns', {}))
            
            logger.info("Memory loaded from %s", self.storage_path)
        except Exception as e:
            logger.error("Failed to load memory: %s", e)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            'total_interactions': len(self.interactions),
            'unique_agents': len(self.agent_memories),
            'active_projects': len(self.project_memories),
            'recurring_issues': len(self.recurring_issues),
            'escalation_types': len(self.escalation_patterns),
            'short_term_memory_size': len(self.short_term_memory),
            'working_memory_keys': list(self.working_memory.keys())
        }
    
    def forget_agent(self, agent_id: str):
        """Remove agent from memory"""
        if agent_id in self.agent_memories:
            del self.agent_memories[agent_id]
            logger.info("Forgot agent: %s", agent_id)