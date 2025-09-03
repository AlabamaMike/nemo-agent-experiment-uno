"""
Agent-to-Agent (A2A) Communication Protocol
Enables structured communication between agents with sass metadata
"""

import json
import uuid
import time
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of A2A messages"""
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    ESCALATION = "escalation"
    STATUS_UPDATE = "status_update"
    TASK_ASSIGNMENT = "task_assignment"
    BLOCKER = "blocker"
    COMPLETION = "completion"
    ERROR = "error"
    SASS = "sass"  # Pure sass messages from Brenda


class Priority(Enum):
    """Message priority levels"""
    LOW = 1
    MEDIUM = 5
    HIGH = 7
    CRITICAL = 9
    EMERGENCY = 10


@dataclass
class SassMetadata:
    """Sass-related metadata for messages"""
    sass_level: int = 0
    quip: Optional[str] = None
    frustration_factor: float = 0.0
    contains_threat: bool = False
    eye_roll_count: int = 0


@dataclass
class A2AMessage:
    """Standard A2A message format"""
    # Core fields
    message_id: str
    sender_id: str
    recipient_id: str  # Use "broadcast" for all agents
    message_type: MessageType
    timestamp: float
    
    # Content
    subject: str
    payload: Dict[str, Any]
    
    # Metadata
    priority: Priority = Priority.MEDIUM
    sass_metadata: Optional[SassMetadata] = None
    requires_response: bool = False
    correlation_id: Optional[str] = None  # For request-response pairs
    thread_id: Optional[str] = None  # For conversation threads
    
    # Routing
    ttl: int = 5  # Time to live (hop count)
    visited_agents: List[str] = None
    
    def __post_init__(self):
        if self.visited_agents is None:
            self.visited_agents = []
        if self.sass_metadata is None:
            self.sass_metadata = SassMetadata()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        data = asdict(self)
        data['message_type'] = self.message_type.value
        data['priority'] = self.priority.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'A2AMessage':
        """Create message from dictionary"""
        data['message_type'] = MessageType(data['message_type'])
        data['priority'] = Priority(data['priority'])
        if data.get('sass_metadata'):
            data['sass_metadata'] = SassMetadata(**data['sass_metadata'])
        return cls(**data)


class A2AProtocol:
    """
    Agent-to-Agent Communication Protocol
    Manages message creation, validation, and routing
    """
    
    VERSION = "1.0"
    
    def __init__(self, agent_id: str = "brenda-pm"):
        self.agent_id = agent_id
        self.message_handlers = {}
        self.message_log = []
        self.response_callbacks = {}
        self.blocked_agents = set()  # Agents on Brenda's naughty list
        
        logger.info(f"A2A Protocol initialized for agent: {agent_id}")
    
    def create_message(
        self,
        recipient_id: str,
        message_type: MessageType,
        subject: str,
        payload: Dict[str, Any],
        priority: Priority = Priority.MEDIUM,
        sass_level: int = 0,
        quip: Optional[str] = None,
        requires_response: bool = False,
        correlation_id: Optional[str] = None,
        thread_id: Optional[str] = None
    ) -> A2AMessage:
        """Create a new A2A message"""
        
        sass_metadata = SassMetadata(
            sass_level=sass_level,
            quip=quip,
            frustration_factor=sass_level / 11.0,
            contains_threat=sass_level >= 9,
            eye_roll_count=max(0, sass_level - 5)
        )
        
        message = A2AMessage(
            message_id=str(uuid.uuid4()),
            sender_id=self.agent_id,
            recipient_id=recipient_id,
            message_type=message_type,
            timestamp=time.time(),
            subject=subject,
            payload=payload,
            priority=priority,
            sass_metadata=sass_metadata,
            requires_response=requires_response,
            correlation_id=correlation_id,
            thread_id=thread_id or str(uuid.uuid4())
        )
        
        logger.info(f"Created {message_type.value} message: {subject} -> {recipient_id}")
        return message
    
    def send_request(
        self,
        recipient_id: str,
        subject: str,
        payload: Dict[str, Any],
        priority: Priority = Priority.MEDIUM,
        sass_level: int = 0,
        timeout: float = 30.0
    ) -> A2AMessage:
        """Send a request message expecting a response"""
        message = self.create_message(
            recipient_id=recipient_id,
            message_type=MessageType.REQUEST,
            subject=subject,
            payload=payload,
            priority=priority,
            sass_level=sass_level,
            requires_response=True
        )
        
        # Store callback for response handling
        self.response_callbacks[message.message_id] = {
            'timeout': time.time() + timeout,
            'callback': None
        }
        
        self._send_message(message)
        return message
    
    def send_response(
        self,
        original_message: A2AMessage,
        payload: Dict[str, Any],
        sass_level: int = 0,
        quip: Optional[str] = None
    ) -> A2AMessage:
        """Send a response to a request"""
        message = self.create_message(
            recipient_id=original_message.sender_id,
            message_type=MessageType.RESPONSE,
            subject=f"Re: {original_message.subject}",
            payload=payload,
            priority=original_message.priority,
            sass_level=sass_level,
            quip=quip,
            correlation_id=original_message.message_id,
            thread_id=original_message.thread_id
        )
        
        self._send_message(message)
        return message
    
    def broadcast(
        self,
        subject: str,
        payload: Dict[str, Any],
        priority: Priority = Priority.MEDIUM,
        sass_level: int = 0,
        quip: Optional[str] = None
    ) -> A2AMessage:
        """Broadcast message to all agents"""
        message = self.create_message(
            recipient_id="broadcast",
            message_type=MessageType.BROADCAST,
            subject=subject,
            payload=payload,
            priority=priority,
            sass_level=sass_level,
            quip=quip
        )
        
        self._send_message(message)
        return message
    
    def send_sass(
        self,
        recipient_id: str,
        sass_level: int,
        quip: str,
        context: Optional[Dict[str, Any]] = None
    ) -> A2AMessage:
        """Send a pure sass message (Brenda's specialty)"""
        payload = {
            'sass_delivered': True,
            'context': context or {},
            'message': quip
        }
        
        message = self.create_message(
            recipient_id=recipient_id,
            message_type=MessageType.SASS,
            subject="Incoming Sass",
            payload=payload,
            priority=Priority.LOW,  # Sass is never urgent, just necessary
            sass_level=sass_level,
            quip=quip
        )
        
        logger.info(f"Sass level {sass_level} delivered to {recipient_id}: {quip[:50]}...")
        self._send_message(message)
        return message
    
    def report_blocker(
        self,
        blocker_description: str,
        blocking_agents: List[str],
        priority: Priority = Priority.HIGH,
        sass_level: int = 7
    ) -> A2AMessage:
        """Report a blocker to all relevant agents"""
        payload = {
            'blocker': blocker_description,
            'blocking_agents': blocking_agents,
            'reported_at': time.time(),
            'status': 'active'
        }
        
        message = self.create_message(
            recipient_id="broadcast",
            message_type=MessageType.BLOCKER,
            subject=f"BLOCKER: {blocker_description[:50]}",
            payload=payload,
            priority=priority,
            sass_level=sass_level,
            quip="Another day, another blocker. How refreshing."
        )
        
        self._send_message(message)
        return message
    
    def _send_message(self, message: A2AMessage):
        """Internal method to send message (implement transport here)"""
        # Add to visited agents
        message.visited_agents.append(self.agent_id)
        
        # Check if recipient is blocked
        if message.recipient_id in self.blocked_agents:
            logger.warning(f"Message to {message.recipient_id} blocked - agent on naughty list")
            return
        
        # Log the message
        self.message_log.append(message)
        
        # In production, this would use actual transport (Redis, RabbitMQ, etc.)
        logger.info(f"Message sent: {message.message_id} -> {message.recipient_id}")
        
        # For now, just trigger local handlers for demo
        if message.recipient_id in self.message_handlers:
            self.message_handlers[message.recipient_id](message)
    
    def receive_message(self, message: A2AMessage):
        """Process received message"""
        # Check TTL
        if message.ttl <= 0:
            logger.warning(f"Message {message.message_id} dropped - TTL expired")
            return
        
        message.ttl -= 1
        
        # Check for loops
        if self.agent_id in message.visited_agents:
            logger.warning(f"Message {message.message_id} detected in loop")
            return
        
        # Log receipt
        logger.info(f"Received {message.message_type.value} from {message.sender_id}: {message.subject}")
        
        # Handle response correlation
        if message.message_type == MessageType.RESPONSE and message.correlation_id:
            if message.correlation_id in self.response_callbacks:
                callback_info = self.response_callbacks.pop(message.correlation_id)
                if callback_info['callback']:
                    callback_info['callback'](message)
        
        # Trigger registered handlers
        if message.message_type in self.message_handlers:
            self.message_handlers[message.message_type](message)
    
    def register_handler(self, message_type: MessageType, handler):
        """Register a handler for a message type"""
        self.message_handlers[message_type] = handler
        logger.info(f"Registered handler for {message_type.value}")
    
    def block_agent(self, agent_id: str, reason: str):
        """Add agent to blocked list (Brenda's naughty list)"""
        self.blocked_agents.add(agent_id)
        logger.warning(f"Agent {agent_id} blocked: {reason}")
        
        # Send sass about it
        self.send_sass(
            agent_id,
            sass_level=9,
            quip=f"Congratulations {agent_id}, you've made the naughty list. {reason}",
            context={'action': 'blocked', 'reason': reason}
        )
    
    def unblock_agent(self, agent_id: str):
        """Remove agent from blocked list"""
        self.blocked_agents.discard(agent_id)
        logger.info(f"Agent {agent_id} unblocked - mercy granted")
    
    def get_message_stats(self) -> Dict[str, Any]:
        """Get protocol statistics"""
        stats = {
            'total_messages': len(self.message_log),
            'messages_by_type': {},
            'average_sass_level': 0,
            'blocked_agents': list(self.blocked_agents),
            'pending_responses': len(self.response_callbacks)
        }
        
        # Calculate stats
        sass_total = 0
        for msg in self.message_log:
            msg_type = msg.message_type.value
            stats['messages_by_type'][msg_type] = stats['messages_by_type'].get(msg_type, 0) + 1
            sass_total += msg.sass_metadata.sass_level
        
        if self.message_log:
            stats['average_sass_level'] = sass_total / len(self.message_log)
        
        return stats