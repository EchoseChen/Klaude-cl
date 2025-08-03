#!/usr/bin/env python3
"""
mitmproxy script to save all requests to https://101.47.14.0/
Usage: mitmdump -s mitm_llm_proxy.py
"""

import json
import os
from datetime import datetime
from mitmproxy import http
from mitmproxy.http import HTTPFlow


class LLMProxyCapture:
    def __init__(self):
        self.log_dir = "request_logsa"
        os.makedirs(self.log_dir, exist_ok=True)
    
    def request(self, flow: HTTPFlow) -> None:
        """Capture requests to 101.47.14.0"""
        if "101.47.14.0" in flow.request.pretty_host:
            self._save_request(flow)
    
    def response(self, flow: HTTPFlow) -> None:
        """Capture responses from 101.47.14.0"""
        if "101.47.14.0" in flow.request.pretty_host:
            self._save_response(flow)
    
    def _save_request(self, flow: HTTPFlow) -> None:
        """Save request details to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{self.log_dir}/request_{timestamp}.json"
        
        request_data = {
            "timestamp": datetime.now().isoformat(),
            "method": flow.request.method,
            "url": flow.request.pretty_url,
            "headers": dict(flow.request.headers),
            "content": flow.request.content.decode('utf-8', errors='ignore') if flow.request.content else None,
            "host": flow.request.pretty_host,
            "port": flow.request.port,
            "scheme": flow.request.scheme,
            "path": flow.request.path,
            "query": dict(flow.request.query) if flow.request.query else None
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(request_data, f, indent=2, ensure_ascii=False)
    
    def _save_response(self, flow: HTTPFlow) -> None:
        """Save response details to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{self.log_dir}/response_{timestamp}.json"
        
        response_data = {
            "timestamp": datetime.now().isoformat(),
            "request_url": flow.request.pretty_url,
            "status_code": flow.response.status_code,
            "headers": dict(flow.response.headers),
            "content": flow.response.content.decode('utf-8', errors='ignore') if flow.response.content else None,
            "reason": flow.response.reason
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(response_data, f, indent=2, ensure_ascii=False)


addons = [LLMProxyCapture()]