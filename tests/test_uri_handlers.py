"""
Tests for the URI handlers module.
"""
import json
import pytest
from unittest.mock import MagicMock, patch
from pydantic import AnyUrl

from mcp_server_salesforce.uri_handlers import (
    parse_uri,
    handle_note_uri,
    handle_salesforce_uri,
    read_resource,
    UriParseError,
    ResourceNotFoundError,
)


class TestUriParsing:
    """Tests for URI parsing functions."""

    def test_parse_uri_success(self):
        """Test successful URI parsing."""
        uri = AnyUrl("note://internal/test-note")
        scheme, path_parts = parse_uri(uri)
        
        assert scheme == "note"
        assert path_parts == ["test-note"]

    def test_parse_uri_no_scheme(self):
        """Test handling of URI without scheme."""
        uri = MagicMock()
        uri.scheme = None
        
        with pytest.raises(UriParseError, match="Missing URI scheme"):
            parse_uri(uri)

    def test_parse_uri_empty_path(self):
        """Test handling of URI with empty path."""
        uri = MagicMock()
        uri.scheme = "note"
        uri.path = ""
        
        scheme, path_parts = parse_uri(uri)
        assert scheme == "note"
        assert path_parts == []


class TestNoteUriHandler:
    """Tests for note URI handler functions."""

    def test_handle_note_uri_success(self):
        """Test successful note URI handling."""
        uri = MagicMock()
        uri.scheme = "note"
        uri.path = "/test-note"
        notes = {"test-note": "Note content"}
        
        result = handle_note_uri(uri, notes)
        assert result == "Note content"

    def test_handle_note_uri_empty_path(self):
        """Test handling note URI with empty path."""
        uri = MagicMock()
        uri.scheme = "note"
        uri.path = ""
        notes = {"test-note": "Note content"}
        
        with pytest.raises(ResourceNotFoundError, match="No note name specified"):
            handle_note_uri(uri, notes)

    def test_handle_note_uri_not_found(self):
        """Test handling note URI for non-existent note."""
        uri = MagicMock()
        uri.scheme = "note"
        uri.path = "/nonexistent"
        notes = {"test-note": "Note content"}
        
        with pytest.raises(ResourceNotFoundError, match="Note not found"):
            handle_note_uri(uri, notes)


class TestSalesforceUriHandler:
    """Tests for Salesforce URI handler functions."""

    def test_handle_salesforce_uri_empty_path(self):
        """Test handling Salesforce URI with empty path."""
        uri = MagicMock()
        uri.scheme = "salesforce"
        uri.path = ""
        client = MagicMock()
        
        with pytest.raises(UriParseError, match="Invalid Salesforce URI format"):
            handle_salesforce_uri(uri, client)

    def test_handle_salesforce_uri_invalid_resource_type(self):
        """Test handling Salesforce URI with invalid resource type."""
        uri = MagicMock()
        uri.scheme = "salesforce"
        uri.path = "/invalid"
        client = MagicMock()
        
        with pytest.raises(UriParseError, match="Unsupported Salesforce resource type"):
            handle_salesforce_uri(uri, client)

    def test_handle_salesforce_uri_object_missing_name(self):
        """Test handling Salesforce URI for object without name."""
        uri = MagicMock()
        uri.scheme = "salesforce"
        uri.path = "/object"
        client = MagicMock()
        
        with pytest.raises(UriParseError, match="Missing object name"):
            handle_salesforce_uri(uri, client)

    def test_handle_salesforce_uri_object_metadata(self):
        """Test handling Salesforce URI for object metadata."""
        uri = MagicMock()
        uri.scheme = "salesforce"
        uri.path = "/object/Account"
        
        client = MagicMock()
        metadata = {"name": "Account", "fields": []}
        client.describe_object.return_value = metadata
        
        result = handle_salesforce_uri(uri, client)
        expected = json.dumps(metadata, indent=2)
        
        assert result == expected
        client.describe_object.assert_called_once_with("Account")

    def test_handle_salesforce_uri_object_record(self):
        """Test handling Salesforce URI for object record."""
        uri = MagicMock()
        uri.scheme = "salesforce"
        uri.path = "/object/Account/12345"
        
        client = MagicMock()
        record = {"Id": "12345", "Name": "Test Account"}
        client.get_record.return_value = record
        
        result = handle_salesforce_uri(uri, client)
        expected = json.dumps(record, indent=2)
        
        assert result == expected
        client.get_record.assert_called_once_with("Account", "12345")


class TestReadResource:
    """Tests for the read_resource function."""

    def test_read_resource_note(self):
        """Test reading a note resource."""
        uri = MagicMock()
        uri.scheme = "note"
        uri.path = "/test-note"
        notes = {"test-note": "Note content"}
        
        result = read_resource(uri, notes)
        assert result == "Note content"

    def test_read_resource_salesforce_missing_client(self):
        """Test reading a Salesforce resource without client."""
        uri = MagicMock()
        uri.scheme = "salesforce"
        notes = {}
        
        with pytest.raises(ValueError, match="Salesforce client not provided"):
            read_resource(uri, notes)

    @patch("mcp_server_salesforce.uri_handlers.handle_salesforce_uri")
    def test_read_resource_salesforce(self, mock_handle_sf):
        """Test reading a Salesforce resource."""
        uri = MagicMock()
        uri.scheme = "salesforce"
        notes = {}
        client = MagicMock()
        mock_handle_sf.return_value = '{"test": "data"}'
        
        result = read_resource(uri, notes, client)
        assert result == '{"test": "data"}'
        mock_handle_sf.assert_called_once_with(uri, client)

    def test_read_resource_unsupported_scheme(self):
        """Test reading a resource with unsupported scheme."""
        uri = MagicMock()
        uri.scheme = "unsupported"
        notes = {}
        
        with pytest.raises(ValueError, match="Unsupported URI scheme"):
            read_resource(uri, notes)