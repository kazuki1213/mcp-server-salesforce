"""
Salesforce client module for interacting with Salesforce REST API.
"""
import os
import json
import functools
from typing import Dict, List, Any, Optional, Union, Callable, TypeVar, cast
from simple_salesforce import Salesforce
from dotenv import load_dotenv

# Custom exception types for better error handling
class SalesforceError(Exception):
    """Base exception for all Salesforce-related errors."""
    pass

class SalesforceAuthError(SalesforceError):
    """Exception raised for authentication/authorization errors."""
    pass

class SalesforceQueryError(SalesforceError):
    """Exception raised for errors during SOQL query execution."""
    pass

class SalesforceDataError(SalesforceError):
    """Exception raised for errors during data operations (create/update/delete)."""
    pass

# Type variables for decorator
T = TypeVar('T')
R = TypeVar('R')

def salesforce_error_handler(operation_name: str) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """
    Decorator for handling Salesforce operation errors consistently.
    
    Args:
        operation_name: Name of the operation (for error messages)
        
    Returns:
        Decorated function with consistent error handling
    """
    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> R:
            try:
                return func(*args, **kwargs)
            except SalesforceError:
                # Re-raise existing SalesforceError exceptions
                raise
            except Exception as e:
                # Map raw exceptions to appropriate SalesforceError types
                if 'authentication' in str(e).lower() or 'login' in str(e).lower():
                    raise SalesforceAuthError(f"Authentication error during {operation_name}: {str(e)}")
                elif 'query' in operation_name.lower():
                    raise SalesforceQueryError(f"Error during {operation_name}: {str(e)}")
                else:
                    raise SalesforceDataError(f"Error during {operation_name}: {str(e)}")
        return wrapper
    return decorator

