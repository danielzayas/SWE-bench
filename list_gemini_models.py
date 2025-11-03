#!/usr/bin/env python3
"""List available Gemini models."""

import json
import os
import urllib.request

def list_models():
    """List available Gemini models."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY or GOOGLE_API_KEY not set")
        return
    
    print(f"Using API key: ...{api_key[-8:]}")
    
    for version in ["v1beta", "v1"]:
        print(f"\nTrying to list models with API version {version}...")
        url = f"https://generativelanguage.googleapis.com/{version}/models?key={api_key}"
        
        req = urllib.request.Request(url)
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                
            if 'models' in result:
                print(f"\nAvailable models (API {version}):")
                print("="*80)
                for model in result['models']:
                    name = model.get('name', 'unknown')
                    display_name = model.get('displayName', '')
                    supported_methods = model.get('supportedGenerationMethods', [])
                    print(f"  - {name}")
                    print(f"    Display: {display_name}")
                    print(f"    Methods: {', '.join(supported_methods)}")
                    print()
            else:
                print(f"Unexpected response: {json.dumps(result, indent=2)[:500]}")
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"Error {e.code}: {error_body[:300]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    list_models()

