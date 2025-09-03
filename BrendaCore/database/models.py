"""
Database Models for BrendaCore
SQLAlchemy models for PostgreSQL
"""

from datetime import datetime
from typing import Optional
from enum import Enum as PyEnum

# Note: In production, would use SQLAlchemy
# from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, ForeignKey, Text, Enum
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import relationship
# from sqlalchemy.dialects.postgresql import UUID

# Mock for development
class Column:
    def __init__(self, type_, **kwargs):
        self.type = type_
        self.kwargs = kwargs

class Integer: pass
class String: 
    def __init__(self, length=None):
        self.length = length
class Float: pass
class DateTime: pass
class Boolean: pass
class JSON: pass
class Text: pass
class ForeignKey:
    def __init__(self, ref):
        self.ref = ref

def relationship(model, **kwargs):
    return f"relationship({model})"

# Base = declarative_base()
class Base:
    """Mock base class"""
    pass


class AgentStatus(PyEnum):
    """Agent status enum"""
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    TERMINATED = "terminated"


class TaskStatus(PyEnum):
    """Task status enum"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


class Agent(Base):
    """Agent model"""
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True)
    agent_id = Column(String(100), unique=True, nullable=False, index=True)
    agent_type = Column(String(50), nullable=False)
    status = Column(String(20), default=AgentStatus.IDLE.value)
    
    # Performance metrics
    overall_score = Column(Float, default=50.0)
    reliability_score = Column(Float, default=0.5)
    collaboration_score = Column(Float, default=0.5)
    innovation_score = Column(Float, default=0.5)
    
    # Counters
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    blocker_count = Column(Integer, default=0)
    sass_received = Column(Integer, default=0)
    strikes = Column(Integer, default=0)
    commendations = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tasks = relationship("Task", back_populates="agent")
    interactions = relationship("Interaction", back_populates="agent")
    metrics = relationship("Metrics", back_populates="agent")
    
    def __repr__(self):
        return f"<Agent(agent_id={self.agent_id}, score={self.overall_score})>"


class Project(Base):
    """Project model"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    phase = Column(String(50), default="planning")
    
    # Health metrics
    health_score = Column(Float, default=50.0)
    health_status = Column(String(20), default="fair")
    sass_level = Column(Integer, default=5)
    
    # Project metrics
    velocity_daily = Column(Float, default=0.0)
    velocity_weekly = Column(Float, default=0.0)
    open_issues = Column(Integer, default=0)
    closed_issues = Column(Integer, default=0)
    open_prs = Column(Integer, default=0)
    merged_prs = Column(Integer, default=0)
    
    # Risk metrics
    blocker_count = Column(Integer, default=0)
    technical_debt = Column(Float, default=0.0)
    security_issues = Column(Integer, default=0)
    
    # Metadata
    platforms = Column(JSON)  # List of platforms (GitHub, Jira, etc.)
    team_members = Column(JSON)  # List of team member IDs
    configuration = Column(JSON)  # Project-specific config
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_health_check = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tasks = relationship("Task", back_populates="project")
    metrics = relationship("Metrics", back_populates="project")
    
    def __repr__(self):
        return f"<Project(name={self.name}, health={self.health_score})>"


class Task(Base):
    """Task model"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True)
    task_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    task_type = Column(String(50))  # pr, issue, deployment, etc.
    
    # Status and priority
    status = Column(String(20), default=TaskStatus.PENDING.value)
    priority = Column(Integer, default=5)
    
    # Assignment
    agent_id = Column(Integer, ForeignKey("agents.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    
    # Metrics
    estimated_hours = Column(Float)
    actual_hours = Column(Float)
    completion_percentage = Column(Float, default=0.0)
    
    # Blocker tracking
    is_blocked = Column(Boolean, default=False)
    blocker_reason = Column(Text)
    blocker_count = Column(Integer, default=0)
    
    # Metadata
    metadata = Column(JSON)  # Additional task-specific data
    labels = Column(JSON)  # List of labels
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    assigned_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    agent = relationship("Agent", back_populates="tasks")
    project = relationship("Project", back_populates="tasks")
    
    def __repr__(self):
        return f"<Task(task_id={self.task_id}, status={self.status})>"


class Interaction(Base):
    """Interaction/Communication model"""
    __tablename__ = "interactions"
    
    id = Column(Integer, primary_key=True)
    interaction_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Participants
    sender_id = Column(Integer, ForeignKey("agents.id"))
    recipient_id = Column(String(100))  # Can be agent_id or "broadcast"
    
    # Message details
    message_type = Column(String(50))  # request, response, sass, etc.
    subject = Column(String(500))
    content = Column(Text)
    
    # Sass metadata
    sass_level = Column(Integer, default=0)
    quip = Column(Text)
    frustration_factor = Column(Float, default=0.0)
    
    # Context
    context = Column(JSON)  # Additional context data
    thread_id = Column(String(100), index=True)
    correlation_id = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    agent = relationship("Agent", back_populates="interactions")
    
    def __repr__(self):
        return f"<Interaction(type={self.message_type}, sass={self.sass_level})>"


class Metrics(Base):
    """Time-series metrics model"""
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True)
    
    # References
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    
    # Metric details
    metric_type = Column(String(50), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    
    # Additional data
    tags = Column(JSON)  # Key-value tags
    metadata = Column(JSON)  # Additional metric data
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    agent = relationship("Agent", back_populates="metrics")
    project = relationship("Project", back_populates="metrics")
    
    def __repr__(self):
        return f"<Metrics(type={self.metric_type}, value={self.metric_value})>"


class SassQuip(Base):
    """Sass quips storage"""
    __tablename__ = "sass_quips"
    
    id = Column(Integer, primary_key=True)
    category = Column(String(50), nullable=False, index=True)
    sass_level = Column(Integer, nullable=False, index=True)
    quip = Column(Text, nullable=False)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime)
    effectiveness_score = Column(Float, default=0.5)
    
    # Metadata
    tags = Column(JSON)  # List of tags
    context_triggers = Column(JSON)  # Conditions that trigger this quip
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SassQuip(level={self.sass_level}, category={self.category})>"


class AuditLog(Base):
    """Audit log for compliance and debugging"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    
    # Event details
    event_type = Column(String(50), nullable=False, index=True)
    event_action = Column(String(100), nullable=False)
    event_result = Column(String(20))  # success, failure, error
    
    # Actor
    actor_type = Column(String(50))  # agent, system, user
    actor_id = Column(String(100))
    
    # Target
    target_type = Column(String(50))  # task, project, agent, etc.
    target_id = Column(String(100))
    
    # Details
    description = Column(Text)
    metadata = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<AuditLog(event={self.event_type}:{self.event_action})>"


class Configuration(Base):
    """System configuration storage"""
    __tablename__ = "configurations"
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=False)
    
    # Metadata
    description = Column(Text)
    category = Column(String(50))
    is_sensitive = Column(Boolean, default=False)
    
    # Versioning
    version = Column(Integer, default=1)
    previous_value = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100))
    
    def __repr__(self):
        return f"<Configuration(key={self.key}, version={self.version})>"