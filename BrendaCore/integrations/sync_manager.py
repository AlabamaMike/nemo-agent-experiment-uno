"""
Sync Manager for Multi-Platform Integration
Handles synchronization between GitHub, Jira, Azure DevOps, etc.
"""

import time
import asyncio
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SyncStatus(Enum):
    """Synchronization status"""
    IDLE = "idle"
    SYNCING = "syncing"
    CONFLICT = "conflict"
    ERROR = "error"
    SUCCESS = "success"


class ConflictType(Enum):
    """Types of conflicts"""
    DUPLICATE = "duplicate"
    FIELD_MISMATCH = "field_mismatch"
    STATE_CONFLICT = "state_conflict"
    PRIORITY_CONFLICT = "priority_conflict"
    ASSIGNMENT_CONFLICT = "assignment_conflict"


class Platform(Enum):
    """Supported platforms"""
    GITHUB = "github"
    JIRA = "jira"
    AZURE_DEVOPS = "azure_devops"
    TRELLO = "trello"
    ASANA = "asana"


@dataclass
class SyncItem:
    """Item being synchronized"""
    item_id: str
    item_type: str  # issue, pr, task, etc.
    platform: Platform
    data: Dict[str, Any]
    last_modified: datetime
    sync_key: Optional[str] = None  # Cross-platform identifier


@dataclass
class SyncConflict:
    """Synchronization conflict"""
    conflict_id: str
    conflict_type: ConflictType
    items: List[SyncItem]
    detected_at: datetime
    resolution: Optional[str] = None
    resolved_at: Optional[datetime] = None


