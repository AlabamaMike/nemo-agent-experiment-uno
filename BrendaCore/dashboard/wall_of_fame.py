"""
Wall of Fame/Shame Dashboard
Visual representation of agent performance
"""

import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AwardType(Enum):
    """Types of awards and shame"""
    # Positive
    MVP = "mvp"
    ROCKSTAR = "rockstar"
    RISING_STAR = "rising_star"
    TEAM_PLAYER = "team_player"
    INNOVATOR = "innovator"
    SPEED_DEMON = "speed_demon"
    
    # Negative
    SLOWPOKE = "slowpoke"
    ERROR_MAGNET = "error_magnet"
    BLOCKER_KING = "blocker_king"
    SASS_TARGET = "sass_target"
    THREE_STRIKES = "three_strikes"
    PERMANENT_RESIDENT = "permanent_resident"  # Always on shame list


@dataclass
class Award:
    """Award or shame entry"""
    award_type: AwardType
    agent_id: str
    reason: str
    timestamp: float
    score: Optional[float] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class WallOfFame:
    """
    Manages the Wall of Fame and Wall of Shame
    Tracks achievements and failures with visual flair
    """
    
    def __init__(self, performance_tracker=None):
        self.performance_tracker = performance_tracker
        self.hall_of_fame = []
        self.wall_of_shame = []
        self.current_awards = {}  # agent_id -> current awards
        self.award_history = []
        
        # Special categories
        self.mvp_throne = None  # Current MVP
        self.dunce_corner = []  # Worst performers
        
        logger.info("Wall of Fame/Shame initialized")
    
    def update_awards(self, performance_data: Dict[str, Any]):
        """Update awards based on performance data"""
        if not performance_data.get('agents'):
            return
        
        # Clear current awards
        self.current_awards.clear()
        
        # Process each agent
        for agent_id, metrics in performance_data['agents'].items():
            awards = self._determine_awards(agent_id, metrics)
            for award in awards:
                self._grant_award(award)
        
        # Update MVP
        if performance_data.get('current_mvp'):
            self._crown_mvp(performance_data['current_mvp'])
        
        # Update dunce corner
        if performance_data.get('problem_agents'):
            self._populate_dunce_corner(performance_data['problem_agents'])
    
    def _determine_awards(self, agent_id: str, metrics: Dict[str, Any]) -> List[Award]:
        """Determine which awards an agent should receive"""
        awards = []
        
        # Positive awards
        if metrics.get('overall_score', 0) >= 90:
            awards.append(Award(
                award_type=AwardType.ROCKSTAR,
                agent_id=agent_id,
                reason="Outstanding performance",
                timestamp=time.time(),
                score=metrics['overall_score']
            ))
        
        if metrics.get('response_time', float('inf')) < 1.0:
            awards.append(Award(
                award_type=AwardType.SPEED_DEMON,
                agent_id=agent_id,
                reason="Lightning fast responses",
                timestamp=time.time(),
                metadata={'avg_response_time': metrics['response_time']}
            ))
        
        if metrics.get('collaboration_score', 0) >= 0.8:
            awards.append(Award(
                award_type=AwardType.TEAM_PLAYER,
                agent_id=agent_id,
                reason="Excellent collaboration",
                timestamp=time.time()
            ))
        
        if metrics.get('innovation_score', 0) >= 0.8:
            awards.append(Award(
                award_type=AwardType.INNOVATOR,
                agent_id=agent_id,
                reason="Creative problem solving",
                timestamp=time.time()
            ))
        
        # Negative awards
        if metrics.get('response_time', 0) > 30.0:
            awards.append(Award(
                award_type=AwardType.SLOWPOKE,
                agent_id=agent_id,
                reason="Glacial response times",
                timestamp=time.time(),
                metadata={'avg_response_time': metrics['response_time']}
            ))
        
        if metrics.get('error_rate', 0) > 0.3:
            awards.append(Award(
                award_type=AwardType.ERROR_MAGNET,
                agent_id=agent_id,
                reason="Excessive error rate",
                timestamp=time.time(),
                metadata={'error_rate': metrics['error_rate']}
            ))
        
        if metrics.get('blocker_count', 0) >= 5:
            awards.append(Award(
                award_type=AwardType.BLOCKER_KING,
                agent_id=agent_id,
                reason="Champion of creating blockers",
                timestamp=time.time(),
                metadata={'blocker_count': metrics['blocker_count']}
            ))
        
        if metrics.get('sass_count', 0) >= 10:
            awards.append(Award(
                award_type=AwardType.SASS_TARGET,
                agent_id=agent_id,
                reason="Brenda's favorite punching bag",
                timestamp=time.time(),
                metadata={'sass_received': metrics['sass_count']}
            ))
        
        if metrics.get('strikes', 0) >= 3:
            awards.append(Award(
                award_type=AwardType.THREE_STRIKES,
                agent_id=agent_id,
                reason="Three strikes - you're out!",
                timestamp=time.time(),
                metadata={'strike_count': metrics['strikes']}
            ))
        
        return awards
    
    def _grant_award(self, award: Award):
        """Grant an award to an agent"""
        # Add to current awards
        if award.agent_id not in self.current_awards:
            self.current_awards[award.agent_id] = []
        self.current_awards[award.agent_id].append(award)
        
        # Add to history
        self.award_history.append(award)
        
        # Add to appropriate wall
        if award.award_type in [AwardType.MVP, AwardType.ROCKSTAR, AwardType.RISING_STAR,
                                AwardType.TEAM_PLAYER, AwardType.INNOVATOR, AwardType.SPEED_DEMON]:
            self.hall_of_fame.append(award)
            logger.info(f"Fame: {award.agent_id} awarded {award.award_type.value}")
        else:
            self.wall_of_shame.append(award)
            logger.info(f"Shame: {award.agent_id} awarded {award.award_type.value}")
    
    def _crown_mvp(self, agent_id: str):
        """Crown the current MVP"""
        self.mvp_throne = {
            'agent_id': agent_id,
            'crowned_at': time.time(),
            'award': Award(
                award_type=AwardType.MVP,
                agent_id=agent_id,
                reason="Weekly MVP - Bow before greatness",
                timestamp=time.time()
            )
        }
        
        # Add to hall of fame
        self.hall_of_fame.append(self.mvp_throne['award'])
        logger.info(f"MVP crowned: {agent_id}")
    
    def _populate_dunce_corner(self, problem_agents: List[str]):
        """Populate the dunce corner with problem agents"""
        self.dunce_corner = []
        
        for agent_id in problem_agents[:3]:  # Top 3 worst
            self.dunce_corner.append({
                'agent_id': agent_id,
                'added_at': time.time(),
                'reason': "Persistent underperformance"
            })
        
        logger.info(f"Dunce corner updated: {', '.join(problem_agents[:3])}")
    
    def add_manual_award(
        self,
        agent_id: str,
        award_type: AwardType,
        reason: str,
        metadata: Dict[str, Any] = None
    ):
        """Manually add an award (for special occasions)"""
        award = Award(
            award_type=award_type,
            agent_id=agent_id,
            reason=reason,
            timestamp=time.time(),
            metadata=metadata
        )
        
        self._grant_award(award)
    
    def get_agent_awards(self, agent_id: str) -> List[Award]:
        """Get all current awards for an agent"""
        return self.current_awards.get(agent_id, [])
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the current leaderboard"""
        if not self.performance_tracker:
            return []
        
        rankings = self.performance_tracker.calculate_weekly_rankings()
        
        leaderboard = []
        for i, (agent_id, score) in enumerate(rankings[:limit]):
            entry = {
                'rank': i + 1,
                'agent_id': agent_id,
                'score': score,
                'awards': [a.award_type.value for a in self.get_agent_awards(agent_id)],
                'is_mvp': agent_id == (self.mvp_throne['agent_id'] if self.mvp_throne else None),
                'in_dunce_corner': any(d['agent_id'] == agent_id for d in self.dunce_corner)
            }
            leaderboard.append(entry)
        
        return leaderboard
    
    def get_wall_summary(self) -> Dict[str, Any]:
        """Get summary of both walls"""
        return {
            'hall_of_fame': {
                'total_entries': len(self.hall_of_fame),
                'current_mvp': self.mvp_throne['agent_id'] if self.mvp_throne else None,
                'recent_honors': [
                    {
                        'agent_id': a.agent_id,
                        'award': a.award_type.value,
                        'reason': a.reason
                    }
                    for a in self.hall_of_fame[-5:]
                ]
            },
            'wall_of_shame': {
                'total_entries': len(self.wall_of_shame),
                'dunce_corner': [d['agent_id'] for d in self.dunce_corner],
                'recent_shame': [
                    {
                        'agent_id': a.agent_id,
                        'award': a.award_type.value,
                        'reason': a.reason
                    }
                    for a in self.wall_of_shame[-5:]
                ]
            },
            'statistics': {
                'total_awards_granted': len(self.award_history),
                'agents_with_awards': len(self.current_awards),
                'most_decorated': self._get_most_decorated(),
                'most_shamed': self._get_most_shamed()
            }
        }
    
    def _get_most_decorated(self) -> Optional[str]:
        """Get the agent with the most positive awards"""
        if not self.hall_of_fame:
            return None
        
        counts = {}
        for award in self.hall_of_fame:
            counts[award.agent_id] = counts.get(award.agent_id, 0) + 1
        
        return max(counts, key=counts.get) if counts else None
    
    def _get_most_shamed(self) -> Optional[str]:
        """Get the agent with the most negative awards"""
        if not self.wall_of_shame:
            return None
        
        counts = {}
        for award in self.wall_of_shame:
            counts[award.agent_id] = counts.get(award.agent_id, 0) + 1
        
        return max(counts, key=counts.get) if counts else None


class DashboardRenderer:
    """
    Renders the dashboard in various formats
    """
    
    @staticmethod
    def render_text(wall_of_fame: WallOfFame) -> str:
        """Render dashboard as text"""
        output = []
        output.append("\n" + "="*60)
        output.append("         🏆 WALL OF FAME & SHAME 💀")
        output.append("="*60)
        
        # MVP Section
        if wall_of_fame.mvp_throne:
            output.append("\n👑 CURRENT MVP 👑")
            output.append(f"  {wall_of_fame.mvp_throne['agent_id']}")
            output.append("  Bow before greatness!\n")
        
        # Leaderboard
        output.append("📊 LEADERBOARD")
        output.append("-" * 40)
        
        leaderboard = wall_of_fame.get_leaderboard(5)
        for entry in leaderboard:
            rank_emoji = "🥇" if entry['rank'] == 1 else "🥈" if entry['rank'] == 2 else "🥉" if entry['rank'] == 3 else "  "
            awards_str = ", ".join(entry['awards']) if entry['awards'] else "No awards"
            output.append(f"{rank_emoji} #{entry['rank']} {entry['agent_id']}: {entry['score']:.1f}")
            if entry['awards']:
                output.append(f"     Awards: {awards_str}")
        
        # Hall of Fame
        output.append("\n🌟 RECENT HONORS")
        output.append("-" * 40)
        
        summary = wall_of_fame.get_wall_summary()
        for honor in summary['hall_of_fame']['recent_honors'][-3:]:
            output.append(f"  {honor['agent_id']}: {honor['award']}")
            output.append(f"    → {honor['reason']}")
        
        # Wall of Shame
        output.append("\n💩 WALL OF SHAME")
        output.append("-" * 40)
        
        if summary['wall_of_shame']['dunce_corner']:
            output.append("  DUNCE CORNER:")
            for agent in summary['wall_of_shame']['dunce_corner']:
                output.append(f"    🤡 {agent}")
        
        for shame in summary['wall_of_shame']['recent_shame'][-3:]:
            output.append(f"  {shame['agent_id']}: {shame['award']}")
            output.append(f"    → {shame['reason']}")
        
        # Statistics
        output.append("\n📈 STATISTICS")
        output.append("-" * 40)
        stats = summary['statistics']
        output.append(f"  Total Awards: {stats['total_awards_granted']}")
        output.append(f"  Most Decorated: {stats['most_decorated'] or 'None'}")
        output.append(f"  Most Shamed: {stats['most_shamed'] or 'None'}")
        
        output.append("\n" + "="*60)
        
        return "\n".join(output)
    
    @staticmethod
    def render_html(wall_of_fame: WallOfFame) -> str:
        """Render dashboard as HTML"""
        summary = wall_of_fame.get_wall_summary()
        leaderboard = wall_of_fame.get_leaderboard()
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>BrendaCore - Wall of Fame & Shame</title>
            <style>
                body { font-family: monospace; background: #1a1a1a; color: #0f0; padding: 20px; }
                .container { max-width: 1200px; margin: 0 auto; }
                .header { text-align: center; font-size: 24px; margin-bottom: 30px; }
                .mvp { background: gold; color: black; padding: 20px; text-align: center; margin: 20px 0; }
                .section { margin: 20px 0; padding: 15px; border: 1px solid #0f0; }
                .fame { border-color: gold; }
                .shame { border-color: red; }
                .leaderboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; }
                .agent-card { padding: 10px; border: 1px solid #0f0; }
                .rank-1 { border-color: gold; background: rgba(255,215,0,0.1); }
                .rank-2 { border-color: silver; background: rgba(192,192,192,0.1); }
                .rank-3 { border-color: #cd7f32; background: rgba(205,127,50,0.1); }
                .dunce { background: rgba(255,0,0,0.2); border-color: red; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    🏆 BRENDACORE WALL OF FAME & SHAME 💀
                </div>
        """
        
        # MVP Section
        if wall_of_fame.mvp_throne:
            html += f"""
                <div class="mvp">
                    👑 CURRENT MVP: {wall_of_fame.mvp_throne['agent_id']} 👑<br>
                    Bow before greatness!
                </div>
            """
        
        # Leaderboard
        html += '<div class="section"><h2>📊 Leaderboard</h2><div class="leaderboard">'
        for entry in leaderboard[:10]:
            rank_class = f"rank-{entry['rank']}" if entry['rank'] <= 3 else ""
            if entry['in_dunce_corner']:
                rank_class = "dunce"
            
            html += f"""
                <div class="agent-card {rank_class}">
                    <strong>#{entry['rank']} {entry['agent_id']}</strong><br>
                    Score: {entry['score']:.1f}<br>
                    {'👑 MVP' if entry['is_mvp'] else ''}
                    {'🤡 DUNCE' if entry['in_dunce_corner'] else ''}
                </div>
            """
        html += '</div></div>'
        
        # Hall of Fame
        html += '<div class="section fame"><h2>🌟 Hall of Fame</h2>'
        for honor in summary['hall_of_fame']['recent_honors'][-5:]:
            html += f"<p><strong>{honor['agent_id']}</strong>: {honor['award']}<br><em>{honor['reason']}</em></p>"
        html += '</div>'
        
        # Wall of Shame
        html += '<div class="section shame"><h2>💩 Wall of Shame</h2>'
        if summary['wall_of_shame']['dunce_corner']:
            html += '<h3>Dunce Corner</h3><ul>'
            for agent in summary['wall_of_shame']['dunce_corner']:
                html += f"<li>🤡 {agent}</li>"
            html += '</ul>'
        
        for shame in summary['wall_of_shame']['recent_shame'][-5:]:
            html += f"<p><strong>{shame['agent_id']}</strong>: {shame['award']}<br><em>{shame['reason']}</em></p>"
        html += '</div>'
        
        html += """
            </div>
        </body>
        </html>
        """
        
        return html