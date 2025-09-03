"""
BrendaCore Integrations Module - Phase 4
External service integrations (GitHub, Jira, Azure DevOps)
"""

from .github_adapter import GitHubAdapter, PRReviewer, IssueManager
from .sync_manager import SyncManager, ConflictResolver
from .project_registry import ProjectRegistry, ProjectHealth

__all__ = [
    'GitHubAdapter',
    'PRReviewer',
    'IssueManager',
    'SyncManager',
    'ConflictResolver',
    'ProjectRegistry',
    'ProjectHealth'
]