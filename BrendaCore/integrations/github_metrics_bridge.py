"""
GitHub Metrics Bridge
Integrates GitHub metrics with BrendaCore's performance tracker
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class GitHubMetricsBridge:
    """
    Bridges GitHub metrics to BrendaCore's performance tracking system
    """
    
    def __init__(
        self,
        github_adapter,
        performance_tracker,
        project_registry
    ):
        self.github = github_adapter
        self.performance_tracker = performance_tracker
        self.project_registry = project_registry
        
        # Metric mappings
        self.contributor_agent_map = {}  # GitHub username -> agent_id
        self.metric_weights = self._init_metric_weights()
        
        logger.info("GitHubMetricsBridge initialized")
    
    def _init_metric_weights(self) -> Dict[str, float]:
        """Initialize metric weights for scoring"""
        return {
            'pr_velocity': 0.2,
            'pr_quality': 0.25,
            'issue_resolution': 0.2,
            'code_quality': 0.15,
            'collaboration': 0.1,
            'reliability': 0.1
        }
    
    def map_contributor_to_agent(self, github_username: str, agent_id: str):
        """Map GitHub contributor to agent ID"""
        self.contributor_agent_map[github_username] = agent_id
        logger.info(f"Mapped {github_username} to agent {agent_id}")
    
    def sync_pr_metrics(self, repo_name: str):
        """Sync PR metrics to performance tracker"""
        prs = self.github.get_pull_requests(repo_name)
        
        for pr in prs:
            agent_id = self.contributor_agent_map.get(pr.author)
            if not agent_id:
                continue
            
            # Update performance metrics
            if pr.status.value == 'merged':
                self.performance_tracker.record_task_completion(
                    agent_id=agent_id,
                    task_id=f"pr_{pr.pr_id}",
                    success=True,
                    duration=pr.get_age_days() * 24 * 3600  # Convert to seconds
                )
                
                # Bonus for clean merges
                if pr.comments < 3:
                    self.performance_tracker.update_innovation_score(agent_id, 0.05)
            
            elif pr.status.value == 'closed':
                self.performance_tracker.record_task_completion(
                    agent_id=agent_id,
                    task_id=f"pr_{pr.pr_id}",
                    success=False,
                    duration=pr.get_age_days() * 24 * 3600
                )
                
                # Record as error if PR was rejected
                self.performance_tracker.record_error(agent_id, "pr_rejected")
            
            # Check for quality issues
            if pr.lines_added > 500:
                self.performance_tracker.record_sass_received(agent_id, 7)
            
            # Update collaboration score based on reviews
            if pr.reviews:
                self.performance_tracker.update_collaboration_score(agent_id, 0.02)
    
    def sync_issue_metrics(self, repo_name: str):
        """Sync issue metrics to performance tracker"""
        issues = self.github.get_issues(repo_name)
        
        for issue in issues:
            # Track issue assignment
            for assignee in issue.assignees:
                agent_id = self.contributor_agent_map.get(assignee)
                if not agent_id:
                    continue
                
                self.performance_tracker.record_task_assignment(
                    agent_id=agent_id,
                    task_id=f"issue_{issue.issue_id}"
                )
                
                # Check if issue is stale
                if issue.is_stale():
                    self.performance_tracker.record_blocker(agent_id)
                    self.performance_tracker.record_sass_received(agent_id, 6)
    
    def sync_commit_metrics(self, repo_name: str):
        """Sync commit metrics to performance tracker"""
        analysis = self.github.commit_analyzer.analyze_commits(repo_name)
        
        for contributor, stats in analysis['contributors'].items():
            agent_id = self.contributor_agent_map.get(contributor)
            if not agent_id:
                continue
            
            # Update based on commit quality
            commits = stats['commits']
            quality_score = analysis['quality_score'] / max(1, analysis['total_commits'])
            
            if quality_score < 0:
                self.performance_tracker.record_sass_received(agent_id, 8)
                self.performance_tracker.record_error(agent_id, "poor_commit_quality")
            elif quality_score > 5:
                self.performance_tracker.issue_commendation(
                    agent_id,
                    "Excellent commit messages"
                )
    
    def sync_workflow_metrics(self, repo_name: str):
        """Sync GitHub Actions metrics to performance tracker"""
        actions = self.github.get_actions_status(repo_name)
        
        # Track build failures
        for failure in actions.get('recent_failures', []):
            # Find who broke the build
            # In production, would analyze commit that triggered the failure
            culprit = 'last_committer'  # Mock
            agent_id = self.contributor_agent_map.get(culprit)
            
            if agent_id:
                self.performance_tracker.record_error(agent_id, "build_failure")
                self.performance_tracker.record_blocker(agent_id)
                self.performance_tracker.record_sass_received(agent_id, 9)
    
    def update_project_health(self, repo_name: str, project_id: str):
        """Update project health metrics from GitHub"""
        # Get repository data
        repo_data = self.github.sync_repository(repo_name)
        
        # Get PR metrics
        prs = self.github.get_pull_requests(repo_name)
        open_prs = len([pr for pr in prs if pr.status.value == 'open'])
        
        # Get issue metrics
        issues = self.github.get_issues(repo_name)
        open_issues = len([issue for issue in issues if issue.status.value == 'open'])
        
        # Get commit analysis
        commit_analysis = self.github.commit_analyzer.analyze_commits(repo_name)
        
        # Calculate metrics
        metrics_update = {
            'open_issues': open_issues,
            'open_prs': open_prs,
            'velocity_daily': commit_analysis['velocity'],
            'active_contributors': len(commit_analysis['contributors']),
            'commit_frequency': commit_analysis['velocity']
        }
        
        # Calculate PR review time
        if prs:
            review_times = []
            for pr in prs:
                if pr.status.value == 'merged':
                    review_times.append(pr.get_age_days() * 24)  # Convert to hours
            
            if review_times:
                metrics_update['pr_review_time'] = sum(review_times) / len(review_times)
        
        # Update project registry
        self.project_registry.update_project_metrics(project_id, metrics_update)
    
    def generate_developer_report(self, github_username: str) -> Dict[str, Any]:
        """Generate developer report combining GitHub and performance metrics"""
        agent_id = self.contributor_agent_map.get(github_username)
        
        if not agent_id:
            return {'error': 'Developer not mapped to agent'}
        
        # Get performance metrics
        perf_report = self.performance_tracker.generate_performance_report(agent_id)
        
        # Add GitHub-specific metrics
        github_metrics = {
            'github_username': github_username,
            'recent_prs': [],
            'recent_issues': [],
            'commit_quality': 0,
            'review_participation': 0
        }
        
        # In production, would fetch actual GitHub data for this user
        
        return {
            'developer': github_username,
            'agent_id': agent_id,
            'performance': perf_report,
            'github': github_metrics,
            'combined_score': self._calculate_combined_score(perf_report, github_metrics)
        }
    
    def _calculate_combined_score(
        self,
        perf_report: Dict[str, Any],
        github_metrics: Dict[str, Any]
    ) -> float:
        """Calculate combined score from performance and GitHub metrics"""
        base_score = perf_report.get('overall_score', 50)
        
        # Adjust based on GitHub activity
        # In production, would use actual GitHub metrics
        github_adjustment = 0
        
        return min(100, max(0, base_score + github_adjustment))
    
    def identify_github_mvp(self, repo_name: str, timeframe_days: int = 7) -> Optional[str]:
        """Identify MVP based on GitHub activity"""
        # Get recent activity
        prs = self.github.get_pull_requests(repo_name)
        commit_analysis = self.github.commit_analyzer.analyze_commits(repo_name)
        
        # Score each contributor
        scores = {}
        
        for contributor, stats in commit_analysis['contributors'].items():
            score = 0
            
            # Score based on commits
            score += stats['commits'] * 10
            
            # Score based on code changes
            score += (stats['additions'] - stats['deletions']) * 0.01
            
            # Score based on PR merges
            merged_prs = [
                pr for pr in prs
                if pr.author == contributor and pr.status.value == 'merged'
            ]
            score += len(merged_prs) * 20
            
            scores[contributor] = score
        
        # Find highest scorer
        if scores:
            mvp = max(scores, key=scores.get)
            agent_id = self.contributor_agent_map.get(mvp)
            
            if agent_id:
                # Issue commendation
                self.performance_tracker.issue_commendation(
                    agent_id,
                    f"GitHub MVP for {repo_name}"
                )
            
            return mvp
        
        return None
    
    def detect_collaboration_patterns(self, repo_name: str) -> Dict[str, Any]:
        """Detect collaboration patterns from GitHub activity"""
        prs = self.github.get_pull_requests(repo_name)
        
        patterns = {
            'review_pairs': {},  # Who reviews whose code
            'collaboration_graph': {},
            'lone_wolves': [],  # Contributors who don't collaborate
            'team_players': []  # Contributors who collaborate well
        }
        
        # Analyze PR reviews
        for pr in prs:
            author = pr.author
            
            if author not in patterns['collaboration_graph']:
                patterns['collaboration_graph'][author] = {
                    'reviews_given': 0,
                    'reviews_received': 0,
                    'collaborators': set()
                }
            
            # Track reviews
            for review in pr.reviews:
                reviewer = review.get('user', 'unknown')
                
                if reviewer not in patterns['collaboration_graph']:
                    patterns['collaboration_graph'][reviewer] = {
                        'reviews_given': 0,
                        'reviews_received': 0,
                        'collaborators': set()
                    }
                
                patterns['collaboration_graph'][author]['reviews_received'] += 1
                patterns['collaboration_graph'][reviewer]['reviews_given'] += 1
                
                patterns['collaboration_graph'][author]['collaborators'].add(reviewer)
                patterns['collaboration_graph'][reviewer]['collaborators'].add(author)
                
                # Track review pairs
                pair_key = f"{reviewer}->{author}"
                patterns['review_pairs'][pair_key] = \
                    patterns['review_pairs'].get(pair_key, 0) + 1
        
        # Identify lone wolves and team players
        for contributor, data in patterns['collaboration_graph'].items():
            if len(data['collaborators']) == 0:
                patterns['lone_wolves'].append(contributor)
            elif len(data['collaborators']) > 3:
                patterns['team_players'].append(contributor)
                
                # Update collaboration score
                agent_id = self.contributor_agent_map.get(contributor)
                if agent_id:
                    self.performance_tracker.update_collaboration_score(agent_id, 0.1)
        
        return patterns
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get statistics about the integration"""
        return {
            'mapped_contributors': len(self.contributor_agent_map),
            'contributors': list(self.contributor_agent_map.keys()),
            'agents': list(self.contributor_agent_map.values()),
            'metric_weights': self.metric_weights
        }