#!/usr/bin/env python3
"""
File: conftest.py
Author: Claude Code Assistant
Created: 2025-08-03
Description: PyTest configuration and fixtures for tests

This file is part of the klaude project.
"""

import pytest
from unittest.mock import patch, Mock
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