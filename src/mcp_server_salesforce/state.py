"""
State management module for the MCP server.
"""
from typing import Dict, List, Any, Optional, cast
import json

from .salesforce_client import SalesforceClient, SalesforceAuthError

class ServerState:
    """
    Manages server state including notes and Salesforce client.
    """
    
    def __init__(self):
        """Initialize the server state."""
        self.notes: Dict[str, str] = {}
        self._sf_client: Optional[SalesforceClient] = None
        self._sf_initialization_attempted = False
    
    def add_note(self, name: str, content: str) -> None:
        """
        Add a note to the state.
        
        Args:
            name: Note name
            content: Note content
        """
        self.notes[name] = content
    
    def get_note(self, name: str) -> Optional[str]:
        """
        Get a note by name.
        
        Args:
            name: Note name
            
        Returns:
            Note content or None if not found
        """
        return self.notes.get(name)
    
    def list_notes(self) -> List[str]:
        """
        Get a list of all note names.
        
        Returns:
            List of note names
        """
        return list(self.notes.keys())
    
    def get_salesforce_client(self, force_new: bool = False) -> SalesforceClient:
        """
        Get the Salesforce client, initializing it if necessary.
        
        Args:
            force_new: If True, create a new client even if one exists
            
        Returns:
            Salesforce client
            
        Raises:
            SalesforceAuthError: If client initialization fails
        """
        if force_new or self._sf_client is None:
            if self._sf_initialization_attempted and not force_new:
                raise SalesforceAuthError(
                    "Salesforce client initialization previously failed. "
                    "Set force_new=True to retry."
                )
            
            try:
                self._sf_client = SalesforceClient()
                self._sf_initialization_attempted = True
            except SalesforceAuthError as e:
                self._sf_initialization_attempted = True
                raise e
        
        return cast(SalesforceClient, self._sf_client)
    
    def has_salesforce_client(self) -> bool:
        """
        Check if a valid Salesforce client exists.
        
        Returns:
            True if client exists, False otherwise
        """
        if not self._sf_client:
            # Try to initialize if we haven't tried before
            if not self._sf_initialization_attempted:
                try:
                    self.get_salesforce_client()
                    return True
                except SalesforceAuthError:
                    return False
            return False
        return True