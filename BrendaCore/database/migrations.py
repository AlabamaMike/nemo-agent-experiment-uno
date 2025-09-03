"""
Database Migrations Manager
Handles schema migrations and version control
"""

import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

# Note: In production, would use Alembic
# from alembic import command
# from alembic.config import Config
# from alembic.script import ScriptDirectory
# from alembic.runtime.migration import MigrationContext

logger = logging.getLogger(__name__)


class Migration:
    """Represents a database migration"""
    
    def __init__(
        self,
        version: str,
        description: str,
        up_sql: str,
        down_sql: str,
        checksum: Optional[str] = None
    ):
        self.version = version
        self.description = description
        self.up_sql = up_sql
        self.down_sql = down_sql
        self.checksum = checksum or self._calculate_checksum()
        self.applied_at = None
    
    def _calculate_checksum(self) -> str:
        """Calculate migration checksum"""
        content = f"{self.version}{self.up_sql}{self.down_sql}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'version': self.version,
            'description': self.description,
            'checksum': self.checksum,
            'applied_at': self.applied_at.isoformat() if self.applied_at else None
        }


class MigrationManager:
    """
    Manages database migrations
    """
    
    def __init__(self, database_manager=None):
        self.db = database_manager
        self.migrations_dir = "database/migrations"
        self.migrations = self._load_migrations()
        self.applied_migrations = []
        
        logger.info("MigrationManager initialized")
    
    def _load_migrations(self) -> List[Migration]:
        """Load migration definitions"""
        migrations = [
            Migration(
                version="001",
                description="Initial schema",
                up_sql="""
                    CREATE TABLE IF NOT EXISTS agents (
                        id SERIAL PRIMARY KEY,
                        agent_id VARCHAR(100) UNIQUE NOT NULL,
                        agent_type VARCHAR(50) NOT NULL,
                        status VARCHAR(20) DEFAULT 'idle',
                        overall_score FLOAT DEFAULT 50.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX idx_agents_agent_id ON agents(agent_id);
                    CREATE INDEX idx_agents_status ON agents(status);
                """,
                down_sql="DROP TABLE IF EXISTS agents;"
            ),
            
            Migration(
                version="002",
                description="Add projects table",
                up_sql="""
                    CREATE TABLE IF NOT EXISTS projects (
                        id SERIAL PRIMARY KEY,
                        project_id VARCHAR(100) UNIQUE NOT NULL,
                        name VARCHAR(200) NOT NULL,
                        description TEXT,
                        phase VARCHAR(50) DEFAULT 'planning',
                        health_score FLOAT DEFAULT 50.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX idx_projects_project_id ON projects(project_id);
                    CREATE INDEX idx_projects_health ON projects(health_score);
                """,
                down_sql="DROP TABLE IF EXISTS projects;"
            ),
            
            Migration(
                version="003",
                description="Add tasks table",
                up_sql="""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id SERIAL PRIMARY KEY,
                        task_id VARCHAR(100) UNIQUE NOT NULL,
                        title VARCHAR(500) NOT NULL,
                        description TEXT,
                        status VARCHAR(20) DEFAULT 'pending',
                        priority INTEGER DEFAULT 5,
                        agent_id INTEGER REFERENCES agents(id),
                        project_id INTEGER REFERENCES projects(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX idx_tasks_task_id ON tasks(task_id);
                    CREATE INDEX idx_tasks_status ON tasks(status);
                    CREATE INDEX idx_tasks_agent ON tasks(agent_id);
                    CREATE INDEX idx_tasks_project ON tasks(project_id);
                """,
                down_sql="DROP TABLE IF EXISTS tasks;"
            ),
            
            Migration(
                version="004",
                description="Add interactions table",
                up_sql="""
                    CREATE TABLE IF NOT EXISTS interactions (
                        id SERIAL PRIMARY KEY,
                        interaction_id VARCHAR(100) UNIQUE NOT NULL,
                        sender_id INTEGER REFERENCES agents(id),
                        recipient_id VARCHAR(100),
                        message_type VARCHAR(50),
                        subject VARCHAR(500),
                        content TEXT,
                        sass_level INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX idx_interactions_sender ON interactions(sender_id);
                    CREATE INDEX idx_interactions_type ON interactions(message_type);
                    CREATE INDEX idx_interactions_created ON interactions(created_at);
                """,
                down_sql="DROP TABLE IF EXISTS interactions;"
            ),
            
            Migration(
                version="005",
                description="Add metrics table",
                up_sql="""
                    CREATE TABLE IF NOT EXISTS metrics (
                        id SERIAL PRIMARY KEY,
                        agent_id INTEGER REFERENCES agents(id),
                        project_id INTEGER REFERENCES projects(id),
                        metric_type VARCHAR(50) NOT NULL,
                        metric_name VARCHAR(100) NOT NULL,
                        metric_value FLOAT NOT NULL,
                        tags JSONB,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX idx_metrics_agent ON metrics(agent_id);
                    CREATE INDEX idx_metrics_project ON metrics(project_id);
                    CREATE INDEX idx_metrics_type ON metrics(metric_type);
                    CREATE INDEX idx_metrics_timestamp ON metrics(timestamp);
                """,
                down_sql="DROP TABLE IF EXISTS metrics;"
            ),
            
            Migration(
                version="006",
                description="Add audit log table",
                up_sql="""
                    CREATE TABLE IF NOT EXISTS audit_logs (
                        id SERIAL PRIMARY KEY,
                        event_type VARCHAR(50) NOT NULL,
                        event_action VARCHAR(100) NOT NULL,
                        event_result VARCHAR(20),
                        actor_type VARCHAR(50),
                        actor_id VARCHAR(100),
                        target_type VARCHAR(50),
                        target_id VARCHAR(100),
                        description TEXT,
                        metadata JSONB,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX idx_audit_event_type ON audit_logs(event_type);
                    CREATE INDEX idx_audit_actor ON audit_logs(actor_id);
                    CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);
                """,
                down_sql="DROP TABLE IF EXISTS audit_logs;"
            ),
            
            Migration(
                version="007",
                description="Add performance indexes",
                up_sql="""
                    -- Composite indexes for common queries
                    CREATE INDEX idx_agents_performance ON agents(overall_score, status);
                    CREATE INDEX idx_projects_health_phase ON projects(health_score, phase);
                    CREATE INDEX idx_tasks_status_priority ON tasks(status, priority);
                    
                    -- Partial indexes for active records
                    CREATE INDEX idx_active_agents ON agents(agent_id) WHERE status != 'terminated';
                    CREATE INDEX idx_open_tasks ON tasks(task_id) WHERE status IN ('pending', 'assigned', 'in_progress');
                """,
                down_sql="""
                    DROP INDEX IF EXISTS idx_agents_performance;
                    DROP INDEX IF EXISTS idx_projects_health_phase;
                    DROP INDEX IF EXISTS idx_tasks_status_priority;
                    DROP INDEX IF EXISTS idx_active_agents;
                    DROP INDEX IF EXISTS idx_open_tasks;
                """
            )
        ]
        
        return migrations
    
    def get_current_version(self) -> Optional[str]:
        """Get current database version"""
        try:
            if not self.db:
                return None
            
            with self.db.get_session() as session:
                # Check migration history table
                result = session.execute("""
                    SELECT version FROM migration_history 
                    ORDER BY applied_at DESC 
                    LIMIT 1
                """)
                
                row = result.fetchone()
                return row[0] if row else None
                
        except Exception as e:
            logger.debug(f"No migration history found: {e}")
            return None
    
    def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations"""
        current_version = self.get_current_version()
        
        if not current_version:
            return self.migrations
        
        # Find migrations after current version
        pending = []
        found_current = False
        
        for migration in self.migrations:
            if found_current:
                pending.append(migration)
            elif migration.version == current_version:
                found_current = True
        
        return pending
    
    def migrate_up(self, target_version: Optional[str] = None) -> Dict[str, Any]:
        """Run migrations up to target version"""
        results = {
            'success': True,
            'applied': [],
            'errors': []
        }
        
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("No pending migrations")
            return results
        
        for migration in pending:
            if target_version and migration.version > target_version:
                break
            
            try:
                self._apply_migration(migration)
                results['applied'].append(migration.version)
                logger.info(f"Applied migration {migration.version}: {migration.description}")
                
            except Exception as e:
                logger.error(f"Migration {migration.version} failed: {e}")
                results['errors'].append({
                    'version': migration.version,
                    'error': str(e)
                })
                results['success'] = False
                break
        
        return results
    
    def migrate_down(self, target_version: str) -> Dict[str, Any]:
        """Rollback migrations to target version"""
        results = {
            'success': True,
            'rolled_back': [],
            'errors': []
        }
        
        current = self.get_current_version()
        
        if not current or current <= target_version:
            logger.info("Nothing to rollback")
            return results
        
        # Find migrations to rollback
        to_rollback = []
        for migration in reversed(self.migrations):
            if migration.version <= target_version:
                break
            if migration.version <= current:
                to_rollback.append(migration)
        
        for migration in to_rollback:
            try:
                self._rollback_migration(migration)
                results['rolled_back'].append(migration.version)
                logger.info(f"Rolled back migration {migration.version}")
                
            except Exception as e:
                logger.error(f"Rollback {migration.version} failed: {e}")
                results['errors'].append({
                    'version': migration.version,
                    'error': str(e)
                })
                results['success'] = False
                break
        
        return results
    
    def _apply_migration(self, migration: Migration):
        """Apply a single migration"""
        if not self.db:
            raise Exception("Database manager not configured")
        
        with self.db.get_session() as session:
            # Execute migration SQL
            session.execute(migration.up_sql)
            
            # Record in history
            session.execute("""
                INSERT INTO migration_history (version, description, checksum, applied_at)
                VALUES (:version, :description, :checksum, :applied_at)
            """, {
                'version': migration.version,
                'description': migration.description,
                'checksum': migration.checksum,
                'applied_at': datetime.utcnow()
            })
    
    def _rollback_migration(self, migration: Migration):
        """Rollback a single migration"""
        if not self.db:
            raise Exception("Database manager not configured")
        
        with self.db.get_session() as session:
            # Execute rollback SQL
            session.execute(migration.down_sql)
            
            # Remove from history
            session.execute("""
                DELETE FROM migration_history WHERE version = :version
            """, {'version': migration.version})
    
    def create_migration_history_table(self):
        """Create migration history table"""
        if not self.db:
            return
        
        try:
            with self.db.get_session() as session:
                session.execute("""
                    CREATE TABLE IF NOT EXISTS migration_history (
                        id SERIAL PRIMARY KEY,
                        version VARCHAR(20) UNIQUE NOT NULL,
                        description VARCHAR(500),
                        checksum VARCHAR(20),
                        applied_at TIMESTAMP NOT NULL,
                        execution_time_ms INTEGER
                    );
                    
                    CREATE INDEX idx_migration_version ON migration_history(version);
                    CREATE INDEX idx_migration_applied ON migration_history(applied_at);
                """)
                
            logger.info("Migration history table created")
            
        except Exception as e:
            logger.error(f"Failed to create migration history table: {e}")
    
    def validate_migrations(self) -> Dict[str, Any]:
        """Validate migration checksums"""
        results = {
            'valid': True,
            'issues': []
        }
        
        if not self.db:
            return results
        
        try:
            with self.db.get_session() as session:
                # Get applied migrations
                result = session.execute("""
                    SELECT version, checksum FROM migration_history
                """)
                
                applied = {row[0]: row[1] for row in result}
                
                # Validate checksums
                for migration in self.migrations:
                    if migration.version in applied:
                        if applied[migration.version] != migration.checksum:
                            results['valid'] = False
                            results['issues'].append({
                                'version': migration.version,
                                'issue': 'Checksum mismatch',
                                'expected': migration.checksum,
                                'actual': applied[migration.version]
                            })
        
        except Exception as e:
            logger.error(f"Migration validation failed: {e}")
            results['valid'] = False
            results['issues'].append({'error': str(e)})
        
        return results
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get migration status"""
        current = self.get_current_version()
        pending = self.get_pending_migrations()
        
        return {
            'current_version': current,
            'latest_version': self.migrations[-1].version if self.migrations else None,
            'pending_count': len(pending),
            'pending_versions': [m.version for m in pending],
            'total_migrations': len(self.migrations)
        }