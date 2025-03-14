"""
Utility functions for the MCP server.
"""
from typing import Any, Dict, List, Optional, Union
import json
import os
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp-server-salesforce")


def setup_logger(level: str = "INFO") -> logging.Logger:
    """
    Set up and configure logger.
    
    Args:
        level: Logging level (INFO, DEBUG, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    return logger


def get_env_var(name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get an environment variable with fallback to default.
    
    Args:
        name: Environment variable name
        default: Default value if not found
        
    Returns:
        Value of environment variable or default
    """
    return os.environ.get(name, default)


def format_json(data: Any) -> str:
    """
    Format data as pretty JSON.
    
    Args:
        data: Data to format
        
    Returns:
        Formatted JSON string
    """
    return json.dumps(data, indent=2, sort_keys=True)


def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path to project root
    """
    return Path(__file__).parent.parent.parent.absolute()


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validate that all required fields are present in data.
    
    Args:
        data: Data dictionary to check
        required_fields: List of required field names
        
    Raises:
        ValueError: If any required fields are missing
    """
    missing = [field for field in required_fields if field not in data or data[field] is None]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")