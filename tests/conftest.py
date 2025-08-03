#!/usr/bin/env python3
"""
File: conftest.py
Author: Claude Code Assistant
Created: 2025-08-03
Description: PyTest configuration and fixtures for tests

This file is part of the klaude project.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
import json


@pytest.fixture(autouse=True)
def mock_websearch_api():
    """
    Mock the Google Serper API calls for WebSearchTool tests.
    This fixture is automatically applied to all tests to prevent external API calls.
    """
    def mock_post(url, headers=None, data=None):
        """Mock response for Google Serper API"""
        if url == 'https://google.serper.dev/search':
            mock_response = Mock()
            mock_response.status_code = 200
            
            # Parse the query from the request data
            request_data = json.loads(data) if isinstance(data, str) else data
            query = request_data.get('q', '')
            
            # Return simulated search results based on query
            if "Python import best practices" in query:
                mock_response.json.return_value = {
                    "organic": [
                        {
                            "title": "Example Result 1",
                            "link": "https://example.com/result1",
                            "snippet": "This is a sample search result for Python import best practices"
                        },
                        {
                            "title": "Example Result 2",
                            "link": "https://example.com/result2",
                            "snippet": "Another sample result about Python imports"
                        }
                    ]
                }
            elif "Python programming" in query:
                mock_response.json.return_value = {
                    "organic": [
                        {
                            "title": "Example Result 1",
                            "link": "https://example.com/result1",
                            "snippet": "Learn Python programming from scratch"
                        },
                        {
                            "title": "Example Result 2",
                            "link": "https://example.com/result2",
                            "snippet": "Advanced Python programming techniques"
                        }
                    ]
                }
            elif len(query) < 2:
                # For short queries, return error
                mock_response.status_code = 400
                mock_response.text = "Query too short"
            else:
                # Default response for any other query
                mock_response.json.return_value = {
                    "organic": [
                        {
                            "title": f"Result for {query}",
                            "link": f"https://example.com/{query.replace(' ', '-').lower()}",
                            "snippet": f"Sample result for query: {query}"
                        }
                    ]
                }
            
            return mock_response
        
        # If not the expected URL, return a failed response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        return mock_response
    
    # Apply the mock to requests.post
    with patch('requests.post', side_effect=mock_post):
        # Also mock the GOOGLE_SEARCH_KEY environment variable
        with patch.dict('os.environ', {'GOOGLE_SEARCH_KEY': 'test-key'}):
            yield


@pytest.fixture(autouse=True)
def mock_webfetch_requests():
    """
    Mock HTTP requests for WebFetchTool tests.
    This fixture prevents all external HTTP requests during tests.
    """
    def mock_get(url, headers=None, timeout=None, allow_redirects=True):
        """Mock response for HTTP GET requests"""
        mock_response = Mock()
        mock_response.history = []  # No redirects by default
        
        # Parse URL to check for specific test cases
        if 'example.com' in url:
            mock_response.status_code = 200
            mock_response.headers = {'Content-Type': 'text/html'}
            mock_response.text = '<html><body><h1>Example Domain</h1><p>This domain is for use in illustrative examples in documents.</p></body></html>'
            mock_response.url = url
        elif 'httpstat.us/200?sleep=60000' in url:
            # Simulate timeout
            import requests
            raise requests.exceptions.Timeout('Request timed out')
        elif 'bit.ly' in url:
            # Simulate redirect
            mock_response.status_code = 200
            mock_response.headers = {'Content-Type': 'text/html'}
            mock_response.text = '<html><body>Redirected content</body></html>'
            mock_response.url = 'https://example.com/redirected'
            # Add redirect history
            redirect_resp = Mock()
            redirect_resp.status_code = 301
            redirect_resp.url = url
            mock_response.history = [redirect_resp]
        elif url == 'not-a-valid-url':
            # Invalid URL
            import requests
            raise requests.exceptions.InvalidURL('Invalid URL')
        elif '://' not in url or url.startswith('://'):
            # Malformed URL
            import requests
            raise requests.exceptions.InvalidURL('Invalid URL format')
        else:
            # Default response
            mock_response.status_code = 200
            mock_response.headers = {'Content-Type': 'text/html'}
            mock_response.text = f'<html><body><p>Mock content for {url}</p></body></html>'
            mock_response.url = url
        
        mock_response.raise_for_status = Mock()
        return mock_response
    
    # Apply the mock to requests.get
    with patch('requests.get', side_effect=mock_get):
        yield


@pytest.fixture(autouse=True)
def mock_task_tool_llm():
    """
    Mock LLM calls for TaskTool tests.
    This ensures TaskTool doesn't make external API calls during tests.
    """
    # Mock the OpenAI API key check to simulate test environment
    with patch.dict('os.environ', {'OPENAI_API_KEY': ''}):
        yield