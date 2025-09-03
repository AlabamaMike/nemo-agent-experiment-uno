"""
Project Registry and Health Scoring
Central registry for all projects across platforms with health metrics
"""

import time
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import statistics
import logging

logger = logging.getLogger(__name__)


class ProjectHealth(Enum):
    """Project health levels"""
    CRITICAL = "critical"      # Immediate intervention needed
    UNHEALTHY = "unhealthy"    # Major issues present
    AT_RISK = "at_risk"        # Trending poorly
    FAIR = "fair"              # Some concerns
    HEALTHY = "healthy"        # On track
    EXCELLENT = "excellent"    # Exceeding expectations


class ProjectPhase(Enum):
    """Project phases"""
    PLANNING = "planning"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "maintenance"
    COMPLETED = "completed"


@dataclass
class ProjectMetrics:
    """Project metrics and statistics"""
    # Velocity metrics
    velocity_daily: float = 0.0
    velocity_weekly: float = 0.0
    velocity_trend: str = "stable"  # increasing, stable, decreasing
    
    # Issue metrics
    open_issues: int = 0
    closed_issues: int = 0
    issue_resolution_time: float = 0.0  # Average in hours
    bug_rate: float = 0.0  # Bugs per day
    
    # PR metrics
    open_prs: int = 0
    merged_prs: int = 0
    pr_review_time: float = 0.0  # Average in hours
    pr_rejection_rate: float = 0.0
    
    # Code metrics
    code_coverage: float = 0.0
    test_pass_rate: float = 0.0
    build_success_rate: float = 0.0
    deployment_frequency: float = 0.0  # Per week
    
    # Team metrics
    active_contributors: int = 0
    commit_frequency: float = 0.0  # Per day
    collaboration_score: float = 0.0
    
    # Risk metrics
    blocker_count: int = 0
    technical_debt: float = 0.0
    security_issues: int = 0
    
    def calculate_health_score(self) -> float:
        """Calculate overall health score (0-100)"""
        score = 50.0  # Base score
        
        # Velocity factors
        if self.velocity_trend == "increasing":
            score += 5
        elif self.velocity_trend == "decreasing":
            score -= 10
        
        # Issue management
        if self.open_issues > 50:
            score -= 15
        elif self.open_issues < 10:
            score += 5
        
        if self.issue_resolution_time > 168:  # More than a week
            score -= 10
        elif self.issue_resolution_time < 24:  # Less than a day
            score += 10
        
        # PR health
        if self.pr_review_time > 48:  # More than 2 days
            score -= 10
        elif self.pr_review_time < 4:  # Less than 4 hours
            score += 10
        
        if self.pr_rejection_rate > 0.3:
            score -= 5
        
        # Code quality
        if self.code_coverage < 0.5:
            score -= 15
        elif self.code_coverage > 0.8:
            score += 10
        
        if self.test_pass_rate < 0.8:
            score -= 20
        elif self.test_pass_rate > 0.95:
            score += 10
        
        if self.build_success_rate < 0.7:
            score -= 15
        elif self.build_success_rate > 0.9:
            score += 5
        
        # Team health
        if self.active_contributors < 2:
            score -= 10
        elif self.active_contributors > 5:
            score += 5
        
        # Risk factors
        score -= self.blocker_count * 5
        score -= self.security_issues * 10
        
        return max(0, min(100, score))


@dataclass
class Project:
    """Project representation"""
    project_id: str
    name: str
    description: str
    created_at: datetime
    phase: ProjectPhase
    platforms: List[str]  # GitHub, Jira, etc.
    team_members: List[str]
    
    metrics: ProjectMetrics = field(default_factory=ProjectMetrics)
    health_history: List[Tuple[datetime, float]] = field(default_factory=list)
    
    # Sass-related
    sass_level: int = 5
    last_escalation: Optional[datetime] = None
    escalation_count: int = 0
    
    def update_health(self):
        """Update project health score"""
        score = self.metrics.calculate_health_score()
        self.health_history.append((datetime.now(), score))
        
        # Keep only last 30 days
        cutoff = datetime.now() - timedelta(days=30)
        self.health_history = [
            (dt, score) for dt, score in self.health_history
            if dt > cutoff
        ]
        
        # Update sass level based on health
        if score < 20:
            self.sass_level = 10
        elif score < 40:
            self.sass_level = 8
        elif score < 60:
            self.sass_level = 6
        elif score < 80:
            self.sass_level = 4
        else:
            self.sass_level = 2
    
    def get_current_health(self) -> ProjectHealth:
        """Get current project health status"""
        if not self.health_history:
            self.update_health()
        
        if self.health_history:
            score = self.health_history[-1][1]
        else:
            score = self.metrics.calculate_health_score()
        
        if score < 20:
            return ProjectHealth.CRITICAL
        elif score < 40:
            return ProjectHealth.UNHEALTHY
        elif score < 55:
            return ProjectHealth.AT_RISK
        elif score < 70:
            return ProjectHealth.FAIR
        elif score < 85:
            return ProjectHealth.HEALTHY
        else:
            return ProjectHealth.EXCELLENT
    
    def get_health_trend(self) -> str:
        """Get health trend over recent period"""
        if len(self.health_history) < 2:
            return "insufficient_data"
        
        # Compare last week to previous week
        one_week_ago = datetime.now() - timedelta(days=7)
        two_weeks_ago = datetime.now() - timedelta(days=14)
        
        recent_scores = [
            score for dt, score in self.health_history
            if dt > one_week_ago
        ]
        
        older_scores = [
            score for dt, score in self.health_history
            if two_weeks_ago < dt <= one_week_ago
        ]
        
        if recent_scores and older_scores:
            recent_avg = statistics.mean(recent_scores)
            older_avg = statistics.mean(older_scores)
            
            if recent_avg > older_avg + 5:
                return "improving"
            elif recent_avg < older_avg - 5:
                return "declining"
            else:
                return "stable"
        
        return "insufficient_data"
    
    def needs_intervention(self) -> bool:
        """Check if project needs intervention"""
        health = self.get_current_health()
        
        return health in [ProjectHealth.CRITICAL, ProjectHealth.UNHEALTHY] or \
               self.metrics.blocker_count > 3 or \
               self.metrics.security_issues > 0 or \
               self.get_health_trend() == "declining"


