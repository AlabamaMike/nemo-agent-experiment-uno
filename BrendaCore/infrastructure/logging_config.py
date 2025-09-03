"""
Comprehensive Logging Configuration
Production-ready logging with multiple handlers and formatters
"""

import os
import sys
import json
import logging
import logging.handlers
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
import traceback


class LogLevel(Enum):
    """Log levels"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LogFormat(Enum):
    """Log formats"""
    SIMPLE = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DETAILED = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    JSON = "json"
    STRUCTURED = "structured"


class SassLogFilter(logging.Filter):
    """Add sass level to log records"""
    
    def filter(self, record):
        # Add sass metadata if available
        if not hasattr(record, 'sass_level'):
            record.sass_level = 0
        if not hasattr(record, 'sass_quip'):
            record.sass_quip = None
        return True


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'process': record.process,
            'thread': record.thread
        }
        
        # Add extra fields
        if hasattr(record, 'sass_level'):
            log_data['sass_level'] = record.sass_level
        if hasattr(record, 'sass_quip'):
            log_data['sass_quip'] = record.sass_quip
        if hasattr(record, 'agent_id'):
            log_data['agent_id'] = record.agent_id
        if hasattr(record, 'project_id'):
            log_data['project_id'] = record.project_id
        if hasattr(record, 'task_id'):
            log_data['task_id'] = record.task_id
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_data)


class BrendaLogger:
    """
    Custom logger with sass integration
    """
    
    def __init__(self, name: str, sass_engine=None):
        self.logger = logging.getLogger(name)
        self.sass_engine = sass_engine
        self.context = {}
    
    def set_context(self, **kwargs):
        """Set logging context"""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear logging context"""
        self.context.clear()
    
    def _log_with_sass(self, level: int, message: str, sass_level: int = 0, **kwargs):
        """Log with sass metadata"""
        extra = self.context.copy()
        extra.update(kwargs)
        
        # Add sass quip if engine available
        if self.sass_engine and sass_level > 0:
            quip = self.sass_engine.get_quip(sass_level=sass_level)
            extra['sass_level'] = sass_level
            extra['sass_quip'] = quip
            message = f"{message} | {quip}"
        
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        self._log_with_sass(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log_with_sass(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, sass_level: int = 5, **kwargs):
        self._log_with_sass(logging.WARNING, message, sass_level, **kwargs)
    
    def error(self, message: str, sass_level: int = 7, **kwargs):
        self._log_with_sass(logging.ERROR, message, sass_level, **kwargs)
    
    def critical(self, message: str, sass_level: int = 10, **kwargs):
        self._log_with_sass(logging.CRITICAL, message, sass_level, **kwargs)
    
    def sass(self, message: str, level: int = logging.INFO, sass_level: int = 8):
        """Log pure sass"""
        self._log_with_sass(level, message, sass_level, event_type='sass')


class LoggingConfig:
    """
    Centralized logging configuration
    """
    
    def __init__(
        self,
        log_level: LogLevel = LogLevel.INFO,
        log_format: LogFormat = LogFormat.DETAILED,
        log_dir: str = "logs",
        enable_console: bool = True,
        enable_file: bool = True,
        enable_syslog: bool = False,
        enable_json: bool = False,
        max_bytes: int = 10485760,  # 10MB
        backup_count: int = 10
    ):
        self.log_level = log_level
        self.log_format = log_format
        self.log_dir = log_dir
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.enable_syslog = enable_syslog
        self.enable_json = enable_json
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        
        # Create log directory
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure logging
        self._configure_logging()
    
    def _configure_logging(self):
        """Configure Python logging"""
        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level.value)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Add sass filter
        sass_filter = SassLogFilter()
        
        # Console handler
        if self.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level.value)
            
            if self.log_format == LogFormat.JSON:
                console_handler.setFormatter(JSONFormatter())
            else:
                console_handler.setFormatter(
                    logging.Formatter(self.log_format.value)
                )
            
            console_handler.addFilter(sass_filter)
            root_logger.addHandler(console_handler)
        
        # File handler with rotation
        if self.enable_file:
            file_path = os.path.join(self.log_dir, "brendacore.log")
            file_handler = logging.handlers.RotatingFileHandler(
                file_path,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count
            )
            file_handler.setLevel(self.log_level.value)
            
            if self.log_format == LogFormat.JSON:
                file_handler.setFormatter(JSONFormatter())
            else:
                file_handler.setFormatter(
                    logging.Formatter(self.log_format.value)
                )
            
            file_handler.addFilter(sass_filter)
            root_logger.addHandler(file_handler)
        
        # JSON file handler for structured logs
        if self.enable_json:
            json_path = os.path.join(self.log_dir, "brendacore.json")
            json_handler = logging.handlers.RotatingFileHandler(
                json_path,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count
            )
            json_handler.setLevel(self.log_level.value)
            json_handler.setFormatter(JSONFormatter())
            json_handler.addFilter(sass_filter)
            root_logger.addHandler(json_handler)
        
        # Syslog handler
        if self.enable_syslog:
            try:
                syslog_handler = logging.handlers.SysLogHandler(
                    address=('localhost', 514)
                )
                syslog_handler.setLevel(self.log_level.value)
                syslog_handler.setFormatter(
                    logging.Formatter(
                        'BrendaCore: %(levelname)s - %(message)s'
                    )
                )
                root_logger.addHandler(syslog_handler)
            except Exception as e:
                print(f"Failed to setup syslog: {e}")
        
        # Error file for critical issues
        error_path = os.path.join(self.log_dir, "errors.log")
        error_handler = logging.handlers.RotatingFileHandler(
            error_path,
            maxBytes=self.max_bytes,
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(
            logging.Formatter(LogFormat.DETAILED.value)
        )
        root_logger.addHandler(error_handler)
        
        # Performance log
        perf_logger = logging.getLogger('performance')
        perf_path = os.path.join(self.log_dir, "performance.log")
        perf_handler = logging.handlers.RotatingFileHandler(
            perf_path,
            maxBytes=self.max_bytes,
            backupCount=5
        )
        perf_handler.setFormatter(JSONFormatter())
        perf_logger.addHandler(perf_handler)
        perf_logger.setLevel(logging.INFO)
        perf_logger.propagate = False
        
        # Security log
        security_logger = logging.getLogger('security')
        security_path = os.path.join(self.log_dir, "security.log")
        security_handler = logging.handlers.RotatingFileHandler(
            security_path,
            maxBytes=self.max_bytes,
            backupCount=10
        )
        security_handler.setFormatter(JSONFormatter())
        security_logger.addHandler(security_handler)
        security_logger.setLevel(logging.INFO)
        security_logger.propagate = False
        
        # Audit log
        audit_logger = logging.getLogger('audit')
        audit_path = os.path.join(self.log_dir, "audit.log")
        audit_handler = logging.handlers.RotatingFileHandler(
            audit_path,
            maxBytes=self.max_bytes,
            backupCount=30  # Keep more audit logs
        )
        audit_handler.setFormatter(JSONFormatter())
        audit_logger.addHandler(audit_handler)
        audit_logger.setLevel(logging.INFO)
        audit_logger.propagate = False
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a configured logger"""
        return logging.getLogger(name)
    
    def get_brenda_logger(self, name: str, sass_engine=None) -> BrendaLogger:
        """Get a Brenda logger with sass"""
        return BrendaLogger(name, sass_engine)
    
    def log_performance(self, operation: str, duration: float, **kwargs):
        """Log performance metrics"""
        perf_logger = logging.getLogger('performance')
        perf_logger.info(
            f"Performance metric",
            extra={
                'operation': operation,
                'duration_ms': duration * 1000,
                **kwargs
            }
        )
    
    def log_security(self, event: str, **kwargs):
        """Log security events"""
        security_logger = logging.getLogger('security')
        security_logger.info(
            f"Security event: {event}",
            extra=kwargs
        )
    
    def log_audit(
        self,
        action: str,
        actor: str,
        target: str,
        result: str,
        **kwargs
    ):
        """Log audit events"""
        audit_logger = logging.getLogger('audit')
        audit_logger.info(
            f"Audit: {action} by {actor} on {target}",
            extra={
                'action': action,
                'actor': actor,
                'target': target,
                'result': result,
                'timestamp': datetime.utcnow().isoformat(),
                **kwargs
            }
        )
    
    def rotate_logs(self):
        """Force log rotation"""
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                handler.doRollover()
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Get logging statistics"""
        stats = {
            'log_dir': self.log_dir,
            'log_level': self.log_level.name,
            'handlers': []
        }
        
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            handler_info = {
                'type': handler.__class__.__name__,
                'level': logging.getLevelName(handler.level)
            }
            
            if hasattr(handler, 'baseFilename'):
                handler_info['file'] = handler.baseFilename
                if os.path.exists(handler.baseFilename):
                    handler_info['size'] = os.path.getsize(handler.baseFilename)
            
            stats['handlers'].append(handler_info)
        
        # Get log file sizes
        log_files = {}
        for filename in os.listdir(self.log_dir):
            if filename.endswith('.log'):
                filepath = os.path.join(self.log_dir, filename)
                log_files[filename] = os.path.getsize(filepath)
        
        stats['log_files'] = log_files
        stats['total_size'] = sum(log_files.values())
        
        return stats