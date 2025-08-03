#!/usr/bin/env python3
"""
File: test_websearch_tool.py
Author: Claude Code Assistant
Created: 2025-08-03
Description: Tests for WebSearchTool implementation

This file is part of the klaude project.
"""

import pytest
import sys
import os

# Add parent directory to path to import the tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.klaude.tools_impl import WebSearchTool


class TestWebSearchTool:
    """Test WebSearchTool implementation"""
    
    def test_websearch_tool_creation(self):
        tool = WebSearchTool()
        assert tool.name == "WebSearch"
        assert "search the web" in tool.description
        
    def test_websearch_tool_parameters(self):
        tool = WebSearchTool()
        schema = tool.get_parameters_schema()
        assert "query" in schema["properties"]
        assert "allowed_domains" in schema["properties"]
        assert "blocked_domains" in schema["properties"]
        assert schema["required"] == ["query"]
    
    def test_websearch_tool_schema_format(self):
        """Test that to_function_schema produces correct format"""
        tool = WebSearchTool()
        schema = tool.to_function_schema()
        
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "WebSearch"
        assert "search the web" in schema["function"]["description"]
        
        params = schema["function"]["parameters"]
        assert params["type"] == "object"
        assert params["required"] == ["query"]
        assert params["additionalProperties"] == False
        assert params["$schema"] == "http://json-schema.org/draft-07/schema#"
        
        props = params["properties"]
        assert props["query"]["type"] == "string"
        assert props["query"]["minLength"] == 2
        assert props["query"]["description"] == "The search query to use"
        
        assert props["allowed_domains"]["type"] == "array"
        assert props["allowed_domains"]["items"]["type"] == "string"
        assert props["allowed_domains"]["description"] == "Only include search results from these domains"
        
        assert props["blocked_domains"]["type"] == "array"
        assert props["blocked_domains"]["items"]["type"] == "string"
        assert props["blocked_domains"]["description"] == "Never include search results from these domains"
        
    def test_websearch_tool_execution(self):
        tool = WebSearchTool()
        result = tool.execute("Python import best practices")
        assert "Web search results for query" in result
        assert "Python import best practices" in result
        assert "Links:" in result
        assert "example.com" in result  # From simulated results
    
    def test_websearch_tool_with_allowed_domains(self):
        tool = WebSearchTool()
        result = tool.execute(
            "Python tutorials",
            allowed_domains=["python.org", "realpython.com"]
        )
        assert "Web search results for query" in result
        assert "Python tutorials" in result
        assert "allowed domains: python.org, realpython.com" in result
    
    def test_websearch_tool_with_blocked_domains(self):
        tool = WebSearchTool()
        result = tool.execute(
            "Programming examples",
            blocked_domains=["spam.com", "ads.com"]
        )
        assert "Web search results for query" in result
        assert "Programming examples" in result
        assert "blocked domains: spam.com, ads.com" in result
    
    def test_websearch_tool_with_both_filters(self):
        tool = WebSearchTool()
        result = tool.execute(
            "Data science",
            allowed_domains=["kaggle.com", "github.com"],
            blocked_domains=["spam.com"]
        )
        assert "Web search results for query" in result
        assert "Data science" in result
        assert "allowed domains:" in result
        assert "blocked domains:" in result
    
    def test_websearch_tool_empty_query(self):
        tool = WebSearchTool()
        # Query has minLength of 2
        result = tool.execute("")
        assert "Error:" in result or "query too short" in result.lower()
    
    def test_websearch_tool_short_query(self):
        tool = WebSearchTool()
        # Query has minLength of 2
        result = tool.execute("a")
        assert "Error:" in result or "query too short" in result.lower()
    
    def test_websearch_tool_valid_short_query(self):
        tool = WebSearchTool()
        # Exactly 2 characters (minimum)
        result = tool.execute("AI")
        assert "Web search results for query" in result
        assert "AI" in result
    
    def test_websearch_tool_special_characters_query(self):
        tool = WebSearchTool()
        result = tool.execute("C++ programming guide")
        assert "Web search results for query" in result
        assert "C++ programming guide" in result
    
    def test_websearch_tool_unicode_query(self):
        tool = WebSearchTool()
        result = tool.execute("Python 编程指南")
        assert "Web search results for query" in result
        assert "Python 编程指南" in result
    
    def test_websearch_tool_long_query(self):
        tool = WebSearchTool()
        long_query = "How to implement a recursive descent parser for a simple expression grammar in Python with proper error handling"
        result = tool.execute(long_query)
        assert "Web search results for query" in result
        assert long_query in result
    
    def test_websearch_tool_empty_domain_lists(self):
        tool = WebSearchTool()
        result = tool.execute(
            "Test query",
            allowed_domains=[],
            blocked_domains=[]
        )
        assert "Web search results for query" in result
        assert "Test query" in result
    
    def test_websearch_tool_simulated_results_format(self):
        tool = WebSearchTool()
        result = tool.execute("Python programming")
        # Check simulated results format
        assert "1. Example Result 1" in result
        assert "URL: https://example.com/result1" in result
        assert "Summary:" in result
        assert "2. Example Result 2" in result
        assert "URL: https://example.com/result2" in result
    
    def test_websearch_tool_query_with_quotes(self):
        tool = WebSearchTool()
        result = tool.execute('"exact phrase search"')
        assert "Web search results for query" in result
        assert '"exact phrase search"' in result
    
    def test_websearch_tool_query_with_operators(self):
        tool = WebSearchTool()
        result = tool.execute("Python AND tutorial NOT beginner")
        assert "Web search results for query" in result
        assert "Python AND tutorial NOT beginner" in result
    
    def test_websearch_tool_domain_validation(self):
        tool = WebSearchTool()
        # Test with invalid domain format
        result = tool.execute(
            "Test query",
            allowed_domains=["not a domain", "also-not-a-domain!"]
        )
        # Should still work but might include the domains in output
        assert "Web search results for query" in result
    
    def test_websearch_tool_date_aware_query(self):
        tool = WebSearchTool()
        result = tool.execute("Python news 2025")
        assert "Web search results for query" in result
        assert "Python news 2025" in result
        # Should handle date-aware queries appropriately


if __name__ == "__main__":
    pytest.main([__file__, "-v"])