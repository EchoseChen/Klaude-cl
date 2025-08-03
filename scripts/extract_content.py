#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def extract_content(input_file, output_file=None):
    """Extract the 'content' field from a JSON file and save it as a separate JSON file."""
    
    # Read the input JSON file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File {input_file} not found")
        return False
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {input_file}: {e}")
        return False
    
    # Extract the content field
    if 'content' not in data:
        print("Error: 'content' field not found in the JSON file")
        return False
    
    content = data['content']
    
    # Parse the content as JSON if it's a string
    try:
        if isinstance(content, str):
            content_json = json.loads(content)
        else:
            content_json = content
    except json.JSONDecodeError as e:
        print(f"Error: Content is not valid JSON: {e}")
        return False
    
    # Generate output filename if not provided
    if output_file is None:
        input_path = Path(input_file)
        output_file = input_path.parent / f"{input_path.stem}_content.json"
    
    # Write the content to the output file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(content_json, f, indent=2, ensure_ascii=False)
        print(f"Content extracted successfully to: {output_file}")
        return True
    except Exception as e:
        print(f"Error writing to {output_file}: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_content.py <input_json_file> [output_json_file]")
        print("Example: python extract_content.py request_20250803_231115_093335.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = extract_content(input_file, output_file)
    sys.exit(0 if success else 1)