"""
MCP Server for Salesforce - A Model Context Protocol server for Salesforce integration.

This package provides a server implementation for the Model Context Protocol
that allows interaction with Salesforce through the MCP interface.
"""

import asyncio
from importlib.metadata import version, PackageNotFoundError

# Import main modules
from . import server
from . import salesforce_client
from . import state
from . import uri_handlers

# Define package metadata
try:
    __version__ = version("mcp-server-salesforce")
except PackageNotFoundError:
    __version__ = "unknown"

__author__ = "kznkzn"


def main():
    """Main entry point for the package."""
    asyncio.run(server.main())


# Define public API
__all__ = [
    'main',
    'server',
    'salesforce_client',
    'state',
    'uri_handlers',
    '__version__',
]