"""
Tests for the state management module.
"""
import pytest
from unittest.mock import patch, MagicMock

from mcp_server_salesforce.state import ServerState
from mcp_server_salesforce.salesforce_client import SalesforceClient, SalesforceAuthError


class TestServerState:
    """Tests for the ServerState class."""

    def test_init(self):
        """Test initialization."""
        state = ServerState()
        assert state.notes == {}
        assert state._sf_client is None
        assert state._sf_initialization_attempted is False

    def test_add_note(self):
        """Test adding a note."""
        state = ServerState()
        state.add_note("test", "Test content")
        assert state.notes == {"test": "Test content"}

    def test_get_note(self):
        """Test getting a note."""
        state = ServerState()
        state.add_note("test", "Test content")
        assert state.get_note("test") == "Test content"
        assert state.get_note("nonexistent") is None

    def test_list_notes(self):
        """Test listing notes."""
        state = ServerState()
        state.add_note("test1", "Test content 1")
        state.add_note("test2", "Test content 2")
        notes = state.list_notes()
        assert sorted(notes) == ["test1", "test2"]

    @patch("mcp_server_salesforce.state.SalesforceClient")
    def test_get_salesforce_client_success(self, mock_sf_client):
        """Test getting Salesforce client successfully."""
        mock_instance = MagicMock()
        mock_sf_client.return_value = mock_instance

        state = ServerState()
        client = state.get_salesforce_client()

        assert client is mock_instance
        assert state._sf_client is mock_instance
        assert state._sf_initialization_attempted is True
        mock_sf_client.assert_called_once()

    @patch("mcp_server_salesforce.state.SalesforceClient")
    def test_get_salesforce_client_cached(self, mock_sf_client):
        """Test getting cached Salesforce client."""
        mock_instance = MagicMock()
        mock_sf_client.return_value = mock_instance

        state = ServerState()
        client1 = state.get_salesforce_client()
        client2 = state.get_salesforce_client()

        assert client1 is client2
        mock_sf_client.assert_called_once()

    @patch("mcp_server_salesforce.state.SalesforceClient")
    def test_get_salesforce_client_force_new(self, mock_sf_client):
        """Test forcing a new Salesforce client."""
        mock_instance1 = MagicMock()
        mock_instance2 = MagicMock()
        mock_sf_client.side_effect = [mock_instance1, mock_instance2]

        state = ServerState()
        client1 = state.get_salesforce_client()
        client2 = state.get_salesforce_client(force_new=True)

        assert client1 is mock_instance1
        assert client2 is mock_instance2
        assert state._sf_client is mock_instance2
        assert mock_sf_client.call_count == 2

    @patch("mcp_server_salesforce.state.SalesforceClient")
    def test_get_salesforce_client_error(self, mock_sf_client):
        """Test error handling when getting Salesforce client."""
        mock_sf_client.side_effect = SalesforceAuthError("Auth failed")

        state = ServerState()
        
        with pytest.raises(SalesforceAuthError, match="Auth failed"):
            state.get_salesforce_client()
        
        assert state._sf_client is None
        assert state._sf_initialization_attempted is True
        
        # Try again, should raise error about previous failure
        with pytest.raises(SalesforceAuthError, match="previously failed"):
            state.get_salesforce_client()
            
        # Force new should try again
        mock_sf_client.side_effect = [SalesforceAuthError("Still failed")]
        with pytest.raises(SalesforceAuthError, match="Still failed"):
            state.get_salesforce_client(force_new=True)

    @patch("mcp_server_salesforce.state.SalesforceClient")
    def test_has_salesforce_client_true(self, mock_sf_client):
        """Test checking if Salesforce client exists when it does."""
        mock_instance = MagicMock()
        mock_sf_client.return_value = mock_instance

        state = ServerState()
        state._sf_client = mock_instance
        
        assert state.has_salesforce_client() is True
        mock_sf_client.assert_not_called()

    @patch("mcp_server_salesforce.state.SalesforceClient")
    def test_has_salesforce_client_init_success(self, mock_sf_client):
        """Test checking if Salesforce client exists when initialization succeeds."""
        mock_instance = MagicMock()
        mock_sf_client.return_value = mock_instance

        state = ServerState()
        
        assert state.has_salesforce_client() is True
        mock_sf_client.assert_called_once()
        assert state._sf_client is mock_instance

    @patch("mcp_server_salesforce.state.SalesforceClient")
    def test_has_salesforce_client_init_failure(self, mock_sf_client):
        """Test checking if Salesforce client exists when initialization fails."""
        mock_sf_client.side_effect = SalesforceAuthError("Auth failed")

        state = ServerState()
        
        assert state.has_salesforce_client() is False
        mock_sf_client.assert_called_once()
        assert state._sf_client is None
        assert state._sf_initialization_attempted is True

    @patch("mcp_server_salesforce.state.SalesforceClient")
    def test_has_salesforce_client_previous_failure(self, mock_sf_client):
        """Test checking if Salesforce client exists after previous failure."""
        state = ServerState()
        state._sf_initialization_attempted = True
        
        assert state.has_salesforce_client() is False
        mock_sf_client.assert_not_called()