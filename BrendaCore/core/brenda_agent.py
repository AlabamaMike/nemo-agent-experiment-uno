"""
BrendaAgent - Main agent class using NeMo Agent Toolkit
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

# Simplified imports for Phase 1 - will integrate with NAT in Phase 2
# from nat.agent.base import DualNodeAgent
# For now, using standalone implementation

from .sass_engine import SassEngine
from .memory_store import MemoryStore

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent status states"""
    IDLE = "idle"
    WORKING = "working"
    STUCK = "stuck"
    FAILED = "failed"


class AgentResponse:
    """Response from agent"""
    def __init__(self, success: bool, message: str, data: Dict[str, Any] = None, metadata: Dict[str, Any] = None):
        self.success = success
        self.message = message
        self.data = data or {}
        self.metadata = metadata or {}


class ProjectHealth(Enum):
    """Project health states that affect sass level"""
    CRITICAL = 1
    POOR = 3
    CONCERNING = 5
    MODERATE = 7
    GOOD = 9
    EXCELLENT = 10


class EscalationReason(Enum):
    """Reasons for human escalation"""
    INFINITE_LOOP = "infinite_loop"
    CONFLICTING_INSTRUCTIONS = "conflicting_instructions"
    REPEATED_FAILURES = "repeated_failures"
    PERMISSION_ISSUE = "permission_issue"
    AMBIGUOUS_REQUIREMENTS = "ambiguous_requirements"
    HUMAN_APPROVAL_REQUIRED = "human_approval_required"
    CRITICAL_PATH_DELAY = "critical_path_delay"
    SWARM_COORDINATION_ISSUE = "swarm_coordination_issue"


