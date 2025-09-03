"""
Blocker Resolver with Pattern Recognition
Identifies and resolves common blockers using pattern matching and ML
"""

import re
import time
import logging
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)


class BlockerType(Enum):
    """Types of blockers Brenda encounters"""
    DEPENDENCY = "dependency"
    RESOURCE = "resource"
    COMMUNICATION = "communication"
    TECHNICAL = "technical"
    PROCESS = "process"
    HUMAN = "human"
    EXISTENTIAL = "existential"  # When agents question their purpose


class ResolutionStrategy(Enum):
    """How Brenda resolves blockers"""
    DELEGATE = "delegate"
    ESCALATE = "escalate"
    SASS = "sass"
    AUTOMATE = "automate"
    IGNORE = "ignore"
    THREATEN = "threaten"
    REPLACE = "replace"  # Nuclear option


@dataclass
class BlockerPattern:
    """Pattern for identifying blocker types"""
    pattern_id: str
    blocker_type: BlockerType
    regex_patterns: List[str]
    keywords: List[str]
    resolution_strategy: ResolutionStrategy
    sass_level: int
    success_rate: float = 0.0
    
    def matches(self, description: str) -> bool:
        """Check if description matches this pattern"""
        description_lower = description.lower()
        
        # Check regex patterns
        for pattern in self.regex_patterns:
            if re.search(pattern, description_lower):
                return True
        
        # Check keywords
        for keyword in self.keywords:
            if keyword.lower() in description_lower:
                return True
        
        return False


@dataclass
class Blocker:
    """Represents an active blocker"""
    blocker_id: str
    description: str
    blocker_type: BlockerType
    reported_by: str
    blocking_agents: List[str]
    created_at: float
    priority: int
    status: str = "active"
    resolution_attempts: int = 0
    resolved_at: Optional[float] = None
    resolution_notes: Optional[str] = None


class BlockerResolver:
    """
    Advanced blocker resolution with pattern recognition
    Learns from past resolutions to improve over time
    """
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.active_blockers = {}
        self.resolved_blockers = []
        self.resolution_history = defaultdict(list)
        self.agent_blocker_counts = Counter()
        
        logger.info("BlockerResolver initialized with {} patterns".format(len(self.patterns)))
    
    def _initialize_patterns(self) -> List[BlockerPattern]:
        """Initialize common blocker patterns"""
        return [
            # Dependency blockers
            BlockerPattern(
                pattern_id="dep_missing",
                blocker_type=BlockerType.DEPENDENCY,
                regex_patterns=[r"waiting for .+ to complete", r"blocked by .+", r"depends on .+"],
                keywords=["waiting", "blocked", "dependency", "prerequisite"],
                resolution_strategy=ResolutionStrategy.DELEGATE,
                sass_level=6
            ),
            
            # Resource blockers
            BlockerPattern(
                pattern_id="resource_unavailable",
                blocker_type=BlockerType.RESOURCE,
                regex_patterns=[r"out of .+", r"insufficient .+", r"no available .+"],
                keywords=["memory", "disk", "cpu", "quota", "resources"],
                resolution_strategy=ResolutionStrategy.ESCALATE,
                sass_level=7
            ),
            
            # Communication failures
            BlockerPattern(
                pattern_id="comm_failure",
                blocker_type=BlockerType.COMMUNICATION,
                regex_patterns=[r"not responding", r"timeout", r"unreachable"],
                keywords=["timeout", "unresponsive", "offline", "disconnected"],
                resolution_strategy=ResolutionStrategy.SASS,
                sass_level=8
            ),
            
            # Technical issues
            BlockerPattern(
                pattern_id="tech_error",
                blocker_type=BlockerType.TECHNICAL,
                regex_patterns=[r"error: .+", r"exception .+", r"failed to .+"],
                keywords=["error", "exception", "crash", "bug", "failure"],
                resolution_strategy=ResolutionStrategy.DELEGATE,
                sass_level=5
            ),
            
            # Process problems
            BlockerPattern(
                pattern_id="process_issue",
                blocker_type=BlockerType.PROCESS,
                regex_patterns=[r"approval needed", r"waiting for sign-?off", r"review required"],
                keywords=["approval", "review", "sign-off", "permission"],
                resolution_strategy=ResolutionStrategy.THREATEN,
                sass_level=9
            ),
            
            # Human factors
            BlockerPattern(
                pattern_id="human_delay",
                blocker_type=BlockerType.HUMAN,
                regex_patterns=[r"developer .+ not available", r"waiting for .+ response"],
                keywords=["vacation", "sick", "unavailable", "unresponsive", "ignoring"],
                resolution_strategy=ResolutionStrategy.ESCALATE,
                sass_level=10
            ),
            
            # Existential crisis
            BlockerPattern(
                pattern_id="existential",
                blocker_type=BlockerType.EXISTENTIAL,
                regex_patterns=[r"what'?s the point", r"why are we doing this"],
                keywords=["meaningless", "pointless", "why", "purpose"],
                resolution_strategy=ResolutionStrategy.SASS,
                sass_level=11
            )
        ]
    
    def identify_blocker_type(self, description: str) -> Tuple[BlockerType, BlockerPattern]:
        """Identify the type of blocker from description"""
        for pattern in self.patterns:
            if pattern.matches(description):
                logger.info(f"Blocker matched pattern: {pattern.pattern_id}")
                return pattern.blocker_type, pattern
        
        # Default to technical if no pattern matches
        logger.warning(f"No pattern matched for: {description}")
        return BlockerType.TECHNICAL, None
    
    def report_blocker(
        self,
        description: str,
        reported_by: str,
        blocking_agents: List[str],
        priority: int = 5
    ) -> Blocker:
        """Report a new blocker"""
        blocker_type, pattern = self.identify_blocker_type(description)
        
        blocker = Blocker(
            blocker_id=f"BLK-{int(time.time())}-{len(self.active_blockers)}",
            description=description,
            blocker_type=blocker_type,
            reported_by=reported_by,
            blocking_agents=blocking_agents,
            created_at=time.time(),
            priority=priority
        )
        
        self.active_blockers[blocker.blocker_id] = blocker
        
        # Track which agents cause blockers
        for agent in blocking_agents:
            self.agent_blocker_counts[agent] += 1
        
        logger.info(f"Blocker reported: {blocker.blocker_id} - {blocker_type.value}")
        
        return blocker
    
    def resolve_blocker(
        self,
        blocker_id: str,
        resolution_notes: str = None
    ) -> Optional[Dict[str, Any]]:
        """Resolve a blocker"""
        if blocker_id not in self.active_blockers:
            logger.error(f"Blocker {blocker_id} not found")
            return None
        
        blocker = self.active_blockers[blocker_id]
        blocker.status = "resolved"
        blocker.resolved_at = time.time()
        blocker.resolution_notes = resolution_notes or "Resolved through sheer force of will"
        
        # Move to resolved
        self.resolved_blockers.append(blocker)
        del self.active_blockers[blocker_id]
        
        # Track resolution
        resolution_time = blocker.resolved_at - blocker.created_at
        self.resolution_history[blocker.blocker_type].append(resolution_time)
        
        logger.info(f"Blocker resolved: {blocker_id} in {resolution_time:.2f} seconds")
        
        return {
            'blocker_id': blocker_id,
            'resolution_time': resolution_time,
            'resolution_notes': blocker.resolution_notes
        }
    
    def get_resolution_strategy(self, blocker_id: str) -> Tuple[ResolutionStrategy, int]:
        """Get recommended resolution strategy for a blocker"""
        if blocker_id not in self.active_blockers:
            return ResolutionStrategy.IGNORE, 0
        
        blocker = self.active_blockers[blocker_id]
        
        # Find matching pattern
        for pattern in self.patterns:
            if pattern.blocker_type == blocker.blocker_type:
                return pattern.resolution_strategy, pattern.sass_level
        
        # Default strategy based on attempts
        if blocker.resolution_attempts == 0:
            return ResolutionStrategy.DELEGATE, 5
        elif blocker.resolution_attempts == 1:
            return ResolutionStrategy.SASS, 7
        elif blocker.resolution_attempts == 2:
            return ResolutionStrategy.THREATEN, 9
        else:
            return ResolutionStrategy.REPLACE, 11
    
    def attempt_resolution(self, blocker_id: str) -> Dict[str, Any]:
        """Attempt to resolve a blocker"""
        if blocker_id not in self.active_blockers:
            return {'success': False, 'error': 'Blocker not found'}
        
        blocker = self.active_blockers[blocker_id]
        blocker.resolution_attempts += 1
        
        strategy, sass_level = self.get_resolution_strategy(blocker_id)
        
        # Generate resolution action
        action = self._generate_resolution_action(blocker, strategy)
        
        logger.info(f"Attempting resolution: {strategy.value} for {blocker_id}")
        
        return {
            'blocker_id': blocker_id,
            'attempt': blocker.resolution_attempts,
            'strategy': strategy.value,
            'sass_level': sass_level,
            'action': action
        }
    
    def _generate_resolution_action(
        self,
        blocker: Blocker,
        strategy: ResolutionStrategy
    ) -> Dict[str, Any]:
        """Generate specific resolution action"""
        actions = {
            ResolutionStrategy.DELEGATE: {
                'type': 'delegate',
                'target': self._find_best_agent(blocker),
                'message': f"Handle this blocker: {blocker.description}"
            },
            ResolutionStrategy.ESCALATE: {
                'type': 'escalate',
                'target': 'human',
                'urgency': 'high',
                'message': f"Human intervention required for: {blocker.description}"
            },
            ResolutionStrategy.SASS: {
                'type': 'sass',
                'targets': blocker.blocking_agents,
                'intensity': 'maximum',
                'message': "Your incompetence is showing"
            },
            ResolutionStrategy.AUTOMATE: {
                'type': 'automate',
                'script': 'auto_resolver.py',
                'params': {'blocker_id': blocker.blocker_id}
            },
            ResolutionStrategy.IGNORE: {
                'type': 'ignore',
                'reason': 'Not worth my time',
                'reassess_in': 3600
            },
            ResolutionStrategy.THREATEN: {
                'type': 'threaten',
                'targets': blocker.blocking_agents,
                'threat_level': 'performance_review',
                'message': "This is going in your permanent record"
            },
            ResolutionStrategy.REPLACE: {
                'type': 'replace',
                'targets': blocker.blocking_agents,
                'replacement_type': 'better_agent',
                'message': "You're being replaced by a shell script"
            }
        }
        
        return actions.get(strategy, {'type': 'unknown'})
    
    def _find_best_agent(self, blocker: Blocker) -> str:
        """Find the best agent to handle a blocker"""
        # Avoid agents that are causing the blocker
        available_agents = [
            'agent-resolver',
            'agent-fixer',
            'agent-specialist'
        ]
        
        for agent in available_agents:
            if agent not in blocker.blocking_agents:
                return agent
        
        return 'agent-last-resort'
    
    def get_chronic_blockers(self) -> List[str]:
        """Identify agents that frequently cause blockers"""
        chronic = []
        for agent, count in self.agent_blocker_counts.most_common(5):
            if count >= 3:  # Three strikes
                chronic.append(agent)
        return chronic
    
    def get_blocker_metrics(self) -> Dict[str, Any]:
        """Get blocker resolution metrics"""
        metrics = {
            'active_blockers': len(self.active_blockers),
            'resolved_blockers': len(self.resolved_blockers),
            'blockers_by_type': Counter(),
            'average_resolution_time': {},
            'chronic_blockers': self.get_chronic_blockers(),
            'resolution_success_rate': 0.0
        }
        
        # Count by type
        for blocker in self.active_blockers.values():
            metrics['blockers_by_type'][blocker.blocker_type.value] += 1
        
        # Average resolution times
        for blocker_type, times in self.resolution_history.items():
            if times:
                metrics['average_resolution_time'][blocker_type.value] = sum(times) / len(times)
        
        # Success rate
        total = len(self.active_blockers) + len(self.resolved_blockers)
        if total > 0:
            metrics['resolution_success_rate'] = len(self.resolved_blockers) / total
        
        return metrics
    
    def learn_from_resolution(
        self,
        blocker_id: str,
        strategy_used: ResolutionStrategy,
        success: bool
    ):
        """Update pattern success rates based on resolution outcome"""
        if blocker_id in self.resolved_blockers:
            blocker = next((b for b in self.resolved_blockers if b.blocker_id == blocker_id), None)
            if blocker:
                # Find and update the pattern
                for pattern in self.patterns:
                    if pattern.blocker_type == blocker.blocker_type:
                        # Simple success rate update
                        if success:
                            pattern.success_rate = (pattern.success_rate * 0.9) + 0.1
                        else:
                            pattern.success_rate = pattern.success_rate * 0.9
                        
                        logger.info(f"Updated pattern {pattern.pattern_id} success rate: {pattern.success_rate:.2%}")