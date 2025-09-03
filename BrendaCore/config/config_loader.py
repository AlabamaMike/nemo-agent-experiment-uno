"""
Configuration Loader for BrendaCore
"""

import os
import yaml
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import re

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Loads and manages configuration for BrendaCore
    
    Features:
    - Environment variable substitution
    - Multi-environment support
    - Config validation
    - Default value handling
    """
    
    def __init__(self, config_dir: Optional[str] = None, environment: Optional[str] = None):
        """
        Initialize configuration loader
        
        Args:
            config_dir: Directory containing config files
            environment: Environment name (development/staging/production)
        """
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent
        self.environment = environment or os.getenv('BRENDA_ENV', 'development')
        self.config_cache: Dict[str, Any] = {}
        
        logger.info("ConfigLoader initialized for environment: %s", self.environment)
    
    def load_config(self, config_name: str = 'cartesia_config') -> Dict[str, Any]:
        """
        Load configuration file
        
        Args:
            config_name: Name of config file (without extension)
            
        Returns:
            Loaded and processed configuration
        """
        if config_name in self.config_cache:
            return self.config_cache[config_name]
        
        config_path = self._find_config_file(config_name)
        
        if not config_path:
            logger.warning("Config file not found: %s", config_name)
            return {}
        
        try:
            with open(config_path, 'r') as f:
                if config_path.suffix == '.yaml' or config_path.suffix == '.yml':
                    config = yaml.safe_load(f)
                elif config_path.suffix == '.json':
                    config = json.load(f)
                else:
                    raise ValueError(f"Unsupported config format: {config_path.suffix}")
            
            config = self._substitute_env_vars(config)
            
            config = self._apply_environment_overrides(config)
            
            config = self._apply_defaults(config)
            
            self.config_cache[config_name] = config
            
            logger.info("Loaded configuration: %s", config_name)
            return config
            
        except Exception as e:
            logger.error("Error loading config %s: %s", config_name, e)
            return {}
    
    def _find_config_file(self, config_name: str) -> Optional[Path]:
        """Find configuration file"""
        extensions = ['.yaml', '.yml', '.json']
        
        for ext in extensions:
            config_path = self.config_dir / f"{config_name}{ext}"
            if config_path.exists():
                return config_path
        
        env_specific = self.config_dir / self.environment / f"{config_name}.yaml"
        if env_specific.exists():
            return env_specific
        
        return None
    
    def _substitute_env_vars(self, config: Any) -> Any:
        """
        Recursively substitute environment variables
        
        Supports:
        - ${VAR_NAME} - Required variable
        - ${VAR_NAME:default} - Variable with default value
        """
        if isinstance(config, dict):
            return {k: self._substitute_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str):
            pattern = r'\$\{([^}]+)\}'
            
            def replacer(match):
                var_expr = match.group(1)
                
                if ':' in var_expr:
                    var_name, default_value = var_expr.split(':', 1)
                    return os.getenv(var_name, default_value)
                else:
                    value = os.getenv(var_expr)
                    if value is None:
                        logger.warning("Missing environment variable: %s", var_expr)
                        return match.group(0)
                    return value
            
            return re.sub(pattern, replacer, config)
        else:
            return config
    
    def _apply_environment_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment-specific overrides"""
        if 'environments' not in config:
            return config
        
        env_config = config.get('environments', {}).get(self.environment, {})
        
        if env_config:
            config = self._deep_merge(config, env_config)
        
        config.pop('environments', None)
        
        return config
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values for missing configuration"""
        defaults = {
            'cartesia': {
                'api': {
                    'timeout': 30,
                    'max_retries': 3
                },
                'voice_settings': {
                    'base': {
                        'speed': 1.0,
                        'pitch': 1.0,
                        'volume': 1.0
                    }
                },
                'call_management': {
                    'inbound': {
                        'max_duration_minutes': 30
                    }
                }
            }
        }
        
        return self._deep_merge(defaults, config)
    
    def get_cartesia_config(self) -> Dict[str, Any]:
        """Get Cartesia-specific configuration"""
        config = self.load_config('cartesia_config')
        return config.get('cartesia', {})
    
    def get_voice_settings(self) -> Dict[str, Any]:
        """Get voice settings"""
        cartesia_config = self.get_cartesia_config()
        return cartesia_config.get('voice_settings', {})
    
    def get_webhook_config(self) -> Dict[str, Any]:
        """Get webhook configuration"""
        cartesia_config = self.get_cartesia_config()
        line_agent = cartesia_config.get('line_agent', {})
        return line_agent.get('webhook', {})
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            'cartesia.api.api_key',
            'cartesia.line_agent.agent_name',
            'cartesia.line_agent.webhook.endpoint'
        ]
        
        for field_path in required_fields:
            if not self._get_nested_value(config, field_path):
                logger.error("Missing required config field: %s", field_path)
                return False
        
        return True
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested dictionary value using dot notation"""
        keys = path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def save_config(self, config: Dict[str, Any], config_name: str):
        """
        Save configuration to file
        
        Args:
            config: Configuration to save
            config_name: Name for config file
        """
        config_path = self.config_dir / f"{config_name}.yaml"
        
        try:
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
            logger.info("Saved configuration to %s", config_path)
            
        except Exception as e:
            logger.error("Error saving config: %s", e)


def load_config(config_name: str = 'cartesia_config', 
               environment: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to load configuration
    
    Args:
        config_name: Name of config file
        environment: Environment name
        
    Returns:
        Loaded configuration
    """
    loader = ConfigLoader(environment=environment)
    return loader.load_config(config_name)