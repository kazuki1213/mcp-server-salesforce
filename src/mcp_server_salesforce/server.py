"""
Main MCP server implementation for Salesforce integration.
"""
import asyncio
import os
import json
from typing import Dict, List, Any, Optional, Union, cast

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl, Field
import mcp.server.stdio

from .salesforce_client import SalesforceClient, SalesforceError, SalesforceAuthError
from .uri_handlers import read_resource, UriParseError, ResourceNotFoundError
from .state import ServerState

# Initialize server with state management
server = Server("mcp-server-salesforce")
state = ServerState()

def create_resource(uri: str, name: str, description: str, mime_type: str) -> types.Resource:
    """
    Create a resource object with consistent formatting.
    
    Args:
        uri: Resource URI
        name: Resource name/title
        description: Resource description
        mime_type: Resource MIME type
        
    Returns:
        Formatted Resource object
    """
    return types.Resource(
        uri=AnyUrl(uri),
        name=name,
        description=description,
        mimeType=mime_type,
    )

def format_response(success: bool, message: str, data: Optional[Any] = None) -> List[types.TextContent]:
    """
    Format a consistent response for tool calls.
    
    Args:
        success: Whether the operation succeeded
        message: Message to display
        data: Optional data to include (will be formatted as JSON)
        
    Returns:
        List with a single TextContent response
    """
    response_text = message
    
    if data:
        response_text += f"\n\n{json.dumps(data, indent=2)}"
        
    return [
        types.TextContent(
            type="text",
            text=response_text,
        )
    ]

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """
    List available resources - both notes and Salesforce objects.
    Each note is exposed as a resource with a custom note:// URI scheme.
    Salesforce objects are exposed with a salesforce:// URI scheme.
    """
    # Add notes resources
    resources = [
        create_resource(
            uri=f"note://internal/{name}",
            name=f"Note: {name}",
            description=f"A simple note named {name}",
            mime_type="text/plain"
        )
        for name in state.list_notes()
    ]
    
    # Try to add Salesforce objects if credentials are available
    if state.has_salesforce_client():
        try:
            sf = state.get_salesforce_client()
            for obj_name in sf.get_available_objects():
                resources.append(
                    create_resource(
                        uri=f"salesforce://object/{obj_name}",
                        name=f"Salesforce: {obj_name}",
                        description=f"Salesforce {obj_name} object",
                        mime_type="application/json"
                    )
                )
        except SalesforceError:
            # Skip Salesforce objects if operation fails
            pass
        
    return resources

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """
    Read a specific resource's content by its URI.
    Handles both note:// and salesforce:// schemes.
    """
    try:
        sf_client = state.get_salesforce_client() if state.has_salesforce_client() else None
        return read_resource(uri, state.notes, sf_client)
    except UriParseError as e:
        raise ValueError(f"Invalid URI format: {str(e)}")
    except ResourceNotFoundError as e:
        raise ValueError(f"Resource not found: {str(e)}")
    except SalesforceError as e:
        raise ValueError(f"Salesforce error: {str(e)}")

@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """
    List available prompts.
    Each prompt can have optional arguments to customize its behavior.
    """
    prompts = [
        types.Prompt(
            name="summarize-notes",
            description="Creates a summary of all notes",
            arguments=[
                types.PromptArgument(
                    name="style",
                    description="Style of the summary (brief/detailed)",
                    required=False,
                )
            ],
        )
    ]
    
    # Only add Salesforce prompts if client is available
    if state.has_salesforce_client():
        prompts.append(
            types.Prompt(
                name="analyze-salesforce-data",
                description="Analyzes data from a Salesforce object",
                arguments=[
                    types.PromptArgument(
                        name="object",
                        description="Salesforce object name (e.g., Account, Contact)",
                        required=True,
                    ),
                    types.PromptArgument(
                        name="limit",
                        description="Maximum number of records to analyze",
                        required=False,
                    )
                ],
            )
        )
    
    return prompts