class ProjectRegistry:
    """
    Central registry for all projects
    """
    
    def __init__(self):
        self.projects = {}
        self.platform_mappings = {}  # platform:id -> project_id
        self.health_alerts = []
        self.intervention_queue = []
        
        logger.info("ProjectRegistry initialized")
    
    def register_project(
        self,
        name: str,
        description: str,
        platforms: List[str],
        team_members: List[str] = None
    ) -> Project:
        """Register a new project"""
        project_id = f"proj_{name.lower().replace(' ', '_')}_{int(time.time())}"
        
        project = Project(
            project_id=project_id,
            name=name,
            description=description,
            created_at=datetime.now(),
            phase=ProjectPhase.PLANNING,
            platforms=platforms,
            team_members=team_members or []
        )
        
        self.projects[project_id] = project
        
        # Create platform mappings
        for platform in platforms:
            self.platform_mappings[f"{platform}:{name}"] = project_id
        
        logger.info(f"Registered project: {project_id}")
        return project
    
    def update_project_metrics(
        self,
        project_id: str,
        metrics_update: Dict[str, Any]
    ):
        """Update project metrics"""
        if project_id not in self.projects:
            logger.error(f"Project {project_id} not found")
            return
        
        project = self.projects[project_id]
        
        # Update metrics
        for key, value in metrics_update.items():
            if hasattr(project.metrics, key):
                setattr(project.metrics, key, value)
        
        # Update health
        project.update_health()
        
        # Check for alerts
        if project.needs_intervention():
            self._create_health_alert(project)
    
    def _create_health_alert(self, project: Project):
        """Create health alert for project"""
        alert = {
            'project_id': project.project_id,
            'project_name': project.name,
            'health': project.get_current_health().value,
            'sass_level': project.sass_level,
            'timestamp': datetime.now(),
            'reason': self._get_alert_reason(project)
        }
        
        self.health_alerts.append(alert)
        self.intervention_queue.append(project.project_id)
        
        logger.warning(f"Health alert for {project.name}: {alert['reason']}")
    
    def _get_alert_reason(self, project: Project) -> str:
        """Get reason for health alert"""
        reasons = []
        
        if project.get_current_health() == ProjectHealth.CRITICAL:
            reasons.append("Critical health status")
        
        if project.metrics.blocker_count > 3:
            reasons.append(f"{project.metrics.blocker_count} blockers")
        
        if project.metrics.security_issues > 0:
            reasons.append(f"{project.metrics.security_issues} security issues")
        
        if project.get_health_trend() == "declining":
            reasons.append("Declining health trend")
        
        if project.metrics.build_success_rate < 0.5:
            reasons.append("Build failures")
        
        return " | ".join(reasons) if reasons else "General concern"
    
    def get_project_by_platform(
        self,
        platform: str,
        platform_id: str
    ) -> Optional[Project]:
        """Get project by platform identifier"""
        mapping_key = f"{platform}:{platform_id}"
        
        if mapping_key in self.platform_mappings:
            project_id = self.platform_mappings[mapping_key]
            return self.projects.get(project_id)
        
        return None
    
    def get_projects_needing_attention(self) -> List[Project]:
        """Get projects that need attention"""
        return [
            project for project in self.projects.values()
            if project.needs_intervention()
        ]
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary"""
        if not self.projects:
            return {
                'total_projects': 0,
                'health_distribution': {},
                'average_health': 0,
                'critical_projects': [],
                'trending': {}
            }
        
        health_distribution = {
            health.value: 0 for health in ProjectHealth
        }
        
        health_scores = []
        critical_projects = []
        trending = {'improving': 0, 'stable': 0, 'declining': 0}
        
        for project in self.projects.values():
            health = project.get_current_health()
            health_distribution[health.value] += 1
            
            if project.health_history:
                health_scores.append(project.health_history[-1][1])
            
            if health in [ProjectHealth.CRITICAL, ProjectHealth.UNHEALTHY]:
                critical_projects.append(project.name)
            
            trend = project.get_health_trend()
            if trend in trending:
                trending[trend] += 1
        
        return {
            'total_projects': len(self.projects),
            'health_distribution': health_distribution,
            'average_health': statistics.mean(health_scores) if health_scores else 0,
            'critical_projects': critical_projects,
            'trending': trending,
            'recent_alerts': self.health_alerts[-5:],
            'intervention_queue_size': len(self.intervention_queue)
        }
    
    def generate_health_report(self, project_id: str) -> Dict[str, Any]:
        """Generate detailed health report for a project"""
        if project_id not in self.projects:
            return {'error': 'Project not found'}
        
        project = self.projects[project_id]
        
        return {
            'project_id': project_id,
            'name': project.name,
            'phase': project.phase.value,
            'health': project.get_current_health().value,
            'health_score': project.metrics.calculate_health_score(),
            'health_trend': project.get_health_trend(),
            'sass_level': project.sass_level,
            'metrics': {
                'velocity': {
                    'daily': project.metrics.velocity_daily,
                    'weekly': project.metrics.velocity_weekly,
                    'trend': project.metrics.velocity_trend
                },
                'issues': {
                    'open': project.metrics.open_issues,
                    'closed': project.metrics.closed_issues,
                    'resolution_time': project.metrics.issue_resolution_time,
                    'bug_rate': project.metrics.bug_rate
                },
                'pull_requests': {
                    'open': project.metrics.open_prs,
                    'merged': project.metrics.merged_prs,
                    'review_time': project.metrics.pr_review_time,
                    'rejection_rate': project.metrics.pr_rejection_rate
                },
                'quality': {
                    'coverage': project.metrics.code_coverage,
                    'test_pass_rate': project.metrics.test_pass_rate,
                    'build_success_rate': project.metrics.build_success_rate
                },
                'risks': {
                    'blockers': project.metrics.blocker_count,
                    'technical_debt': project.metrics.technical_debt,
                    'security_issues': project.metrics.security_issues
                }
            },
            'team': {
                'members': project.team_members,
                'active_contributors': project.metrics.active_contributors,
                'collaboration_score': project.metrics.collaboration_score
            },
            'needs_intervention': project.needs_intervention(),
            'recommendation': self._get_recommendation(project)
        }
    
    def _get_recommendation(self, project: Project) -> str:
        """Get recommendation for project"""
        health = project.get_current_health()
        
        recommendations = {
            ProjectHealth.CRITICAL: "IMMEDIATE INTERVENTION REQUIRED. Consider stopping new development.",
            ProjectHealth.UNHEALTHY: "Major issues detected. Schedule emergency team meeting.",
            ProjectHealth.AT_RISK: "Project showing warning signs. Increase monitoring.",
            ProjectHealth.FAIR: "Some concerns present. Review and address bottlenecks.",
            ProjectHealth.HEALTHY: "Project on track. Maintain current practices.",
            ProjectHealth.EXCELLENT: "Exceeding expectations. Consider documenting best practices."
        }
        
        return recommendations.get(health, "Continue monitoring")