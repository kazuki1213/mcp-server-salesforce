"""
Data models for the MCP server.
"""
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, validator


class SalesforceRecord(BaseModel):
    """A Salesforce record model."""
    id: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
    fields: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        extra = "allow"


class SalesforceObject(BaseModel):
    """A Salesforce object metadata model."""
    name: str
    label: str
    fields: List[Dict[str, Any]] = Field(default_factory=list)
    custom: bool = False
    description: Optional[str] = None
    
    class Config:
        extra = "allow"


class SalesforceQueryResult(BaseModel):
    """A result from a Salesforce SOQL query."""
    totalSize: int
    done: bool
    records: List[Dict[str, Any]] = Field(default_factory=list)
    
    @validator('records', pre=True)
    def parse_records(cls, v):
        if isinstance(v, list):
            return v
        return []


class Note(BaseModel):
    """A note stored in the server."""
    name: str
    content: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class ToolResult:
    """Result from executing a tool."""
    success: bool
    message: str
    data: Any = None


@dataclass
class ResourceInfo:
    """Information about a resource."""
    uri: str
    name: str
    description: str
    mime_type: str