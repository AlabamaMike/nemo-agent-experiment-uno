"""
GitHub Adapter for BrendaCore
Integrates with GitHub for project management, PR reviews, and issue tracking
"""

import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

# Note: In production, would use PyGithub
# from github import Github
# For now, we'll create a mock interface

logger = logging.getLogger(__name__)


class PRStatus(Enum):
    """Pull Request status"""
    DRAFT = "draft"
    OPEN = "open"
    REVIEW_REQUIRED = "review_required"
    CHANGES_REQUESTED = "changes_requested"
    APPROVED = "approved"
    MERGED = "merged"
    CLOSED = "closed"


class IssueStatus(Enum):
    """Issue status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    CLOSED = "closed"


class CodeQuality(Enum):
    """Code quality assessment"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    NEEDS_WORK = "needs_work"
    DISASTER = "disaster"


@dataclass
class PullRequest:
    """Pull Request representation"""
    pr_id: int
    title: str
    author: str
    created_at: datetime
    updated_at: datetime
    status: PRStatus
    lines_added: int
    lines_removed: int
    files_changed: int
    comments: int
    reviews: List[Dict[str, Any]]
    labels: List[str]
    assignees: List[str]
    
    def get_age_days(self) -> int:
        """Get PR age in days"""
        return (datetime.now() - self.created_at).days
    
    def needs_attention(self) -> bool:
        """Check if PR needs attention"""
        age = self.get_age_days()
        return (age > 3 and self.status == PRStatus.OPEN) or \
               (age > 1 and self.status == PRStatus.REVIEW_REQUIRED)


@dataclass
class Issue:
    """Issue representation"""
    issue_id: int
    title: str
    author: str
    created_at: datetime
    updated_at: datetime
    status: IssueStatus
    priority: str
    labels: List[str]
    assignees: List[str]
    comments: int
    
    def is_stale(self) -> bool:
        """Check if issue is stale"""
        days_old = (datetime.now() - self.updated_at).days
        return days_old > 7 and self.status != IssueStatus.CLOSED


class RateLimiter:
    """Rate limiter for API calls"""
    
    def __init__(self, max_calls: int = 5000, window: int = 3600):
        self.max_calls = max_calls
        self.window = window
        self.calls = []
    
    def can_call(self) -> bool:
        """Check if we can make an API call"""
        now = time.time()
        # Remove old calls outside window
        self.calls = [t for t in self.calls if now - t < self.window]
        return len(self.calls) < self.max_calls
    
    def record_call(self):
        """Record an API call"""
        self.calls.append(time.time())