class SalesforceClient:
    """Client for Salesforce REST API interactions."""
    
    def __init__(self, username: Optional[str] = None, 
                 password: Optional[str] = None, 
                 security_token: Optional[str] = None,
                 domain: Optional[str] = None):
        """
        Initialize Salesforce client with credentials.
        If credentials not provided, will attempt to load from environment variables.
        
        Raises:
            SalesforceAuthError: If credentials are missing or authentication fails
        """
        load_dotenv()  # Load environment variables from .env file if exists
        
        self.username = username or os.getenv('SALESFORCE_USERNAME')
        self.password = password or os.getenv('SALESFORCE_PASSWORD')
        self.security_token = security_token or os.getenv('SALESFORCE_SECURITY_TOKEN')
        self.domain = domain or os.getenv('SALESFORCE_DOMAIN', 'login')
        
        if not all([self.username, self.password, self.security_token]):
            raise SalesforceAuthError(
                "Missing required Salesforce credentials. "
                "Provide credentials directly or set environment variables: "
                "SALESFORCE_USERNAME, SALESFORCE_PASSWORD, SALESFORCE_SECURITY_TOKEN"
            )
        
        try:
            self.client = Salesforce(
                username=self.username,
                password=self.password,
                security_token=self.security_token,
                domain=self.domain
            )
        except Exception as e:
            raise SalesforceAuthError(f"Failed to authenticate with Salesforce: {str(e)}")
    
    def _get_sobject(self, object_name: str) -> Any:
        """
        Get Salesforce object by name.
        
        Args:
            object_name: The Salesforce object type (e.g., 'Account', 'Contact')
            
        Returns:
            Salesforce object instance
            
        Raises:
            SalesforceError: If the object doesn't exist
        """
        try:
            return getattr(self.client, object_name)
        except AttributeError:
            raise SalesforceError(f"Salesforce object '{object_name}' not found")
    
    @salesforce_error_handler("SOQL query")
    def query(self, soql_query: str) -> List[Dict[str, Any]]:
        """
        Execute a SOQL query and return results.
        
        Args:
            soql_query: A valid SOQL query string
            
        Returns:
            List of records as dictionaries
            
        Raises:
            SalesforceQueryError: If query execution fails
        """
        results = self.client.query(soql_query)
        return results.get('records', [])
    
    @salesforce_error_handler("record creation")
    def create_record(self, object_name: str, data: Dict[str, Any]) -> str:
        """
        Create a new record in Salesforce.
        
        Args:
            object_name: The Salesforce object type (e.g., 'Account', 'Contact')
            data: Dictionary of field names and values
            
        Returns:
            The ID of the created record
            
        Raises:
            SalesforceDataError: If record creation fails
        """
        sf_object = self._get_sobject(object_name)
        result = sf_object.create(data)
        
        if result.get('success'):
            return cast(str, result.get('id'))
        else:
            errors = result.get('errors', [])
            error_msg = '; '.join([str(err) for err in errors]) if errors else 'Unknown error'
            raise SalesforceDataError(f"Failed to create {object_name}: {error_msg}")
    
    @salesforce_error_handler("record update")
    def update_record(self, object_name: str, record_id: str, data: Dict[str, Any]) -> None:
        """
        Update an existing record in Salesforce.
        
        Args:
            object_name: The Salesforce object type (e.g., 'Account', 'Contact')
            record_id: The ID of the record to update
            data: Dictionary of field names and values to update
            
        Raises:
            SalesforceDataError: If record update fails
        """
        sf_object = self._get_sobject(object_name)
        sf_object.update(record_id, data)
    
    @salesforce_error_handler("record deletion")
    def delete_record(self, object_name: str, record_id: str) -> None:
        """
        Delete a record from Salesforce.
        
        Args:
            object_name: The Salesforce object type (e.g., 'Account', 'Contact')
            record_id: The ID of the record to delete
            
        Raises:
            SalesforceDataError: If record deletion fails
        """
        sf_object = self._get_sobject(object_name)
        sf_object.delete(record_id)
    
    def get_record_with_fields(self, object_name: str, record_id: str, fields: List[str]) -> Dict[str, Any]:
        """
        Get a record with specific fields from Salesforce by ID using SOQL.
        
        Args:
            object_name: The Salesforce object type (e.g., 'Account', 'Contact')
            record_id: The ID of the record to retrieve
            fields: List of fields to retrieve
            
        Returns:
            Record as dictionary with specified fields
            
        Raises:
            SalesforceQueryError: If query execution fails
        """
        field_str = ', '.join(fields)
        query = f"SELECT {field_str} FROM {object_name} WHERE Id = '{record_id}'"
        results = self.query(query)
        
        if results:
            return results[0]
        return {}
    
    @salesforce_error_handler("record retrieval")
    def get_record(self, object_name: str, record_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get a record from Salesforce by ID.
        
        Args:
            object_name: The Salesforce object type (e.g., 'Account', 'Contact')
            record_id: The ID of the record to retrieve
            fields: Optional list of fields to retrieve. If None, gets all fields.
            
        Returns:
            Record as dictionary
            
        Raises:
            SalesforceDataError: If record retrieval fails
        """
        if fields:
            return self.get_record_with_fields(object_name, record_id, fields)
        
        sf_object = self._get_sobject(object_name)
        return sf_object.get(record_id)
    
    @salesforce_error_handler("object listing")
    def get_available_objects(self) -> List[str]:
        """
        Get a list of available Salesforce objects.
        
        Returns:
            List of object names
            
        Raises:
            SalesforceError: If object listing fails
        """
        describe = self.client.describe()
        return [obj['name'] for obj in describe.get('sobjects', [])]
    
    @salesforce_error_handler("object description")
    def describe_object(self, object_name: str) -> Dict[str, Any]:
        """
        Get metadata for a specific Salesforce object.
        
        Args:
            object_name: The Salesforce object type (e.g., 'Account', 'Contact')
            
        Returns:
            Object metadata as dictionary
            
        Raises:
            SalesforceError: If object description fails
        """
        sf_object = self._get_sobject(object_name)
        return sf_object.describe()