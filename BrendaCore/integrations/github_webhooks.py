"""
GitHub Webhook Handler
Processes GitHub events in real-time with appropriate sass
"""

import hmac
import hashlib
import json
import logging
from enum import Enum
from typing import Dict, Any, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class GitHubEvent(Enum):
    """GitHub webhook event types"""
    PUSH = "push"
    PULL_REQUEST = "pull_request"
    PULL_REQUEST_REVIEW = "pull_request_review"
    PULL_REQUEST_REVIEW_COMMENT = "pull_request_review_comment"
    ISSUES = "issues"
    ISSUE_COMMENT = "issue_comment"
    CREATE = "create"
    DELETE = "delete"
    FORK = "fork"
    STAR = "star"
    WATCH = "watch"
    RELEASE = "release"
    DEPLOYMENT = "deployment"
    DEPLOYMENT_STATUS = "deployment_status"
    WORKFLOW_RUN = "workflow_run"
    CHECK_RUN = "check_run"
    CHECK_SUITE = "check_suite"


class WebhookHandler:
    """
    Handles GitHub webhook events with Brenda's personality
    """
    
    def __init__(self, secret: str = None, sass_engine=None):
        self.secret = secret
        self.sass_engine = sass_engine
        self.event_handlers = self._init_handlers()
        self.event_log = []
        self.stats = {
            'total_events': 0,
            'events_by_type': {},
            'sass_delivered': 0
        }
        
        logger.info("GitHub WebhookHandler initialized")
    
    def _init_handlers(self) -> Dict[GitHubEvent, Callable]:
        """Initialize event handlers"""
        return {
            GitHubEvent.PUSH: self._handle_push,
            GitHubEvent.PULL_REQUEST: self._handle_pull_request,
            GitHubEvent.PULL_REQUEST_REVIEW: self._handle_pr_review,
            GitHubEvent.ISSUES: self._handle_issue,
            GitHubEvent.ISSUE_COMMENT: self._handle_issue_comment,
            GitHubEvent.WORKFLOW_RUN: self._handle_workflow_run,
            GitHubEvent.DEPLOYMENT: self._handle_deployment,
            GitHubEvent.RELEASE: self._handle_release
        }
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature"""
        if not self.secret:
            return True  # No secret configured, skip verification
        
        expected_sig = 'sha256=' + hmac.new(
            self.secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_sig, signature)
    
    def process_webhook(
        self,
        event_type: str,
        payload: Dict[str, Any],
        signature: str = None
    ) -> Dict[str, Any]:
        """Process incoming webhook"""
        # Update stats
        self.stats['total_events'] += 1
        self.stats['events_by_type'][event_type] = \
            self.stats['events_by_type'].get(event_type, 0) + 1
        
        # Log event
        self.event_log.append({
            'timestamp': datetime.now().isoformat(),
            'event': event_type,
            'repository': payload.get('repository', {}).get('name', 'unknown')
        })
        
        # Get appropriate handler
        try:
            event_enum = GitHubEvent(event_type)
        except ValueError:
            logger.warning(f"Unknown event type: {event_type}")
            return {
                'status': 'unknown_event',
                'sass': "I don't know what this is, but I'm sure it's disappointing"
            }
        
        if event_enum in self.event_handlers:
            return self.event_handlers[event_enum](payload)
        else:
            return {
                'status': 'unhandled',
                'sass': f"Event {event_type} noted. I'm thrilled. Really."
            }
    
    def _handle_push(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle push event"""
        commits = payload.get('commits', [])
        pusher = payload.get('pusher', {}).get('name', 'someone')
        branch = payload.get('ref', '').split('/')[-1]
        
        response = {
            'event': 'push',
            'branch': branch,
            'commits': len(commits),
            'pusher': pusher
        }
        
        # Generate sass based on push
        if len(commits) == 0:
            response['sass'] = "An empty push? How productive."
            response['sass_level'] = 7
        elif len(commits) == 1:
            commit_msg = commits[0].get('message', '')
            if 'fix' in commit_msg.lower():
                response['sass'] = "Another fix? Maybe try not breaking it first time."
                response['sass_level'] = 6
            elif 'wip' in commit_msg.lower():
                response['sass'] = "WIP in main? Living dangerously, I see."
                response['sass_level'] = 8
            else:
                response['sass'] = "One commit. Such restraint."
                response['sass_level'] = 4
        elif len(commits) > 10:
            response['sass'] = f"{len(commits)} commits? Did you discover version control yesterday?"
            response['sass_level'] = 9
        else:
            response['sass'] = f"{pusher} pushed {len(commits)} commits. I'll add it to the pile."
            response['sass_level'] = 5
        
        self.stats['sass_delivered'] += 1
        return response
    
    def _handle_pull_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pull request event"""
        action = payload.get('action', '')
        pr = payload.get('pull_request', {})
        pr_number = pr.get('number', 0)
        pr_title = pr.get('title', '')
        author = pr.get('user', {}).get('login', 'someone')
        
        response = {
            'event': 'pull_request',
            'action': action,
            'pr_number': pr_number,
            'author': author
        }
        
        # Generate sass based on PR action
        if action == 'opened':
            additions = pr.get('additions', 0)
            deletions = pr.get('deletions', 0)
            
            if additions > 1000:
                response['sass'] = f"PR #{pr_number}: {additions} additions? This isn't a PR, it's a novel."
                response['sass_level'] = 9
            elif 'WIP' in pr_title:
                response['sass'] = "Another WIP PR. At least you're consistent in your incompleteness."
                response['sass_level'] = 7
            else:
                response['sass'] = f"PR #{pr_number} opened. Let's see how this goes wrong."
                response['sass_level'] = 5
                
        elif action == 'closed':
            merged = pr.get('merged', False)
            if merged:
                response['sass'] = f"PR #{pr_number} merged. Miracles do happen."
                response['sass_level'] = 4
            else:
                response['sass'] = f"PR #{pr_number} closed without merging. Another dream dies."
                response['sass_level'] = 6
                
        elif action == 'review_requested':
            response['sass'] = "Review requested. Time to crush someone's hopes."
            response['sass_level'] = 6
        
        self.stats['sass_delivered'] += 1
        return response
    
    def _handle_pr_review(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle PR review event"""
        review = payload.get('review', {})
        state = review.get('state', '')
        reviewer = review.get('user', {}).get('login', 'someone')
        pr_number = payload.get('pull_request', {}).get('number', 0)
        
        response = {
            'event': 'pull_request_review',
            'pr_number': pr_number,
            'reviewer': reviewer,
            'state': state
        }
        
        # Generate sass based on review state
        if state == 'approved':
            response['sass'] = f"{reviewer} approved PR #{pr_number}. Low standards, I see."
            response['sass_level'] = 5
        elif state == 'changes_requested':
            response['sass'] = f"{reviewer} requested changes. Someone has standards!"
            response['sass_level'] = 4
        elif state == 'commented':
            response['sass'] = "More comments. Because that's what this PR needed."
            response['sass_level'] = 6
        
        self.stats['sass_delivered'] += 1
        return response
    
    def _handle_issue(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle issue event"""
        action = payload.get('action', '')
        issue = payload.get('issue', {})
        issue_number = issue.get('number', 0)
        issue_title = issue.get('title', '')
        author = issue.get('user', {}).get('login', 'someone')
        
        response = {
            'event': 'issues',
            'action': action,
            'issue_number': issue_number,
            'author': author
        }
        
        # Generate sass based on issue action
        if action == 'opened':
            if 'urgent' in issue_title.lower():
                response['sass'] = "Another 'urgent' issue. Everything is urgent when you can't plan."
                response['sass_level'] = 8
            elif 'bug' in issue_title.lower():
                response['sass'] = f"Issue #{issue_number}: Another bug. Shocking."
                response['sass_level'] = 6
            else:
                response['sass'] = f"Issue #{issue_number} opened. Add it to the backlog graveyard."
                response['sass_level'] = 5
                
        elif action == 'closed':
            response['sass'] = f"Issue #{issue_number} closed. Only {self._count_open_issues()} more to go."
            response['sass_level'] = 5
            
        elif action == 'reopened':
            response['sass'] = f"Issue #{issue_number} reopened. Did you miss it?"
            response['sass_level'] = 7
        
        self.stats['sass_delivered'] += 1
        return response
    
    def _handle_issue_comment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle issue comment event"""
        comment = payload.get('comment', {})
        commenter = comment.get('user', {}).get('login', 'someone')
        issue_number = payload.get('issue', {}).get('number', 0)
        
        response = {
            'event': 'issue_comment',
            'issue_number': issue_number,
            'commenter': commenter
        }
        
        # Check for common patterns
        comment_body = comment.get('body', '').lower()
        if '+1' in comment_body or '👍' in comment_body:
            response['sass'] = "Another +1. How constructive."
            response['sass_level'] = 7
        elif 'any update' in comment_body:
            response['sass'] = "Asking for updates won't make it happen faster."
            response['sass_level'] = 6
        else:
            response['sass'] = f"{commenter} commented on #{issue_number}. The discussion continues."
            response['sass_level'] = 4
        
        self.stats['sass_delivered'] += 1
        return response
    
    def _handle_workflow_run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle workflow run event"""
        workflow = payload.get('workflow_run', {})
        status = workflow.get('status', '')
        conclusion = workflow.get('conclusion', '')
        name = workflow.get('name', 'workflow')
        
        response = {
            'event': 'workflow_run',
            'workflow': name,
            'status': status,
            'conclusion': conclusion
        }
        
        # Generate sass based on workflow result
        if conclusion == 'failure':
            response['sass'] = f"{name} failed. What a surprise. Did you test locally?"
            response['sass_level'] = 8
            response['action'] = 'escalate'
        elif conclusion == 'success':
            response['sass'] = f"{name} passed. Even a broken clock is right twice a day."
            response['sass_level'] = 4
        elif status == 'in_progress':
            response['sass'] = f"{name} running. Time to see what breaks."
            response['sass_level'] = 5
        
        self.stats['sass_delivered'] += 1
        return response
    
    def _handle_deployment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle deployment event"""
        deployment = payload.get('deployment', {})
        environment = deployment.get('environment', 'unknown')
        creator = deployment.get('creator', {}).get('login', 'someone')
        
        response = {
            'event': 'deployment',
            'environment': environment,
            'creator': creator
        }
        
        # Generate sass based on deployment
        if environment == 'production':
            response['sass'] = f"{creator} deploying to production. Brave or foolish?"
            response['sass_level'] = 7
            response['action'] = 'monitor_closely'
        elif environment == 'staging':
            response['sass'] = "Deploying to staging. At least you're testing first."
            response['sass_level'] = 4
        else:
            response['sass'] = f"Deployment to {environment}. Another day, another deploy."
            response['sass_level'] = 5
        
        self.stats['sass_delivered'] += 1
        return response
    
    def _handle_release(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle release event"""
        release = payload.get('release', {})
        tag = release.get('tag_name', 'unknown')
        author = release.get('author', {}).get('login', 'someone')
        prerelease = release.get('prerelease', False)
        
        response = {
            'event': 'release',
            'tag': tag,
            'author': author,
            'prerelease': prerelease
        }
        
        # Generate sass based on release
        if prerelease:
            response['sass'] = "A pre-release. Because committing to a real release is hard."
            response['sass_level'] = 6
        else:
            response['sass'] = f"Release {tag} by {author}. Let's see what breaks in production."
            response['sass_level'] = 7
            response['action'] = 'prepare_rollback'
        
        self.stats['sass_delivered'] += 1
        return response
    
    def _count_open_issues(self) -> int:
        """Mock count of open issues"""
        return 42  # The answer to everything
    
    def get_event_stats(self) -> Dict[str, Any]:
        """Get webhook event statistics"""
        return {
            'total_events': self.stats['total_events'],
            'events_by_type': self.stats['events_by_type'],
            'sass_delivered': self.stats['sass_delivered'],
            'recent_events': self.event_log[-10:],
            'sass_per_event': self.stats['sass_delivered'] / max(1, self.stats['total_events'])
        }
    
    def get_sass_summary(self) -> str:
        """Get a sassy summary of recent events"""
        if not self.event_log:
            return "No events yet. How peaceful. How boring."
        
        recent = self.event_log[-5:]
        event_types = [e['event'] for e in recent]
        
        if 'workflow_run' in event_types:
            return "Recent builds failing? I'm shocked. Truly."
        elif 'pull_request' in event_types:
            return "More PRs to review. My favorite waste of time."
        elif 'issues' in event_types:
            return "Issues piling up. Business as usual."
        else:
            return "GitHub is happening. Try to contain your excitement."