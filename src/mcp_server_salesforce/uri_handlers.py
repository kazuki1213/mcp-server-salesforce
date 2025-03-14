"""
URI handlers for different resource types.
"""
import json
from typing import Dict, List, Optional, Any, Tuple, Union
from pydantic import AnyUrl

from .salesforce_client import SalesforceClient, SalesforceError

class UriParseError(Exception):
    """Exception raised when a URI cannot be parsed correctly."""
    pass

class ResourceNotFoundError(Exception):
    """Exception raised when a requested resource is not found."""
    pass

def parse_uri(uri: AnyUrl) -> Tuple[str, List[str]]:
    """
    Parse a URI into scheme and path components.
    
    Args:
        uri: URI to parse
        
    Returns:
        Tuple of (scheme, path_parts)
        
    Raises:
        UriParseError: If URI cannot be parsed correctly
    """
    scheme = uri.scheme
    
    if not scheme:
        raise UriParseError("Missing URI scheme")
    
    path = uri.path or ""
    path_parts = [p for p in path.lstrip('/').split('/') if p]
    
    return scheme, path_parts

def handle_note_uri(uri: AnyUrl, notes: Dict[str, str]) -> str:
    """
    Handle a note:// URI.
    
    Args:
        uri: The note URI
        notes: Dictionary of notes
        
    Returns:
        Note content
        
    Raises:
        ResourceNotFoundError: If note not found
    """
    _, path_parts = parse_uri(uri)
    
    if not path_parts:
        raise ResourceNotFoundError("No note name specified in URI")
    
    note_name = path_parts[0]
    if note_name not in notes:
        raise ResourceNotFoundError(f"Note not found: {note_name}")
    
    return notes[note_name]

def handle_salesforce_uri(uri: AnyUrl, sf_client: SalesforceClient) -> str:
    """
    Handle a salesforce:// URI.
    
    Args:
        uri: The Salesforce URI
        sf_client: Salesforce client instance
        
    Returns:
        JSON string with resource content
        
    Raises:
        UriParseError: If URI format is invalid
        ResourceNotFoundError: If resource not found
        SalesforceError: If Salesforce operation fails
    """
    _, path_parts = parse_uri(uri)
    
    if not path_parts:
        raise UriParseError("Invalid Salesforce URI format")
    
    resource_type = path_parts[0]
    
    if resource_type == "object":
        if len(path_parts) == 1:
            # Request is for object metadata
            raise UriParseError("Missing object name in URI")
            
        elif len(path_parts) == 2:
            # Request is for object metadata
            object_name = path_parts[1]
            metadata = sf_client.describe_object(object_name)
            return json.dumps(metadata, indent=2)
            
        elif len(path_parts) == 3:
            # Request is for specific record
            object_name = path_parts[1]
            record_id = path_parts[2]
            record = sf_client.get_record(object_name, record_id)
            return json.dumps(record, indent=2)
    
    raise UriParseError(f"Unsupported Salesforce resource type: {resource_type}")

def read_resource(uri: AnyUrl, notes: Dict[str, str], sf_client: Optional[SalesforceClient] = None) -> str:
    """
    Read a resource by URI.
    
    Args:
        uri: Resource URI
        notes: Dictionary of notes
        sf_client: Optional Salesforce client
        
    Returns:
        Resource content
        
    Raises:
        UriParseError: If URI format is invalid
        ResourceNotFoundError: If resource not found
        ValueError: If scheme is not supported or required client is missing
    """
    scheme = uri.scheme
    
    if scheme == "note":
        return handle_note_uri(uri, notes)
        
    elif scheme == "salesforce":
        if sf_client is None:
            raise ValueError("Salesforce client not provided for salesforce:// URI")
        return handle_salesforce_uri(uri, sf_client)
    
    raise ValueError(f"Unsupported URI scheme: {scheme}")