class GitHubAdapter:
    """
    GitHub integration adapter
    Manages repositories, PRs, issues, and actions
    """
    
    def __init__(self, token: str = None, organization: str = None):
        self.token = token or "mock_token"
        self.organization = organization
        self.rate_limiter = RateLimiter(5000, 3600)
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # In production: self.github = Github(token)
        self.github = None  # Mock for now
        
        # Initialize sub-components
        self.pr_reviewer = PRReviewer(self)
        self.issue_manager = IssueManager(self)
        self.commit_analyzer = CommitAnalyzer(self)
        
        logger.info(f"GitHubAdapter initialized for org: {organization}")
    
    def sync_repository(self, repo_name: str) -> Dict[str, Any]:
        """Sync repository data"""
        if not self.rate_limiter.can_call():
            logger.warning("Rate limit reached")
            return {'error': 'rate_limit'}
        
        self.rate_limiter.record_call()
        
        # Check cache
        cache_key = f"repo:{repo_name}"
        if cache_key in self.cache:
            if time.time() - self.cache[cache_key]['timestamp'] < self.cache_ttl:
                return self.cache[cache_key]['data']
        
        # In production, would fetch from GitHub API
        repo_data = self._mock_fetch_repo(repo_name)
        
        # Cache the result
        self.cache[cache_key] = {
            'timestamp': time.time(),
            'data': repo_data
        }
        
        logger.info(f"Synced repository: {repo_name}")
        return repo_data
    
    def get_pull_requests(
        self,
        repo_name: str,
        state: str = "open"
    ) -> List[PullRequest]:
        """Get pull requests for a repository"""
        # In production, would use GitHub API
        prs = self._mock_fetch_prs(repo_name, state)
        
        # Convert to PullRequest objects
        pull_requests = []
        for pr_data in prs:
            pr = PullRequest(
                pr_id=pr_data['number'],
                title=pr_data['title'],
                author=pr_data['user'],
                created_at=datetime.fromisoformat(pr_data['created_at']),
                updated_at=datetime.fromisoformat(pr_data['updated_at']),
                status=PRStatus(pr_data['state']),
                lines_added=pr_data.get('additions', 0),
                lines_removed=pr_data.get('deletions', 0),
                files_changed=pr_data.get('changed_files', 0),
                comments=pr_data.get('comments', 0),
                reviews=pr_data.get('reviews', []),
                labels=pr_data.get('labels', []),
                assignees=pr_data.get('assignees', [])
            )
            pull_requests.append(pr)
        
        return pull_requests
    
    def get_issues(
        self,
        repo_name: str,
        state: str = "open"
    ) -> List[Issue]:
        """Get issues for a repository"""
        # In production, would use GitHub API
        issues = self._mock_fetch_issues(repo_name, state)
        
        # Convert to Issue objects
        issue_objects = []
        for issue_data in issues:
            issue = Issue(
                issue_id=issue_data['number'],
                title=issue_data['title'],
                author=issue_data['user'],
                created_at=datetime.fromisoformat(issue_data['created_at']),
                updated_at=datetime.fromisoformat(issue_data['updated_at']),
                status=IssueStatus(issue_data['state']),
                priority=issue_data.get('priority', 'medium'),
                labels=issue_data.get('labels', []),
                assignees=issue_data.get('assignees', []),
                comments=issue_data.get('comments', 0)
            )
            issue_objects.append(issue)
        
        return issue_objects
    
    def get_actions_status(self, repo_name: str) -> Dict[str, Any]:
        """Get GitHub Actions status"""
        # In production, would fetch from GitHub API
        return {
            'workflow_runs': [
                {
                    'id': 1,
                    'name': 'CI/CD Pipeline',
                    'status': 'success',
                    'conclusion': 'success',
                    'created_at': datetime.now().isoformat()
                }
            ],
            'recent_failures': [],
            'success_rate': 0.95
        }
    
    def _mock_fetch_repo(self, repo_name: str) -> Dict[str, Any]:
        """Mock repository fetch"""
        return {
            'name': repo_name,
            'full_name': f"{self.organization}/{repo_name}",
            'description': 'Mock repository',
            'stars': 42,
            'forks': 7,
            'open_issues': 15,
            'open_prs': 5,
            'language': 'Python',
            'default_branch': 'main'
        }
    
    def _mock_fetch_prs(self, repo_name: str, state: str) -> List[Dict[str, Any]]:
        """Mock PR fetch"""
        return [
            {
                'number': 101,
                'title': 'Add new feature',
                'user': 'developer1',
                'created_at': (datetime.now() - timedelta(days=2)).isoformat(),
                'updated_at': datetime.now().isoformat(),
                'state': 'open',
                'additions': 150,
                'deletions': 30,
                'changed_files': 5,
                'comments': 3,
                'reviews': [],
                'labels': ['enhancement'],
                'assignees': ['reviewer1']
            }
        ]
    
    def _mock_fetch_issues(self, repo_name: str, state: str) -> List[Dict[str, Any]]:
        """Mock issue fetch"""
        return [
            {
                'number': 42,
                'title': 'Bug in production',
                'user': 'user1',
                'created_at': (datetime.now() - timedelta(days=5)).isoformat(),
                'updated_at': (datetime.now() - timedelta(days=1)).isoformat(),
                'state': 'open',
                'priority': 'high',
                'labels': ['bug', 'priority-high'],
                'assignees': ['developer1'],
                'comments': 5
            }
        ]


