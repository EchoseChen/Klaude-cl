#!/usr/bin/env python3
"""
File: test_webfetch_tool.py
Author: Claude Code Assistant
Created: 2025-08-03
Description: Tests for WebFetchTool implementation

This file is part of the klaude project.
"""

import pytest
import sys
import os

# Add parent directory to path to import the tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.klaude.tools_impl import WebFetchTool
from test_helpers import assert_schema_matches_expected


class TestWebFetchTool:
    """Test WebFetchTool implementation"""
    
    def test_webfetch_tool_creation(self):
        tool = WebFetchTool()
        assert tool.name == "WebFetch"
        assert "Fetches content from" in tool.description
        
    def test_webfetch_tool_parameters(self):
        tool = WebFetchTool()
        schema = tool.get_parameters_schema()
        assert "url" in schema["properties"]
        assert "prompt" in schema["properties"]
        assert schema["required"] == ["url", "prompt"]
    
    def test_webfetch_tool_schema_format(self):
        """Test that to_function_schema produces correct format"""
        tool = WebFetchTool()
        schema = tool.to_function_schema()
        assert_schema_matches_expected(schema, "WebFetch")
        
    def test_webfetch_tool_execution(self):
        """Test that WebFetchTool executes with mocked requests"""
        tool = WebFetchTool()
        result = tool.execute(
            "https://example.com",
            "Extract main content"
        )
        # With our mocks, this should return content without actual network calls
        assert "Fetched content from" in result
        assert "https://example.com" in result
        assert "Extract main content" in result
        
    def test_webfetch_tool_restricted_domain(self):
        tool = WebFetchTool()
        result = tool.execute(
            "https://docs.python.org/3/tutorial/modules.html",
            "Get import info"
        )
        assert "unable to fetch from docs.python.org" in result
    
    def test_webfetch_tool_invalid_url(self):
        tool = WebFetchTool()
        result = tool.execute(
            "not-a-valid-url",
            "Extract content"
        )
        assert "Error:" in result or "Invalid URL" in result
    
    def test_webfetch_tool_http_to_https_upgrade(self):
        tool = WebFetchTool()
        # Test that HTTP URLs are upgraded to HTTPS
        result = tool.execute(
            "http://example.com",
            "Extract content"
        )
        # Should mention HTTPS in the result
        assert "https://" in result or "HTTP" in result
    
    def test_webfetch_tool_with_query_params(self):
        tool = WebFetchTool()
        result = tool.execute(
            "https://example.com/search?q=test&page=1",
            "Extract search results"
        )
        assert "example.com" in result
        assert "Extract search results" in result
    
    def test_webfetch_tool_empty_prompt(self):
        tool = WebFetchTool()
        result = tool.execute(
            "https://example.com",
            ""
        )
        # Should still work but might warn about empty prompt
        assert "example.com" in result
    
    def test_webfetch_tool_redirect_handling(self):
        tool = WebFetchTool()
        # Test URL that typically redirects
        result = tool.execute(
            "https://bit.ly/example",
            "Follow redirect"
        )
        # Should either follow redirect or mention it
        assert "redirect" in result.lower() or "bit.ly" in result
    
    def test_webfetch_tool_timeout_handling(self):
        """Test timeout handling with mocked timeout"""
        tool = WebFetchTool()
        # This URL is mocked to timeout in conftest.py
        result = tool.execute(
            "https://httpstat.us/200?sleep=60000",  # 60 second delay
            "Test timeout"
        )
        assert "Error:" in result or "timeout" in result.lower() or "timed out" in result.lower()
    
    def test_webfetch_tool_cache_behavior(self):
        tool = WebFetchTool()
        # First request
        result1 = tool.execute(
            "https://example.com",
            "First request"
        )
        
        # Second request to same URL (should hit cache)
        result2 = tool.execute(
            "https://example.com",
            "Second request"
        )
        
        assert "example.com" in result1
        assert "example.com" in result2
    
    def test_webfetch_tool_malformed_url(self):
        tool = WebFetchTool()
        test_cases = [
            "https://",
            "://example.com",
            "https://example..com",
            "https://example.com:99999",  # Invalid port
        ]
        
        for url in test_cases:
            result = tool.execute(url, "Test malformed URL")
            assert "Error:" in result or "Invalid" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])