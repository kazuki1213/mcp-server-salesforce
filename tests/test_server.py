"""
Tests for the MCP server module.
"""
import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pydantic import AnyUrl

from mcp_server_salesforce.server import (
    create_resource,
    format_response,
    handle_add_note,
    handle_salesforce_query,
    handle_salesforce_create,
    handle_salesforce_update,
    handle_salesforce_delete,
)
from mcp_server_salesforce.salesforce_client import SalesforceError


class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_create_resource(self):
        """Test creating a resource."""
        resource = create_resource(
            uri="note://internal/test",
            name="Test Note",
            description="A test note",
            mime_type="text/plain"
        )
        
        assert resource.uri == AnyUrl("note://internal/test")
        assert resource.name == "Test Note"
        assert resource.description == "A test note"
        assert resource.mimeType == "text/plain"
    
    def test_format_response_simple(self):
        """Test formatting a simple response."""
        response = format_response(
            success=True,
            message="Operation successful"
        )
        
        assert len(response) == 1
        assert response[0].type == "text"
        assert response[0].text == "Operation successful"
    
    def test_format_response_with_data(self):
        """Test formatting a response with data."""
        data = {"id": "12345", "name": "Test"}
        response = format_response(
            success=True,
            message="Operation successful",
            data=data
        )
        
        assert len(response) == 1
        assert response[0].type == "text"
        assert response[0].text.startswith("Operation successful")
        assert json.dumps(data, indent=2) in response[0].text