@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:
    """
    Generate a prompt by combining arguments with server state.
    """
    arguments = arguments or {}
    
    if name == "summarize-notes":
        style = arguments.get("style", "brief")
        detail_prompt = " Give extensive details." if style == "detailed" else ""
        
        notes_content = "\n".join(
            f"- {name}: {content}"
            for name, content in state.notes.items()
        )
        
        if not notes_content:
            notes_content = "No notes available."

        return types.GetPromptResult(
            description="Summarize the current notes",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"Here are the current notes to summarize:{detail_prompt}\n\n{notes_content}",
                    ),
                )
            ],
        )
    
    elif name == "analyze-salesforce-data":
        object_name = arguments.get("object")
        if not object_name:
            raise ValueError("Missing required argument 'object'")
            
        limit = int(arguments.get("limit", "10"))
        
        try:
            sf = state.get_salesforce_client()
            query = f"SELECT * FROM {object_name} LIMIT {limit}"
            records = sf.query(query)
            
            return types.GetPromptResult(
                description=f"Analyze Salesforce {object_name} data",
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=f"Please analyze the following {object_name} data from Salesforce and provide insights:\n\n"
                                f"{json.dumps(records, indent=2)}"
                        ),
                    )
                ],
            )
        except SalesforceError as e:
            raise ValueError(f"Error retrieving Salesforce data: {str(e)}")
    
    else:
        raise ValueError(f"Unknown prompt: {name}")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    Each tool specifies its arguments using JSON Schema validation.
    """
    tools = [
        types.Tool(
            name="add-note",
            description="Add a new note",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["name", "content"],
            },
        )
    ]
    
    # Only add Salesforce tools if available
    if state.has_salesforce_client():
        sf_tools = [
            types.Tool(
                name="salesforce-query",
                description="Execute a SOQL query against Salesforce",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "SOQL query string"},
                    },
                    "required": ["query"],
                },
            ),
            types.Tool(
                name="salesforce-create",
                description="Create a new record in Salesforce",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "object": {"type": "string", "description": "Salesforce object type (e.g., Account)"},
                        "data": {"type": "object", "description": "Record data as key-value pairs"},
                    },
                    "required": ["object", "data"],
                },
            ),
            types.Tool(
                name="salesforce-update",
                description="Update an existing record in Salesforce",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "object": {"type": "string", "description": "Salesforce object type (e.g., Account)"},
                        "id": {"type": "string", "description": "Record ID to update"},
                        "data": {"type": "object", "description": "Record data as key-value pairs"},
                    },
                    "required": ["object", "id", "data"],
                },
            ),
            types.Tool(
                name="salesforce-delete",
                description="Delete a record from Salesforce",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "object": {"type": "string", "description": "Salesforce object type (e.g., Account)"},
                        "id": {"type": "string", "description": "Record ID to delete"},
                    },
                    "required": ["object", "id"],
                },
            ),
        ]
        tools.extend(sf_tools)
    
    return tools

async def handle_add_note(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """
    Handle the add-note tool call.
    
    Args:
        arguments: Tool arguments
        
    Returns:
        Response message
    """
    note_name = arguments.get("name")
    content = arguments.get("content")

    if not note_name or not content:
        raise ValueError("Missing name or content")

    # Update server state
    state.add_note(note_name, content)

    # Notify clients that resources have changed
    await server.request_context.session.send_resource_list_changed()

    return format_response(
        success=True,
        message=f"Added note '{note_name}' with content: {content}"
    )

async def handle_salesforce_query(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """
    Handle the salesforce-query tool call.
    
    Args:
        arguments: Tool arguments
        
    Returns:
        Response message with query results
    """
    query = arguments.get("query")
    if not query:
        raise ValueError("Missing query")
        
    try:
        sf = state.get_salesforce_client()
        results = sf.query(query)
        
        return format_response(
            success=True,
            message="Query executed successfully. Results:",
            data=results
        )
    except SalesforceError as e:
        return format_response(
            success=False,
            message=f"Error executing query: {str(e)}"
        )

async def handle_salesforce_create(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """
    Handle the salesforce-create tool call.
    
    Args:
        arguments: Tool arguments
        
    Returns:
        Response message with created record ID
    """
    object_name = arguments.get("object")
    data = arguments.get("data")
    
    if not object_name or not data:
        raise ValueError("Missing object name or data")
        
    try:
        sf = state.get_salesforce_client()
        record_id = sf.create_record(object_name, data)
        
        # Notify clients that resources have changed
        await server.request_context.session.send_resource_list_changed()
        
        return format_response(
            success=True,
            message=f"Created {object_name} record with ID: {record_id}"
        )
    except SalesforceError as e:
        return format_response(
            success=False,
            message=f"Error creating record: {str(e)}"
        )

async def handle_salesforce_update(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """
    Handle the salesforce-update tool call.
    
    Args:
        arguments: Tool arguments
        
    Returns:
        Response message
    """
    object_name = arguments.get("object")
    record_id = arguments.get("id")
    data = arguments.get("data")
    
    if not object_name or not record_id or not data:
        raise ValueError("Missing object name, record ID, or data")
        
    try:
        sf = state.get_salesforce_client()
        sf.update_record(object_name, record_id, data)
        
        return format_response(
            success=True,
            message=f"Updated {object_name} record with ID: {record_id}"
        )
    except SalesforceError as e:
        return format_response(
            success=False,
            message=f"Error updating record: {str(e)}"
        )

async def handle_salesforce_delete(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """
    Handle the salesforce-delete tool call.
    
    Args:
        arguments: Tool arguments
        
    Returns:
        Response message
    """
    object_name = arguments.get("object")
    record_id = arguments.get("id")
    
    if not object_name or not record_id:
        raise ValueError("Missing object name or record ID")
        
    try:
        sf = state.get_salesforce_client()
        sf.delete_record(object_name, record_id)
        
        # Notify clients that resources have changed
        await server.request_context.session.send_resource_list_changed()
        
        return format_response(
            success=True,
            message=f"Deleted {object_name} record with ID: {record_id}"
        )
    except SalesforceError as e:
        return format_response(
            success=False,
            message=f"Error deleting record: {str(e)}"
        )

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.
    Tools can modify server state and notify clients of changes.
    """
    if not arguments:
        raise ValueError("Missing arguments")

    # Map tool names to handler functions
    handlers = {
        "add-note": handle_add_note,
        "salesforce-query": handle_salesforce_query,
        "salesforce-create": handle_salesforce_create,
        "salesforce-update": handle_salesforce_update,
        "salesforce-delete": handle_salesforce_delete,
    }
    
    handler = handlers.get(name)
    if handler:
        return await handler(arguments)
    
    raise ValueError(f"Unknown tool: {name}")

async def main():
    """Main entry point for the MCP server."""
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-server-salesforce",
                server_version="0.0.1",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )