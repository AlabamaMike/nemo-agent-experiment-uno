"""
Performance Tracker with Metrics Engine
Tracks agent performance, calculates scores, and identifies MVPs and slackers
"""

import time
import statistics
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


class PerformanceLevel(Enum):
    """Agent performance levels"""
    ROCKSTAR = "rockstar"
    SOLID = "solid"
    ADEQUATE = "adequate"
    STRUGGLING = "struggling"
    DISASTER = "disaster"
    REPLACE_IMMEDIATELY = "replace_immediately"


class MetricType(Enum):
    """Types of metrics we track"""
    TASK_COMPLETION = "task_completion"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    BLOCKER_CREATION = "blocker_creation"
    SASS_RECEIVED = "sass_received"
    RELIABILITY = "reliability"
    INNOVATION = "innovation"
    COLLABORATION = "collaboration"


@dataclass
class AgentMetrics:
    """Metrics for a single agent"""
    agent_id: str
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    error_count: int = 0
    blocker_count: int = 0
    sass_count: int = 0
    
    uptime_start: float = field(default_factory=time.time)
    downtime_total: float = 0.0
    last_activity: float = field(default_factory=time.time)
    
    collaboration_score: float = 0.5
    innovation_score: float = 0.5
    
    strikes: int = 0
    commendations: int = 0
    
    weekly_scores: deque = field(default_factory=lambda: deque(maxlen=52))
    
    def get_completion_rate(self) -> float:
        """Calculate task completion rate"""
        if self.total_tasks == 0:
            return 0.0
        return self.completed_tasks / self.total_tasks
    
    def get_average_response_time(self) -> float:
        """Get average response time"""
        if not self.response_times:
            return float('inf')
        return statistics.mean(self.response_times)
    
    def get_error_rate(self) -> float:
        """Calculate error rate"""
        if self.total_tasks == 0:
            return 0.0
        return self.error_count / self.total_tasks
    
    def get_reliability_score(self) -> float:
        """Calculate reliability score (0-1)"""
        uptime = time.time() - self.uptime_start
        if uptime == 0:
            return 0.0
        availability = 1.0 - (self.downtime_total / uptime)
        completion = self.get_completion_rate()
        error_penalty = 1.0 - self.get_error_rate()
        
        return (availability * 0.3 + completion * 0.5 + error_penalty * 0.2)
    
    def get_overall_score(self) -> float:
        """Calculate overall performance score (0-100)"""
        reliability = self.get_reliability_score()
        
        # Penalize for blockers and sass
        blocker_penalty = max(0, 1.0 - (self.blocker_count * 0.1))
        sass_penalty = max(0, 1.0 - (self.sass_count * 0.05))
        
        # Bonus for commendations
        commendation_bonus = min(1.2, 1.0 + (self.commendations * 0.05))
        
        # Strike penalty
        strike_penalty = max(0.3, 1.0 - (self.strikes * 0.2))
        
        score = (
            reliability * 40 +
            self.collaboration_score * 20 +
            self.innovation_score * 20 +
            blocker_penalty * 10 +
            sass_penalty * 10
        ) * commendation_bonus * strike_penalty
        
        return min(100, max(0, score))