class PRReviewer:
    """
    Automated PR review with sass
    """
    
    def __init__(self, github_adapter: GitHubAdapter):
        self.github = github_adapter
        self.review_patterns = self._init_review_patterns()
        
    def _init_review_patterns(self) -> List[Dict[str, Any]]:
        """Initialize code review patterns"""
        return [
            {
                'pattern': 'no tests',
                'severity': 'high',
                'sass_level': 8,
                'comment': "No tests? How brave of you. I'm sure nothing will break. *eye roll*"
            },
            {
                'pattern': 'console.log',
                'severity': 'medium',
                'sass_level': 6,
                'comment': "Console.log in production code? That's... a choice."
            },
            {
                'pattern': 'TODO',
                'severity': 'low',
                'sass_level': 4,
                'comment': "Another TODO for the collection. I'm starting a museum."
            },
            {
                'pattern': 'large PR',
                'severity': 'high',
                'sass_level': 9,
                'comment': "This PR is larger than my patience. Split it up."
            }
        ]
    
    def review_pr(self, pr: PullRequest) -> Dict[str, Any]:
        """Review a pull request"""
        review = {
            'pr_id': pr.pr_id,
            'quality': self._assess_quality(pr),
            'issues': [],
            'sass_comments': [],
            'approval_status': 'pending',
            'sass_level': 5
        }
        
        # Check for issues
        if pr.lines_added > 500:
            review['issues'].append('PR too large')
            review['sass_comments'].append("This PR could be its own repository")
            review['sass_level'] = 8
        
        if pr.get_age_days() > 7:
            review['issues'].append('Stale PR')
            review['sass_comments'].append("This PR is older than some of my grievances")
            review['sass_level'] = 7
        
        if not pr.reviews:
            review['issues'].append('No reviews')
            review['sass_comments'].append("Zero reviews? Even I'm not that antisocial")
            review['sass_level'] = 6
        
        # Determine approval
        if review['quality'] in [CodeQuality.EXCELLENT, CodeQuality.GOOD]:
            review['approval_status'] = 'approved'
        elif review['quality'] == CodeQuality.DISASTER:
            review['approval_status'] = 'rejected'
            review['sass_level'] = 10
        
        return review
    
    def _assess_quality(self, pr: PullRequest) -> CodeQuality:
        """Assess PR code quality"""
        score = 100
        
        # Deduct points for issues
        if pr.lines_added > 500:
            score -= 20
        if pr.files_changed > 20:
            score -= 15
        if pr.get_age_days() > 7:
            score -= 10
        if not pr.reviews:
            score -= 15
        if 'WIP' in pr.title:
            score -= 25
        
        # Map score to quality
        if score >= 90:
            return CodeQuality.EXCELLENT
        elif score >= 75:
            return CodeQuality.GOOD
        elif score >= 60:
            return CodeQuality.ACCEPTABLE
        elif score >= 40:
            return CodeQuality.NEEDS_WORK
        else:
            return CodeQuality.DISASTER
    
    def suggest_reviewers(self, pr: PullRequest) -> List[str]:
        """Suggest reviewers for a PR"""
        # In production, would analyze code ownership and expertise
        suggestions = ['senior_dev', 'code_expert']
        
        if 'security' in pr.labels:
            suggestions.append('security_expert')
        if 'database' in pr.labels:
            suggestions.append('db_expert')
        
        return suggestions
    
    def auto_approve_safe_prs(self, prs: List[PullRequest]) -> List[int]:
        """Auto-approve safe PRs (documentation, dependencies)"""
        auto_approved = []
        
        for pr in prs:
            if self._is_safe_pr(pr):
                auto_approved.append(pr.pr_id)
                logger.info(f"Auto-approved PR #{pr.pr_id}: {pr.title}")
        
        return auto_approved
    
    def _is_safe_pr(self, pr: PullRequest) -> bool:
        """Check if PR is safe to auto-approve"""
        safe_labels = ['documentation', 'dependencies', 'chore']
        return any(label in pr.labels for label in safe_labels) and \
               pr.lines_added < 50 and \
               pr.files_changed < 5


