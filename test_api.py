#!/usr/bin/env python3
"""Test the API calls to see full responses."""

import json
import os
import urllib.request

def test_openai():
    """Test OpenAI API."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not set")
        return
    
    prompt = """You are a software engineer. Fix this bug in the sympy repository:

The sympify function in sympy/core/sympify.py doesn't catch AttributeError when converting strings.

Provide a git diff patch that adds AttributeError to the exception tuple on line 508.
The current line is:
         ValueError)):

Change it to:
         ValueError, AttributeError)):

Provide ONLY the patch in unified diff format, starting with 'diff --git'."""
    
    url = "https://api.openai.com/v1/chat/completions"
    
    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are a helpful software engineer that provides git diff patches. Provide ONLY the patch, nothing else."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 2000
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        content = result['choices'][0]['message']['content']
        print("="*80)
        print("OpenAI Response:")
        print("="*80)
        print(content)
        print("="*80)
        print(f"Length: {len(content)} characters")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_openai()