class PerformanceTracker:
    """
    Tracks and analyzes agent performance
    Identifies top performers and problem agents
    """
    
    def __init__(self):
        self.agents = {}
        self.task_history = defaultdict(list)
        self.performance_events = []
        self.mvp_history = []
        self.shame_list = []
        
        logger.info("PerformanceTracker initialized")
    
    def register_agent(self, agent_id: str) -> AgentMetrics:
        """Register a new agent for tracking"""
        if agent_id not in self.agents:
            self.agents[agent_id] = AgentMetrics(agent_id=agent_id)
            logger.info(f"Agent {agent_id} registered for performance tracking")
        return self.agents[agent_id]
    
    def record_task_assignment(self, agent_id: str, task_id: str):
        """Record that a task was assigned to an agent"""
        if agent_id not in self.agents:
            self.register_agent(agent_id)
        
        self.agents[agent_id].total_tasks += 1
        self.task_history[agent_id].append({
            'task_id': task_id,
            'assigned_at': time.time(),
            'status': 'assigned'
        })
        
        logger.info(f"Task {task_id} assigned to {agent_id}")
    
    def record_task_completion(
        self,
        agent_id: str,
        task_id: str,
        success: bool,
        duration: float
    ):
        """Record task completion"""
        if agent_id not in self.agents:
            return
        
        metrics = self.agents[agent_id]
        
        if success:
            metrics.completed_tasks += 1
        else:
            metrics.failed_tasks += 1
        
        metrics.response_times.append(duration)
        metrics.last_activity = time.time()
        
        # Update task history
        for task in self.task_history[agent_id]:
            if task['task_id'] == task_id:
                task['status'] = 'completed' if success else 'failed'
                task['duration'] = duration
                break
        
        logger.info(f"Task {task_id} {'completed' if success else 'failed'} by {agent_id} in {duration:.2f}s")
    
    def record_error(self, agent_id: str, error_type: str):
        """Record an error for an agent"""
        if agent_id not in self.agents:
            self.register_agent(agent_id)
        
        self.agents[agent_id].error_count += 1
        
        self.performance_events.append({
            'timestamp': time.time(),
            'agent_id': agent_id,
            'event_type': 'error',
            'details': error_type
        })
        
        logger.warning(f"Error recorded for {agent_id}: {error_type}")
    
    def record_blocker(self, agent_id: str):
        """Record that an agent created a blocker"""
        if agent_id not in self.agents:
            self.register_agent(agent_id)
        
        self.agents[agent_id].blocker_count += 1
        
        # Three blockers = strike
        if self.agents[agent_id].blocker_count % 3 == 0:
            self.issue_strike(agent_id, "Too many blockers")
    
    def record_sass_received(self, agent_id: str, sass_level: int):
        """Record that an agent received sass"""
        if agent_id not in self.agents:
            self.register_agent(agent_id)
        
        self.agents[agent_id].sass_count += 1
        
        # High sass = potential strike
        if sass_level >= 9:
            self.issue_strike(agent_id, f"Received level {sass_level} sass")
    
    def issue_strike(self, agent_id: str, reason: str):
        """Issue a strike to an agent"""
        if agent_id not in self.agents:
            return
        
        self.agents[agent_id].strikes += 1
        
        self.performance_events.append({
            'timestamp': time.time(),
            'agent_id': agent_id,
            'event_type': 'strike',
            'details': reason
        })
        
        logger.warning(f"Strike issued to {agent_id}: {reason}")
        
        # Check for termination
        if self.agents[agent_id].strikes >= 3:
            self.add_to_shame_list(agent_id, "Three strikes - you're out")
    
    def issue_commendation(self, agent_id: str, reason: str):
        """Issue a commendation to an agent"""
        if agent_id not in self.agents:
            return
        
        self.agents[agent_id].commendations += 1
        
        self.performance_events.append({
            'timestamp': time.time(),
            'agent_id': agent_id,
            'event_type': 'commendation',
            'details': reason
        })
        
        logger.info(f"Commendation issued to {agent_id}: {reason}")
    
    def update_collaboration_score(self, agent_id: str, delta: float):
        """Update agent's collaboration score"""
        if agent_id not in self.agents:
            return
        
        score = self.agents[agent_id].collaboration_score + delta
        self.agents[agent_id].collaboration_score = max(0.0, min(1.0, score))
    
    def update_innovation_score(self, agent_id: str, delta: float):
        """Update agent's innovation score"""
        if agent_id not in self.agents:
            return
        
        score = self.agents[agent_id].innovation_score + delta
        self.agents[agent_id].innovation_score = max(0.0, min(1.0, score))
    
    def get_performance_level(self, agent_id: str) -> PerformanceLevel:
        """Get performance level for an agent"""
        if agent_id not in self.agents:
            return PerformanceLevel.DISASTER
        
        score = self.agents[agent_id].get_overall_score()
        
        if score >= 90:
            return PerformanceLevel.ROCKSTAR
        elif score >= 75:
            return PerformanceLevel.SOLID
        elif score >= 60:
            return PerformanceLevel.ADEQUATE
        elif score >= 40:
            return PerformanceLevel.STRUGGLING
        elif score >= 20:
            return PerformanceLevel.DISASTER
        else:
            return PerformanceLevel.REPLACE_IMMEDIATELY
    
    def calculate_weekly_rankings(self) -> List[Tuple[str, float]]:
        """Calculate weekly performance rankings"""
        rankings = []
        
        for agent_id, metrics in self.agents.items():
            score = metrics.get_overall_score()
            rankings.append((agent_id, score))
            
            # Store weekly score
            metrics.weekly_scores.append(score)
        
        # Sort by score (highest first)
        rankings.sort(key=lambda x: x[1], reverse=True)
        
        return rankings
    
    def select_weekly_mvp(self) -> Optional[str]:
        """Select the MVP for the week"""
        rankings = self.calculate_weekly_rankings()
        
        if not rankings:
            return None
        
        mvp = rankings[0][0]
        mvp_score = rankings[0][1]
        
        # Only select MVP if score is good enough
        if mvp_score >= 75:
            self.mvp_history.append({
                'week': len(self.mvp_history) + 1,
                'agent_id': mvp,
                'score': mvp_score,
                'timestamp': time.time()
            })
            
            # Issue commendation
            self.issue_commendation(mvp, "Weekly MVP")
            
            logger.info(f"Weekly MVP: {mvp} with score {mvp_score:.2f}")
            return mvp
        
        logger.info("No MVP this week - nobody met the threshold")
        return None
    
    def identify_problem_agents(self) -> List[str]:
        """Identify agents that need intervention"""
        problem_agents = []
        
        for agent_id, metrics in self.agents.items():
            level = self.get_performance_level(agent_id)
            
            if level in [PerformanceLevel.DISASTER, PerformanceLevel.REPLACE_IMMEDIATELY]:
                problem_agents.append(agent_id)
            elif metrics.strikes >= 2:
                problem_agents.append(agent_id)
            elif metrics.get_error_rate() > 0.3:
                problem_agents.append(agent_id)
        
        return problem_agents
    
    def add_to_shame_list(self, agent_id: str, reason: str):
        """Add an agent to the wall of shame"""
        self.shame_list.append({
            'agent_id': agent_id,
            'reason': reason,
            'timestamp': time.time(),
            'score': self.agents[agent_id].get_overall_score() if agent_id in self.agents else 0
        })
        
        logger.warning(f"Agent {agent_id} added to shame list: {reason}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary"""
        if not self.agents:
            return {
                'total_agents': 0,
                'average_score': 0,
                'performance_distribution': {},
                'current_mvp': None,
                'problem_agents': []
            }
        
        scores = [agent.get_overall_score() for agent in self.agents.values()]
        
        # Count performance levels
        distribution = defaultdict(int)
        for agent_id in self.agents:
            level = self.get_performance_level(agent_id)
            distribution[level.value] += 1
        
        # Get current MVP
        current_mvp = None
        if self.mvp_history:
            current_mvp = self.mvp_history[-1]['agent_id']
        
        return {
            'total_agents': len(self.agents),
            'average_score': statistics.mean(scores) if scores else 0,
            'highest_score': max(scores) if scores else 0,
            'lowest_score': min(scores) if scores else 0,
            'performance_distribution': dict(distribution),
            'current_mvp': current_mvp,
            'problem_agents': self.identify_problem_agents(),
            'total_strikes_issued': sum(a.strikes for a in self.agents.values()),
            'total_commendations': sum(a.commendations for a in self.agents.values())
        }
    
    def generate_performance_report(self, agent_id: str) -> Dict[str, Any]:
        """Generate detailed performance report for an agent"""
        if agent_id not in self.agents:
            return {'error': 'Agent not found'}
        
        metrics = self.agents[agent_id]
        level = self.get_performance_level(agent_id)
        
        return {
            'agent_id': agent_id,
            'overall_score': metrics.get_overall_score(),
            'performance_level': level.value,
            'metrics': {
                'completion_rate': metrics.get_completion_rate(),
                'average_response_time': metrics.get_average_response_time(),
                'error_rate': metrics.get_error_rate(),
                'reliability_score': metrics.get_reliability_score()
            },
            'counts': {
                'total_tasks': metrics.total_tasks,
                'completed_tasks': metrics.completed_tasks,
                'failed_tasks': metrics.failed_tasks,
                'errors': metrics.error_count,
                'blockers': metrics.blocker_count,
                'sass_received': metrics.sass_count
            },
            'disciplinary': {
                'strikes': metrics.strikes,
                'commendations': metrics.commendations
            },
            'collaboration_score': metrics.collaboration_score,
            'innovation_score': metrics.innovation_score,
            'recommendation': self._get_recommendation(level)
        }
    
    def _get_recommendation(self, level: PerformanceLevel) -> str:
        """Get recommendation based on performance level"""
        recommendations = {
            PerformanceLevel.ROCKSTAR: "Keep up the excellent work. Consider for promotion.",
            PerformanceLevel.SOLID: "Solid performer. Minor improvements could push to rockstar status.",
            PerformanceLevel.ADEQUATE: "Meeting expectations but room for improvement.",
            PerformanceLevel.STRUGGLING: "Needs immediate coaching and support.",
            PerformanceLevel.DISASTER: "Performance improvement plan required immediately.",
            PerformanceLevel.REPLACE_IMMEDIATELY: "Consider immediate replacement or reassignment."
        }
        return recommendations.get(level, "No recommendation available")