class IssueManager:
    """
    Issue tracking and management
    """
    
    def __init__(self, github_adapter: GitHubAdapter):
        self.github = github_adapter
        self.issue_patterns = self._init_issue_patterns()
    
    def _init_issue_patterns(self) -> Dict[str, Any]:
        """Initialize issue patterns"""
        return {
            'bug': {
                'keywords': ['bug', 'error', 'broken', 'crash'],
                'priority': 'high',
                'sass_level': 6
            },
            'feature': {
                'keywords': ['feature', 'enhancement', 'add', 'implement'],
                'priority': 'medium',
                'sass_level': 4
            },
            'duplicate': {
                'keywords': ['duplicate', 'same as', 'already reported'],
                'priority': 'low',
                'sass_level': 8
            }
        }
    
    def triage_issue(self, issue: Issue) -> Dict[str, Any]:
        """Triage an issue"""
        triage = {
            'issue_id': issue.issue_id,
            'priority': self._determine_priority(issue),
            'category': self._categorize_issue(issue),
            'suggested_assignee': self._suggest_assignee(issue),
            'estimated_effort': self._estimate_effort(issue),
            'sass_comment': None
        }
        
        # Add sass for certain conditions
        if issue.is_stale():
            triage['sass_comment'] = "This issue is so old it's growing moss"
        
        if 'urgent' in issue.title.lower() and triage['priority'] == 'low':
            triage['sass_comment'] = "Everything is urgent when you don't plan properly"
        
        return triage
    
    def _determine_priority(self, issue: Issue) -> str:
        """Determine issue priority"""
        if 'critical' in issue.labels or 'blocker' in issue.labels:
            return 'critical'
        elif 'high-priority' in issue.labels or 'bug' in issue.labels:
            return 'high'
        elif 'low-priority' in issue.labels:
            return 'low'
        else:
            return 'medium'
    
    def _categorize_issue(self, issue: Issue) -> str:
        """Categorize issue type"""
        title_lower = issue.title.lower()
        
        for category, pattern in self.issue_patterns.items():
            if any(keyword in title_lower for keyword in pattern['keywords']):
                return category
        
        return 'general'
    
    def _suggest_assignee(self, issue: Issue) -> str:
        """Suggest assignee for issue"""
        # In production, would analyze code ownership and expertise
        if 'bug' in issue.labels:
            return 'bug_fixer'
        elif 'feature' in issue.labels:
            return 'feature_developer'
        else:
            return 'general_developer'
    
    def _estimate_effort(self, issue: Issue) -> str:
        """Estimate effort required"""
        if 'epic' in issue.labels:
            return 'xl'
        elif 'large' in issue.labels:
            return 'l'
        elif 'small' in issue.labels:
            return 's'
        else:
            return 'm'
    
    def find_duplicate_issues(self, issues: List[Issue]) -> List[Tuple[int, int]]:
        """Find potential duplicate issues"""
        duplicates = []
        
        for i, issue1 in enumerate(issues):
            for issue2 in issues[i+1:]:
                if self._are_similar(issue1, issue2):
                    duplicates.append((issue1.issue_id, issue2.issue_id))
        
        return duplicates
    
    def _are_similar(self, issue1: Issue, issue2: Issue) -> bool:
        """Check if two issues are similar"""
        # Simple similarity check - in production would use NLP
        title_words1 = set(issue1.title.lower().split())
        title_words2 = set(issue2.title.lower().split())
        
        common_words = title_words1.intersection(title_words2)
        similarity = len(common_words) / max(len(title_words1), len(title_words2))
        
        return similarity > 0.7