class TestHandlers:
    """Tests for handler functions."""
    
    @patch('mcp_server_salesforce.server.state')
    @patch('mcp_server_salesforce.server.server')
    async def test_handle_add_note(self, mock_server, mock_state):
        """Test handling add-note tool call."""
        # Setup mocks
        mock_state.add_note = MagicMock()
        mock_server.request_context.session.send_resource_list_changed = AsyncMock()
        
        # Call handler
        result = await handle_add_note({
            "name": "test-note",
            "content": "Test content"
        })
        
        # Verify results
        mock_state.add_note.assert_called_once_with("test-note", "Test content")
        mock_server.request_context.session.send_resource_list_changed.assert_awaited_once()
        assert len(result) == 1
        assert "Added note 'test-note'" in result[0].text
    
    @patch('mcp_server_salesforce.server.state')
    async def test_handle_add_note_missing_args(self, mock_state):
        """Test handling add-note tool call with missing arguments."""
        with pytest.raises(ValueError, match="Missing name or content"):
            await handle_add_note({})
    
    @patch('mcp_server_salesforce.server.state')
    async def test_handle_salesforce_query_success(self, mock_state):
        """Test handling salesforce-query tool call successfully."""
        # Setup mocks
        mock_sf = MagicMock()
        mock_sf.query.return_value = [{"Id": "1", "Name": "Test"}]
        mock_state.get_salesforce_client.return_value = mock_sf
        
        # Call handler
        result = await handle_salesforce_query({
            "query": "SELECT Id FROM Account"
        })
        
        # Verify results
        mock_sf.query.assert_called_once_with("SELECT Id FROM Account")
        assert len(result) == 1
        assert "Query executed successfully" in result[0].text
        assert json.dumps([{"Id": "1", "Name": "Test"}], indent=2) in result[0].text
    
    @patch('mcp_server_salesforce.server.state')
    async def test_handle_salesforce_query_error(self, mock_state):
        """Test handling salesforce-query tool call with error."""
        # Setup mocks
        mock_sf = MagicMock()
        mock_sf.query.side_effect = SalesforceError("Query failed")
        mock_state.get_salesforce_client.return_value = mock_sf
        
        # Call handler
        result = await handle_salesforce_query({
            "query": "SELECT Id FROM Account"
        })
        
        # Verify results
        assert len(result) == 1
        assert "Error executing query" in result[0].text
    
    @patch('mcp_server_salesforce.server.state')
    async def test_handle_salesforce_query_missing_args(self, mock_state):
        """Test handling salesforce-query tool call with missing arguments."""
        with pytest.raises(ValueError, match="Missing query"):
            await handle_salesforce_query({})
    
    @patch('mcp_server_salesforce.server.state')
    @patch('mcp_server_salesforce.server.server')
    async def test_handle_salesforce_create_success(self, mock_server, mock_state):
        """Test handling salesforce-create tool call successfully."""
        # Setup mocks
        mock_sf = MagicMock()
        mock_sf.create_record.return_value = "12345"
        mock_state.get_salesforce_client.return_value = mock_sf
        mock_server.request_context.session.send_resource_list_changed = AsyncMock()
        
        # Call handler
        result = await handle_salesforce_create({
            "object": "Account",
            "data": {"Name": "Test Account"}
        })
        
        # Verify results
        mock_sf.create_record.assert_called_once_with("Account", {"Name": "Test Account"})
        mock_server.request_context.session.send_resource_list_changed.assert_awaited_once()
        assert len(result) == 1
        assert "Created Account record with ID: 12345" in result[0].text
    
    @patch('mcp_server_salesforce.server.state')
    async def test_handle_salesforce_create_error(self, mock_state):
        """Test handling salesforce-create tool call with error."""
        # Setup mocks
        mock_sf = MagicMock()
        mock_sf.create_record.side_effect = SalesforceError("Create failed")
        mock_state.get_salesforce_client.return_value = mock_sf
        
        # Call handler
        result = await handle_salesforce_create({
            "object": "Account",
            "data": {"Name": "Test Account"}
        })
        
        # Verify results
        assert len(result) == 1
        assert "Error creating record" in result[0].text
    
    @patch('mcp_server_salesforce.server.state')
    async def test_handle_salesforce_create_missing_args(self, mock_state):
        """Test handling salesforce-create tool call with missing arguments."""
        with pytest.raises(ValueError, match="Missing object name or data"):
            await handle_salesforce_create({})
    
    @patch('mcp_server_salesforce.server.state')
    async def test_handle_salesforce_update_success(self, mock_state):
        """Test handling salesforce-update tool call successfully."""
        # Setup mocks
        mock_sf = MagicMock()
        mock_state.get_salesforce_client.return_value = mock_sf
        
        # Call handler
        result = await handle_salesforce_update({
            "object": "Account",
            "id": "12345",
            "data": {"Name": "Updated Name"}
        })
        
        # Verify results
        mock_sf.update_record.assert_called_once_with("Account", "12345", {"Name": "Updated Name"})
        assert len(result) == 1
        assert "Updated Account record with ID: 12345" in result[0].text
    
    @patch('mcp_server_salesforce.server.state')
    async def test_handle_salesforce_update_error(self, mock_state):
        """Test handling salesforce-update tool call with error."""
        # Setup mocks
        mock_sf = MagicMock()
        mock_sf.update_record.side_effect = SalesforceError("Update failed")
        mock_state.get_salesforce_client.return_value = mock_sf
        
        # Call handler
        result = await handle_salesforce_update({
            "object": "Account",
            "id": "12345",
            "data": {"Name": "Updated Name"}
        })
        
        # Verify results
        assert len(result) == 1
        assert "Error updating record" in result[0].text
    
    @patch('mcp_server_salesforce.server.state')
    async def test_handle_salesforce_update_missing_args(self, mock_state):
        """Test handling salesforce-update tool call with missing arguments."""
        with pytest.raises(ValueError, match="Missing object name, record ID, or data"):
            await handle_salesforce_update({})
    
    @patch('mcp_server_salesforce.server.state')
    @patch('mcp_server_salesforce.server.server')
    async def test_handle_salesforce_delete_success(self, mock_server, mock_state):
        """Test handling salesforce-delete tool call successfully."""
        # Setup mocks
        mock_sf = MagicMock()
        mock_state.get_salesforce_client.return_value = mock_sf
        mock_server.request_context.session.send_resource_list_changed = AsyncMock()
        
        # Call handler
        result = await handle_salesforce_delete({
            "object": "Account",
            "id": "12345"
        })
        
        # Verify results
        mock_sf.delete_record.assert_called_once_with("Account", "12345")
        mock_server.request_context.session.send_resource_list_changed.assert_awaited_once()
        assert len(result) == 1
        assert "Deleted Account record with ID: 12345" in result[0].text
    
    @patch('mcp_server_salesforce.server.state')
    async def test_handle_salesforce_delete_error(self, mock_state):
        """Test handling salesforce-delete tool call with error."""
        # Setup mocks
        mock_sf = MagicMock()
        mock_sf.delete_record.side_effect = SalesforceError("Delete failed")
        mock_state.get_salesforce_client.return_value = mock_sf
        
        # Call handler
        result = await handle_salesforce_delete({
            "object": "Account",
            "id": "12345"
        })
        
        # Verify results
        assert len(result) == 1
        assert "Error deleting record" in result[0].text
    
    @patch('mcp_server_salesforce.server.state')
    async def test_handle_salesforce_delete_missing_args(self, mock_state):
        """Test handling salesforce-delete tool call with missing arguments."""
        with pytest.raises(ValueError, match="Missing object name or record ID"):
            await handle_salesforce_delete({})