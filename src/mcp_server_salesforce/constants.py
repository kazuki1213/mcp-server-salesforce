"""
Constants used throughout the MCP server.
"""

# Server information
SERVER_NAME = "mcp-server-salesforce"
SERVER_VERSION = "0.0.1"

# URI schemes
SCHEME_NOTE = "note"
SCHEME_SALESFORCE = "salesforce"

# MIME types
MIME_TYPE_TEXT = "text/plain"
MIME_TYPE_JSON = "application/json"

# Salesforce environment variables
ENV_SF_USERNAME = "SALESFORCE_USERNAME"
ENV_SF_PASSWORD = "SALESFORCE_PASSWORD"
ENV_SF_TOKEN = "SALESFORCE_SECURITY_TOKEN"
ENV_SF_DOMAIN = "SALESFORCE_DOMAIN"
DEFAULT_SF_DOMAIN = "login"

# Tool names
TOOL_ADD_NOTE = "add-note"
TOOL_SF_QUERY = "salesforce-query"
TOOL_SF_CREATE = "salesforce-create"
TOOL_SF_UPDATE = "salesforce-update"
TOOL_SF_DELETE = "salesforce-delete"

# Prompt names
PROMPT_SUMMARIZE_NOTES = "summarize-notes"
PROMPT_ANALYZE_SF_DATA = "analyze-salesforce-data"

# Default values
DEFAULT_QUERY_LIMIT = 10
DEFAULT_PROMPT_STYLE = "brief"