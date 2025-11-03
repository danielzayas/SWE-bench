#!/usr/bin/env python3
"""Test Gemini API with different endpoints."""

import json
import os
import urllib.request

def test_gemini():
    """Test Gemini API."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY or GOOGLE_API_KEY not set")
        return
    
    print(f"Using API key: ...{api_key[-8:]}")
    
    prompt = """You are a software engineer. Fix this bug in the sympy repository:

The sympify function in sympy/core/sympify.py doesn't catch AttributeError when converting strings.

Provide a git diff patch that adds AttributeError to the exception tuple around line 508.
The current line is:
         ValueError)):

Change it to:
         ValueError, AttributeError)):

Provide ONLY the patch in unified diff format, starting with 'diff --git'."""
    
    # Try v1 API
    models = [
        ("gemini-1.5-flash-8b", "v1beta"),
        ("gemini-1.5-flash", "v1beta"),
        ("gemini-pro", "v1beta"),
    ]
    
    for model, version in models:
        print(f"\nTrying {model} with {version}...")
        url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 2000,
            }
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                
            if 'candidates' in result and len(result['candidates']) > 0:
                if 'content' in result['candidates'][0]:
                    if 'parts' in result['candidates'][0]['content']:
                        content = result['candidates'][0]['content']['parts'][0]['text']
                        print("="*80)
                        print(f"Gemini Response ({model}):")
                        print("="*80)
                        print(content)
                        print("="*80)
                        print(f"Length: {len(content)} characters")
                        return
            
            print(f"Unexpected response format: {json.dumps(result, indent=2)}")
            
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"Error {e.code}: {error_body[:200]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_gemini()