class CommitAnalyzer:
    """
    Analyze commit patterns and quality
    """
    
    def __init__(self, github_adapter: GitHubAdapter):
        self.github = github_adapter
        self.commit_patterns = self._init_patterns()
    
    def _init_patterns(self) -> Dict[str, Any]:
        """Initialize commit patterns"""
        return {
            'good': {
                'patterns': [r'^(feat|fix|docs|style|refactor|test|chore):', r'^[A-Z]'],
                'score': 10
            },
            'bad': {
                'patterns': [r'^wip', r'^tmp', r'^test', r'^\s*$'],
                'score': -5
            },
            'terrible': {
                'patterns': [r'^asdf', r'^xxx', r'^\.\.\.'],
                'score': -20
            }
        }
    
    def analyze_commits(self, repo_name: str, branch: str = "main") -> Dict[str, Any]:
        """Analyze recent commits"""
        # In production, would fetch from GitHub API
        commits = self._mock_fetch_commits(repo_name, branch)
        
        analysis = {
            'total_commits': len(commits),
            'quality_score': 0,
            'velocity': self._calculate_velocity(commits),
            'patterns': self._analyze_patterns(commits),
            'contributors': self._analyze_contributors(commits),
            'sass_commentary': []
        }
        
        # Calculate quality score
        for commit in commits:
            analysis['quality_score'] += self._score_commit(commit)
        
        # Add sass commentary
        if analysis['quality_score'] < 0:
            analysis['sass_commentary'].append("Your commit messages are crimes against humanity")
        
        if analysis['velocity'] < 1:
            analysis['sass_commentary'].append("This velocity would make a sloth impatient")
        
        return analysis
    
    def _mock_fetch_commits(self, repo_name: str, branch: str) -> List[Dict[str, Any]]:
        """Mock commit fetch"""
        return [
            {
                'sha': 'abc123',
                'message': 'feat: Add new feature',
                'author': 'developer1',
                'timestamp': datetime.now().isoformat(),
                'additions': 50,
                'deletions': 10
            },
            {
                'sha': 'def456',
                'message': 'fix: Fix critical bug',
                'author': 'developer2',
                'timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),
                'additions': 20,
                'deletions': 5
            }
        ]
    
    def _score_commit(self, commit: Dict[str, Any]) -> int:
        """Score a commit message"""
        message = commit['message']
        score = 0
        
        for category, pattern_data in self.commit_patterns.items():
            for pattern in pattern_data['patterns']:
                if re.match(pattern, message):
                    score += pattern_data['score']
                    break
        
        return score
    
    def _calculate_velocity(self, commits: List[Dict[str, Any]]) -> float:
        """Calculate commit velocity (commits per day)"""
        if not commits:
            return 0.0
        
        # Get time range
        timestamps = [datetime.fromisoformat(c['timestamp']) for c in commits]
        time_range = max(timestamps) - min(timestamps)
        days = max(1, time_range.days)
        
        return len(commits) / days
    
    def _analyze_patterns(self, commits: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze commit patterns"""
        patterns = {
            'features': 0,
            'fixes': 0,
            'docs': 0,
            'refactors': 0,
            'tests': 0,
            'other': 0
        }
        
        for commit in commits:
            message = commit['message'].lower()
            if message.startswith('feat'):
                patterns['features'] += 1
            elif message.startswith('fix'):
                patterns['fixes'] += 1
            elif message.startswith('docs'):
                patterns['docs'] += 1
            elif message.startswith('refactor'):
                patterns['refactors'] += 1
            elif message.startswith('test'):
                patterns['tests'] += 1
            else:
                patterns['other'] += 1
        
        return patterns
    
    def _analyze_contributors(self, commits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze contributor patterns"""
        contributors = {}
        
        for commit in commits:
            author = commit['author']
            if author not in contributors:
                contributors[author] = {
                    'commits': 0,
                    'additions': 0,
                    'deletions': 0
                }
            
            contributors[author]['commits'] += 1
            contributors[author]['additions'] += commit.get('additions', 0)
            contributors[author]['deletions'] += commit.get('deletions', 0)
        
        return contributors