class ConflictResolver:
    """
    Resolves conflicts between different platforms
    """
    
    def __init__(self):
        self.resolution_strategies = self._init_strategies()
        self.conflict_log = []
        
    def _init_strategies(self) -> Dict[ConflictType, Any]:
        """Initialize resolution strategies"""
        return {
            ConflictType.DUPLICATE: self._resolve_duplicate,
            ConflictType.FIELD_MISMATCH: self._resolve_field_mismatch,
            ConflictType.STATE_CONFLICT: self._resolve_state_conflict,
            ConflictType.PRIORITY_CONFLICT: self._resolve_priority_conflict,
            ConflictType.ASSIGNMENT_CONFLICT: self._resolve_assignment_conflict
        }
    
    def detect_conflict(self, items: List[SyncItem]) -> Optional[SyncConflict]:
        """Detect conflicts between items"""
        if len(items) < 2:
            return None
        
        # Check for duplicates
        if self._are_duplicates(items):
            return SyncConflict(
                conflict_id=f"conflict_{int(time.time())}",
                conflict_type=ConflictType.DUPLICATE,
                items=items,
                detected_at=datetime.now()
            )
        
        # Check for field mismatches
        mismatch = self._check_field_mismatch(items)
        if mismatch:
            return SyncConflict(
                conflict_id=f"conflict_{int(time.time())}",
                conflict_type=ConflictType.FIELD_MISMATCH,
                items=items,
                detected_at=datetime.now()
            )
        
        # Check for state conflicts
        if self._has_state_conflict(items):
            return SyncConflict(
                conflict_id=f"conflict_{int(time.time())}",
                conflict_type=ConflictType.STATE_CONFLICT,
                items=items,
                detected_at=datetime.now()
            )
        
        return None
    
    def resolve_conflict(self, conflict: SyncConflict) -> Dict[str, Any]:
        """Resolve a conflict"""
        if conflict.conflict_type in self.resolution_strategies:
            resolution = self.resolution_strategies[conflict.conflict_type](conflict)
            
            # Update conflict
            conflict.resolution = resolution['strategy']
            conflict.resolved_at = datetime.now()
            
            # Log resolution
            self.conflict_log.append(conflict)
            
            logger.info(f"Resolved conflict {conflict.conflict_id} using {resolution['strategy']}")
            return resolution
        
        return {
            'strategy': 'manual',
            'action': 'escalate_to_human',
            'reason': 'No automatic resolution available'
        }
    
    def _are_duplicates(self, items: List[SyncItem]) -> bool:
        """Check if items are duplicates"""
        # Simple duplicate check - compare titles/names
        titles = []
        for item in items:
            title = item.data.get('title') or item.data.get('name', '')
            titles.append(title.lower())
        
        # Check for similar titles
        for i, title1 in enumerate(titles):
            for title2 in titles[i+1:]:
                similarity = self._calculate_similarity(title1, title2)
                if similarity > 0.8:
                    return True
        
        return False
    
    def _check_field_mismatch(self, items: List[SyncItem]) -> Optional[str]:
        """Check for field mismatches"""
        # Compare critical fields
        critical_fields = ['priority', 'status', 'assignee']
        
        for field in critical_fields:
            values = [item.data.get(field) for item in items]
            unique_values = set(v for v in values if v is not None)
            
            if len(unique_values) > 1:
                return f"Mismatch in {field}: {unique_values}"
        
        return None
    
    def _has_state_conflict(self, items: List[SyncItem]) -> bool:
        """Check for state conflicts"""
        states = [item.data.get('state') or item.data.get('status') for item in items]
        
        # Check for conflicting states
        if 'closed' in states and 'open' in states:
            return True
        if 'done' in states and 'in_progress' in states:
            return True
        
        return False
    
    def _resolve_duplicate(self, conflict: SyncConflict) -> Dict[str, Any]:
        """Resolve duplicate conflict"""
        # Keep the most recently updated item
        items_sorted = sorted(conflict.items, key=lambda x: x.last_modified, reverse=True)
        
        return {
            'strategy': 'keep_newest',
            'action': 'merge',
            'primary': items_sorted[0].item_id,
            'merge_into': items_sorted[0].platform.value,
            'delete': [item.item_id for item in items_sorted[1:]]
        }
    
    def _resolve_field_mismatch(self, conflict: SyncConflict) -> Dict[str, Any]:
        """Resolve field mismatch"""
        # Use platform priority (GitHub > Jira > Others)
        platform_priority = {
            Platform.GITHUB: 3,
            Platform.JIRA: 2,
            Platform.AZURE_DEVOPS: 2,
            Platform.TRELLO: 1,
            Platform.ASANA: 1
        }
        
        items_sorted = sorted(
            conflict.items,
            key=lambda x: platform_priority.get(x.platform, 0),
            reverse=True
        )
        
        return {
            'strategy': 'platform_priority',
            'action': 'update_all',
            'source': items_sorted[0].item_id,
            'source_platform': items_sorted[0].platform.value,
            'targets': [item.item_id for item in items_sorted[1:]]
        }
    
    def _resolve_state_conflict(self, conflict: SyncConflict) -> Dict[str, Any]:
        """Resolve state conflict"""
        # Use most restrictive state
        states = [item.data.get('state') or item.data.get('status') for item in conflict.items]
        
        if 'closed' in states or 'done' in states:
            target_state = 'closed'
        elif 'blocked' in states:
            target_state = 'blocked'
        elif 'in_progress' in states:
            target_state = 'in_progress'
        else:
            target_state = 'open'
        
        return {
            'strategy': 'most_restrictive',
            'action': 'synchronize_state',
            'target_state': target_state,
            'items': [item.item_id for item in conflict.items]
        }
    
    def _resolve_priority_conflict(self, conflict: SyncConflict) -> Dict[str, Any]:
        """Resolve priority conflict"""
        # Use highest priority
        priority_map = {
            'critical': 5,
            'high': 4,
            'medium': 3,
            'low': 2,
            'trivial': 1
        }
        
        priorities = []
        for item in conflict.items:
            priority = item.data.get('priority', 'medium')
            priorities.append((priority, priority_map.get(priority, 3)))
        
        highest_priority = max(priorities, key=lambda x: x[1])
        
        return {
            'strategy': 'highest_priority',
            'action': 'update_priority',
            'target_priority': highest_priority[0],
            'items': [item.item_id for item in conflict.items]
        }
    
    def _resolve_assignment_conflict(self, conflict: SyncConflict) -> Dict[str, Any]:
        """Resolve assignment conflict"""
        # Check workload and assign to least loaded
        assignees = [item.data.get('assignee') for item in conflict.items]
        assignees = [a for a in assignees if a]
        
        if assignees:
            # For now, keep first assignee
            return {
                'strategy': 'keep_first',
                'action': 'update_assignment',
                'assignee': assignees[0],
                'items': [item.item_id for item in conflict.items]
            }
        
        return {
            'strategy': 'unassigned',
            'action': 'clear_assignment',
            'items': [item.item_id for item in conflict.items]
        }
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity"""
        # Simple similarity calculation
        if not str1 or not str2:
            return 0.0
        
        words1 = set(str1.lower().split())
        words2 = set(str2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)


class SyncManager:
    """
    Manages synchronization between multiple platforms
    """
    
    def __init__(self):
        self.platforms = {}
        self.sync_mappings = {}
        self.sync_queue = []
        self.conflict_resolver = ConflictResolver()
        self.sync_status = SyncStatus.IDLE
        self.last_sync = {}
        self.sync_interval = 300  # 5 minutes
        
        logger.info("SyncManager initialized")
    
    def register_platform(self, platform: Platform, adapter: Any):
        """Register a platform adapter"""
        self.platforms[platform] = adapter
        self.last_sync[platform] = datetime.now() - timedelta(hours=1)
        logger.info(f"Registered platform: {platform.value}")
    
    def create_mapping(
        self,
        source_platform: Platform,
        source_id: str,
        target_platform: Platform,
        target_id: str
    ):
        """Create a mapping between items on different platforms"""
        sync_key = f"{source_platform.value}:{source_id}"
        
        if sync_key not in self.sync_mappings:
            self.sync_mappings[sync_key] = {}
        
        self.sync_mappings[sync_key][target_platform] = target_id
        
        logger.info(f"Created mapping: {source_platform.value}:{source_id} -> {target_platform.value}:{target_id}")
    
    async def sync_all(self) -> Dict[str, Any]:
        """Synchronize all platforms"""
        self.sync_status = SyncStatus.SYNCING
        results = {
            'synced_items': 0,
            'conflicts': 0,
            'errors': 0,
            'platforms': {}
        }
        
        try:
            for platform in self.platforms:
                platform_results = await self.sync_platform(platform)
                results['platforms'][platform.value] = platform_results
                results['synced_items'] += platform_results.get('synced', 0)
                results['conflicts'] += platform_results.get('conflicts', 0)
                results['errors'] += platform_results.get('errors', 0)
            
            self.sync_status = SyncStatus.SUCCESS
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            self.sync_status = SyncStatus.ERROR
            results['errors'] += 1
        
        return results
    
    async def sync_platform(self, platform: Platform) -> Dict[str, Any]:
        """Synchronize a specific platform"""
        if platform not in self.platforms:
            return {'error': 'Platform not registered'}
        
        adapter = self.platforms[platform]
        results = {
            'synced': 0,
            'conflicts': 0,
            'errors': 0
        }
        
        try:
            # Get items from platform
            items = await self._fetch_items(adapter, platform)
            
            # Process each item
            for item in items:
                sync_result = await self._sync_item(item, platform)
                
                if sync_result.get('status') == 'success':
                    results['synced'] += 1
                elif sync_result.get('status') == 'conflict':
                    results['conflicts'] += 1
                else:
                    results['errors'] += 1
            
            self.last_sync[platform] = datetime.now()
            
        except Exception as e:
            logger.error(f"Platform sync failed for {platform.value}: {e}")
            results['errors'] += 1
        
        return results
    
    async def _fetch_items(self, adapter: Any, platform: Platform) -> List[SyncItem]:
        """Fetch items from a platform"""
        # This would call the appropriate method on the adapter
        # For now, return mock data
        return [
            SyncItem(
                item_id=f"{platform.value}_1",
                item_type="issue",
                platform=platform,
                data={'title': 'Test Issue', 'status': 'open'},
                last_modified=datetime.now()
            )
        ]
    
    async def _sync_item(self, item: SyncItem, source_platform: Platform) -> Dict[str, Any]:
        """Synchronize a single item across platforms"""
        sync_key = f"{source_platform.value}:{item.item_id}"
        
        # Check for existing mappings
        if sync_key in self.sync_mappings:
            # Update existing items
            for target_platform, target_id in self.sync_mappings[sync_key].items():
                if target_platform in self.platforms:
                    # Check for conflicts
                    target_item = await self._fetch_item(target_platform, target_id)
                    
                    if target_item:
                        conflict = self.conflict_resolver.detect_conflict([item, target_item])
                        
                        if conflict:
                            resolution = self.conflict_resolver.resolve_conflict(conflict)
                            return {'status': 'conflict', 'resolution': resolution}
                    
                    # Update target
                    await self._update_item(target_platform, target_id, item.data)
            
            return {'status': 'success'}
        else:
            # Create new items on other platforms
            for target_platform in self.platforms:
                if target_platform != source_platform:
                    target_id = await self._create_item(target_platform, item.data)
                    if target_id:
                        self.create_mapping(source_platform, item.item_id, target_platform, target_id)
            
            return {'status': 'success'}
    
    async def _fetch_item(self, platform: Platform, item_id: str) -> Optional[SyncItem]:
        """Fetch a specific item from a platform"""
        # Mock implementation
        return SyncItem(
            item_id=item_id,
            item_type="issue",
            platform=platform,
            data={'title': 'Test Issue', 'status': 'open'},
            last_modified=datetime.now()
        )
    
    async def _update_item(self, platform: Platform, item_id: str, data: Dict[str, Any]):
        """Update an item on a platform"""
        # This would call the appropriate update method on the adapter
        logger.info(f"Updated {item_id} on {platform.value}")
    
    async def _create_item(self, platform: Platform, data: Dict[str, Any]) -> Optional[str]:
        """Create an item on a platform"""
        # This would call the appropriate create method on the adapter
        new_id = f"{platform.value}_new_{int(time.time())}"
        logger.info(f"Created {new_id} on {platform.value}")
        return new_id
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get synchronization status"""
        return {
            'status': self.sync_status.value,
            'platforms': list(self.platforms.keys()),
            'mappings': len(self.sync_mappings),
            'last_sync': {
                platform.value: last.isoformat()
                for platform, last in self.last_sync.items()
            },
            'conflicts_resolved': len(self.conflict_resolver.conflict_log)
        }
    
    def needs_sync(self, platform: Platform) -> bool:
        """Check if platform needs synchronization"""
        if platform not in self.last_sync:
            return True
        
        time_since_sync = datetime.now() - self.last_sync[platform]
        return time_since_sync.total_seconds() > self.sync_interval