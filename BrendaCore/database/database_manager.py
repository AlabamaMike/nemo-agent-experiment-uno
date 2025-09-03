"""
Database Manager for PostgreSQL
Handles database connections, sessions, and operations
"""

import os
import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from datetime import datetime, timedelta

# Note: In production, would use SQLAlchemy
# from sqlalchemy import create_engine, pool, event
# from sqlalchemy.orm import sessionmaker, scoped_session
# from sqlalchemy.exc import SQLAlchemyError
# from sqlalchemy.pool import NullPool, QueuePool

from .models import Base, Agent, Project, Task, Interaction, Metrics

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration"""
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None,
        pool_size: int = 20,
        max_overflow: int = 40,
        pool_timeout: int = 30,
        echo: bool = False
    ):
        self.host = host or os.getenv('DB_HOST', 'localhost')
        self.port = port or int(os.getenv('DB_PORT', 5432))
        self.database = database or os.getenv('DB_NAME', 'brendacore')
        self.user = user or os.getenv('DB_USER', 'brenda')
        self.password = password or os.getenv('DB_PASSWORD', 'sass_queen_2024')
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.echo = echo
    
    def get_connection_string(self) -> str:
        """Get PostgreSQL connection string"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class DatabaseManager:
    """
    Manages database connections and operations
    """
    
    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig()
        self.engine = None
        self.session_factory = None
        self.scoped_session = None
        
        self._initialize_engine()
        logger.info("DatabaseManager initialized")
    
    def _initialize_engine(self):
        """Initialize database engine"""
        try:
            # In production:
            # self.engine = create_engine(
            #     self.config.get_connection_string(),
            #     poolclass=QueuePool,
            #     pool_size=self.config.pool_size,
            #     max_overflow=self.config.max_overflow,
            #     pool_timeout=self.config.pool_timeout,
            #     pool_pre_ping=True,  # Check connection health
            #     echo=self.config.echo
            # )
            
            # Mock engine
            self.engine = MockEngine(self.config)
            
            # Create session factory
            # self.session_factory = sessionmaker(bind=self.engine)
            # self.scoped_session = scoped_session(self.session_factory)
            
            self.session_factory = MockSessionFactory()
            self.scoped_session = self.session_factory
            
            logger.info("Database engine initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise
    
    def create_tables(self):
        """Create all database tables"""
        try:
            # In production: Base.metadata.create_all(self.engine)
            logger.info("Database tables created")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables (use with caution)"""
        try:
            # In production: Base.metadata.drop_all(self.engine)
            logger.warning("All database tables dropped")
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """Get database session context manager"""
        session = self.scoped_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Session error: {e}")
            raise
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """Check database health"""
        try:
            with self.get_session() as session:
                # In production: session.execute("SELECT 1")
                result = session.execute("SELECT 1")
                return result is not None
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with self.get_session() as session:
                stats = {
                    'agents': session.query(Agent).count(),
                    'projects': session.query(Project).count(),
                    'tasks': session.query(Task).count(),
                    'interactions': session.query(Interaction).count(),
                    'metrics': session.query(Metrics).count()
                }
                return stats
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}


class SessionManager:
    """
    Manages database sessions and transactions
    """
    
    def __init__(self, database_manager: DatabaseManager):
        self.db = database_manager
        self.active_sessions = []
    
    @contextmanager
    def transaction(self):
        """Transaction context manager"""
        session = self.db.scoped_session()
        self.active_sessions.append(session)
        
        try:
            yield session
            session.commit()
            logger.debug("Transaction committed")
        except Exception as e:
            session.rollback()
            logger.error(f"Transaction rolled back: {e}")
            raise
        finally:
            self.active_sessions.remove(session)
            session.close()
    
    def bulk_insert(self, objects: List[Any]) -> bool:
        """Bulk insert objects"""
        try:
            with self.transaction() as session:
                session.bulk_save_objects(objects)
                logger.info(f"Bulk inserted {len(objects)} objects")
                return True
        except Exception as e:
            logger.error(f"Bulk insert failed: {e}")
            return False
    
    def upsert(self, model_class, **kwargs) -> Any:
        """Insert or update object"""
        try:
            with self.transaction() as session:
                # Check for existing
                filters = {k: v for k, v in kwargs.items() 
                          if hasattr(model_class, k)}
                
                obj = session.query(model_class).filter_by(**filters).first()
                
                if obj:
                    # Update existing
                    for key, value in kwargs.items():
                        if hasattr(obj, key):
                            setattr(obj, key, value)
                    logger.debug(f"Updated {model_class.__name__}")
                else:
                    # Create new
                    obj = model_class(**kwargs)
                    session.add(obj)
                    logger.debug(f"Created new {model_class.__name__}")
                
                return obj
                
        except Exception as e:
            logger.error(f"Upsert failed: {e}")
            return None
    
    def paginated_query(
        self,
        model_class,
        page: int = 1,
        per_page: int = 20,
        filters: Dict[str, Any] = None,
        order_by: str = None
    ) -> Dict[str, Any]:
        """Paginated query"""
        try:
            with self.transaction() as session:
                query = session.query(model_class)
                
                # Apply filters
                if filters:
                    for key, value in filters.items():
                        if hasattr(model_class, key):
                            query = query.filter(getattr(model_class, key) == value)
                
                # Apply ordering
                if order_by and hasattr(model_class, order_by):
                    query = query.order_by(getattr(model_class, order_by))
                
                # Get total count
                total = query.count()
                
                # Apply pagination
                offset = (page - 1) * per_page
                items = query.offset(offset).limit(per_page).all()
                
                return {
                    'items': items,
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'pages': (total + per_page - 1) // per_page
                }
                
        except Exception as e:
            logger.error(f"Paginated query failed: {e}")
            return {
                'items': [],
                'total': 0,
                'page': page,
                'per_page': per_page,
                'pages': 0
            }
    
    def cleanup_old_data(self, days: int = 30) -> int:
        """Cleanup old data"""
        try:
            with self.transaction() as session:
                cutoff = datetime.utcnow() - timedelta(days=days)
                
                # Clean old metrics
                deleted = session.query(Metrics).filter(
                    Metrics.timestamp < cutoff
                ).delete()
                
                # Clean old interactions
                deleted += session.query(Interaction).filter(
                    Interaction.created_at < cutoff
                ).delete()
                
                logger.info(f"Cleaned up {deleted} old records")
                return deleted
                
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return 0


# Mock implementations for development

class MockEngine:
    """Mock database engine"""
    
    def __init__(self, config):
        self.config = config
        self.data = {
            'agents': {},
            'projects': {},
            'tasks': {},
            'interactions': {},
            'metrics': []
        }


class MockSession:
    """Mock database session"""
    
    def __init__(self, engine=None):
        self.engine = engine or MockEngine(None)
        self.pending = []
    
    def add(self, obj):
        self.pending.append(obj)
    
    def commit(self):
        # Process pending objects
        for obj in self.pending:
            # Store in mock database
            pass
        self.pending.clear()
    
    def rollback(self):
        self.pending.clear()
    
    def close(self):
        pass
    
    def execute(self, query):
        return True
    
    def query(self, model_class):
        return MockQuery(model_class, self)
    
    def bulk_save_objects(self, objects):
        for obj in objects:
            self.add(obj)


class MockQuery:
    """Mock query object"""
    
    def __init__(self, model_class, session):
        self.model_class = model_class
        self.session = session
        self.filters = {}
    
    def filter_by(self, **kwargs):
        self.filters.update(kwargs)
        return self
    
    def filter(self, *args):
        return self
    
    def first(self):
        # Return mock object
        return None
    
    def all(self):
        return []
    
    def count(self):
        return 0
    
    def offset(self, n):
        return self
    
    def limit(self, n):
        return self
    
    def order_by(self, *args):
        return self
    
    def delete(self):
        return 0


class MockSessionFactory:
    """Mock session factory"""
    
    def __call__(self):
        return MockSession()