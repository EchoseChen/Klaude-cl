#!/usr/bin/env python3
"""Sample Python file for testing tools"""

import os
import sys
from pathlib import Path
import json

def hello_world():
    """Sample function"""
    print("Hello, World!")

class SampleClass:
    """Sample class for testing"""
    def __init__(self):
        self.value = 42
    
    def get_value(self):
        return self.value

if __name__ == "__main__":
    hello_world()