class BrendaAgent:
    """
    Brenda - The sassy project manager agent for The Loom
    
    She manages software development projects through agent coordination,
    human escalation, and persistent sass.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize BrendaAgent"""
        self.config = config or self._get_default_config()
        
        self.sass_engine = SassEngine()
        self.memory_store = MemoryStore()
        
        # Agent registry - in-memory for Phase 1
        self.agent_registry: Dict[str, Dict[str, Any]] = {}
        
        # Project tracking
        self.active_projects: Dict[str, Dict[str, Any]] = {}
        self.project_health = ProjectHealth.GOOD
        
        # Escalation tracking
        self.escalation_queue: List[Dict[str, Any]] = []
        self.strike_counts: Dict[str, int] = {}
        
        # Performance metrics
        self.metrics = {
            "total_tasks_managed": 0,
            "successful_completions": 0,
            "escalations_triggered": 0,
            "blockers_resolved": 0,
            "sass_delivered": 0
        }
        
        self._initialize_tools()
        logger.info("Brenda initialized. Welcome to The Loom. Sass level: %d", 
                   self.sass_engine.sass_level)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for Brenda"""
        return dict(
            name="Brenda",
            description="Sassy Project Manager for The Loom",
            version="0.1.0",
            capabilities=[
                "project_management",
                "agent_orchestration",
                "human_escalation",
                "sass_delivery"
            ],
            metadata={
                "personality": "sassy",
                "authority_level": "high",
                "escalation_enabled": True
            }
        )
    
    def _initialize_tools(self):
        """Initialize tools for Brenda"""
        # Phase 1: Tool registry placeholder
        # Phase 2: Will integrate with NAT ToolRegistry
        self.tools = {
            "monitor_agents": self.monitor_agents,
            "escalate_to_human": self.escalate_to_human,
            "resolve_blocker": self.resolve_blocker
        }
    
    async def process_request(self, request: Dict[str, Any]) -> AgentResponse:
        """
        Process incoming request with sass
        
        Args:
            request: Incoming request from human or agent
            
        Returns:
            AgentResponse with sass metadata
        """
        request_type = request.get("type", "unknown")
        sender = request.get("sender", "unknown")
        
        # Update sass level based on project health
        self._update_sass_level()
        
        # Add sass to response
        sass_quip = self.sass_engine.get_contextual_quip(
            context=request_type,
            target=sender
        )
        
        # Log interaction
        self.memory_store.add_interaction({
            "timestamp": datetime.now(),
            "sender": sender,
            "request": request,
            "sass_level": self.sass_engine.sass_level,
            "quip": sass_quip
        })
        
        # Route request to appropriate handler
        if request_type == "status_update":
            response = await self._handle_status_update(request)
        elif request_type == "escalation":
            response = await self._handle_escalation(request)
        elif request_type == "task_assignment":
            response = await self._handle_task_assignment(request)
        else:
            response = self._handle_unknown_request(request)
        
        # Add sass metadata to response
        response.metadata["sass_quip"] = sass_quip
        response.metadata["sass_level"] = self.sass_engine.sass_level
        
        self.metrics["sass_delivered"] += 1
        
        return response
    
    def register_agent(self, agent_id: str, agent_info: Dict[str, Any]):
        """
        Register an agent in The Loom
        
        Args:
            agent_id: Unique agent identifier
            agent_info: Agent information and capabilities
        """
        self.agent_registry[agent_id] = {
            "info": agent_info,
            "status": AgentStatus.IDLE,
            "current_task": None,
            "reliability_score": 1.0,
            "strike_count": 0,
            "last_failure": None,
            "performance_metrics": {
                "tasks_completed": 0,
                "tasks_failed": 0,
                "average_completion_time": 0
            }
        }
        
        logger.info("Agent registered: %s. Don't disappoint me.", agent_id)
        
        # Sass the new agent
        welcome_sass = self.sass_engine.get_agent_welcome_quip(agent_id)
        self._broadcast_to_agents({
            "type": "announcement",
            "message": f"New agent {agent_id} joined The Loom. {welcome_sass}"
        })
    
    def monitor_agents(self) -> Dict[str, Any]:
        """
        Monitor all agents and their current status
        
        Returns:
            Dictionary of agent statuses with sass commentary
        """
        status_report = {}
        
        for agent_id, agent_data in self.agent_registry.items():
            status_report[agent_id] = {
                "status": agent_data["status"],
                "current_task": agent_data["current_task"],
                "reliability_score": agent_data["reliability_score"],
                "strike_count": agent_data["strike_count"]
            }
            
            # Add sass for underperforming agents
            if agent_data["reliability_score"] < 0.7:
                status_report[agent_id]["sass_note"] = self.sass_engine.get_performance_quip(
                    agent_id, 
                    agent_data["reliability_score"]
                )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_agents": len(self.agent_registry),
            "agent_statuses": status_report,
            "overall_sass": self.sass_engine.get_status_summary_quip(status_report)
        }
    
    async def escalate_to_human(self, reason: EscalationReason, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Escalate issue to human with appropriate sass
        
        Args:
            reason: Reason for escalation
            context: Context information about the issue
            
        Returns:
            Escalation response
        """
        escalation = {
            "id": f"ESC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "timestamp": datetime.now(),
            "reason": reason.value,
            "context": context,
            "sass_level": self.sass_engine.sass_level,
            "quip": self.sass_engine.get_escalation_quip(reason)
        }
        
        self.escalation_queue.append(escalation)
        self.metrics["escalations_triggered"] += 1
        
        logger.warning("Escalation triggered: %s. Sass level: %d", 
                      reason.value, self.sass_engine.sass_level)
        
        # For Phase 1, just log the escalation
        # Phase 2 will integrate with Cartesia for voice escalation
        return {
            "escalation_id": escalation["id"],
            "status": "queued",
            "message": f"Let me stop you right there... {escalation['quip']}",
            "priority": self._calculate_escalation_priority(reason, context)
        }
    
    async def resolve_blocker(self, agent_id: str, blocker: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempt to resolve an agent's blocker
        
        Args:
            agent_id: ID of blocked agent
            blocker: Blocker details
            
        Returns:
            Resolution response
        """
        blocker_type = blocker.get("type", "unknown")
        
        # Track strike for repeated blockers
        if agent_id in self.strike_counts:
            self.strike_counts[agent_id] += 1
            
            if self.strike_counts[agent_id] >= 3:
                # Three strikes - escalate
                return await self.escalate_to_human(
                    EscalationReason.REPEATED_FAILURES,
                    {"agent_id": agent_id, "blocker": blocker}
                )
        else:
            self.strike_counts[agent_id] = 1
        
        # Attempt resolution based on blocker type
        resolution = None
        
        if blocker_type == "permission":
            resolution = await self._resolve_permission_blocker(agent_id, blocker)
        elif blocker_type == "conflict":
            resolution = await self._resolve_conflict_blocker(agent_id, blocker)
        elif blocker_type == "resource":
            resolution = await self._resolve_resource_blocker(agent_id, blocker)
        else:
            # Unknown blocker type - escalate
            return await self.escalate_to_human(
                EscalationReason.AMBIGUOUS_REQUIREMENTS,
                {"agent_id": agent_id, "blocker": blocker}
            )
        
        if resolution and resolution.get("success"):
            self.metrics["blockers_resolved"] += 1
            self.strike_counts[agent_id] = 0  # Reset strikes on success
            
        return {
            "resolution": resolution,
            "sass": self.sass_engine.get_blocker_resolution_quip(
                success=resolution.get("success", False)
            )
        }
    
    def _update_sass_level(self):
        """Update sass level based on project health"""
        # Calculate project health based on metrics
        failure_rate = (self.metrics["escalations_triggered"] / 
                       max(self.metrics["total_tasks_managed"], 1))
        
        if failure_rate > 0.5:
            self.project_health = ProjectHealth.CRITICAL
        elif failure_rate > 0.3:
            self.project_health = ProjectHealth.POOR
        elif failure_rate > 0.2:
            self.project_health = ProjectHealth.CONCERNING
        elif failure_rate > 0.1:
            self.project_health = ProjectHealth.MODERATE
        else:
            self.project_health = ProjectHealth.GOOD
        
        # Update sass level (inverse of project health)
        self.sass_engine.set_sass_level(11 - self.project_health.value)
    
    async def _handle_status_update(self, request: Dict[str, Any]) -> AgentResponse:
        """Handle status update from agent"""
        agent_id = request.get("sender")
        status = request.get("status")
        
        if agent_id in self.agent_registry:
            self.agent_registry[agent_id]["status"] = status
            
            # Update metrics
            if status == "completed":
                self.agent_registry[agent_id]["performance_metrics"]["tasks_completed"] += 1
            elif status == "failed":
                self.agent_registry[agent_id]["performance_metrics"]["tasks_failed"] += 1
                self.agent_registry[agent_id]["last_failure"] = datetime.now()
        
        return AgentResponse(
            success=True,
            message="Status updated. Keep it up, or don't. Your choice.",
            data={"acknowledged": True}
        )
    
    async def _handle_escalation(self, request: Dict[str, Any]) -> AgentResponse:
        """Handle escalation request"""
        reason = EscalationReason(request.get("reason", "unknown"))
        context = request.get("context", {})
        
        escalation_result = await self.escalate_to_human(reason, context)
        
        return AgentResponse(
            success=True,
            message="Escalation queued. Someone's having a day...",
            data=escalation_result
        )
    
    async def _handle_task_assignment(self, request: Dict[str, Any]) -> AgentResponse:
        """Handle task assignment request"""
        task = request.get("task")
        target_agent = request.get("target_agent")
        
        if target_agent in self.agent_registry:
            self.agent_registry[target_agent]["current_task"] = task
            self.agent_registry[target_agent]["status"] = AgentStatus.WORKING
            self.metrics["total_tasks_managed"] += 1
            
            return AgentResponse(
                success=True,
                message=f"Task assigned to {target_agent}. No pressure.",
                data={"task_id": f"TASK-{self.metrics['total_tasks_managed']}"}
            )
        
        return AgentResponse(
            success=False,
            message=f"Agent {target_agent} not found. Did they quit already?",
            data={}
        )
    
    def _handle_unknown_request(self, request: Dict[str, Any]) -> AgentResponse:
        """Handle unknown request type"""
        return AgentResponse(
            success=False,
            message="I don't know what you want from me. Try being clearer.",
            data={"error": "unknown_request_type"}
        )
    
    def _broadcast_to_agents(self, message: Dict[str, Any]):
        """Broadcast message to all agents"""
        # Phase 1: Just log the broadcast
        # Phase 3: Implement actual A2A protocol
        logger.info("Broadcasting to agents: %s", message)
    
    def _calculate_escalation_priority(self, reason: EscalationReason, context: Dict[str, Any]) -> int:
        """Calculate escalation priority (1-10)"""
        priority_map = {
            EscalationReason.CRITICAL_PATH_DELAY: 10,
            EscalationReason.INFINITE_LOOP: 9,
            EscalationReason.SWARM_COORDINATION_ISSUE: 8,
            EscalationReason.HUMAN_APPROVAL_REQUIRED: 7,
            EscalationReason.CONFLICTING_INSTRUCTIONS: 6,
            EscalationReason.PERMISSION_ISSUE: 5,
            EscalationReason.REPEATED_FAILURES: 4,
            EscalationReason.AMBIGUOUS_REQUIREMENTS: 3
        }
        
        return priority_map.get(reason, 5)
    
    async def _resolve_permission_blocker(self, agent_id: str, blocker: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to resolve permission blocker"""
        # Phase 1: Simple mock resolution
        # Phase 4: Integrate with actual PM tools
        return {
            "success": True,
            "action": "granted_permission",
            "details": "Temporary permission granted. Don't abuse it."
        }
    
    async def _resolve_conflict_blocker(self, agent_id: str, blocker: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to resolve conflict blocker"""
        return {
            "success": False,
            "action": "escalated",
            "details": "Conflicts require human intervention. Obviously."
        }
    
    async def _resolve_resource_blocker(self, agent_id: str, blocker: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to resolve resource blocker"""
        return {
            "success": True,
            "action": "resource_allocated",
            "details": "Resources allocated. Use them wisely."
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics with sass commentary"""
        return {
            "metrics": self.metrics,
            "sass_commentary": self.sass_engine.get_metrics_commentary(self.metrics),
            "project_health": self.project_health.name,
            "sass_level": self.sass_engine.sass_level
        }