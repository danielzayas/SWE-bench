#!/usr/bin/env python3
"""Generate Gemini prediction using correct model name."""

import json
import os
import urllib.request

def call_gemini():
    """Call Gemini API."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not set")
    
    prompt = """Fix this bug: In sympy/core/sympify.py line 508, add AttributeError to the exception tuple.

Change:
    except (TokenError, SyntaxError, ValueError):

To:
    except (TokenError, SyntaxError, ValueError, AttributeError):

Provide ONLY a git unified diff patch."""
    
    # Use gemini-2.0-flash instead of 2.5 to avoid thinking tokens
    model = "gemini-2.0-flash"
    version = "v1"
    
    print(f"Calling Gemini API ({model} with {version})...")
    url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 4096,
        }
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
    
    # Debug: print the response structure
    print(f"Response structure: {json.dumps(result, indent=2)[:500]}...")
        
    if 'candidates' in result and len(result['candidates']) > 0:
        candidate = result['candidates'][0]
        
        # Check finish reason
        finish_reason = candidate.get('finishReason', '')
        if finish_reason == 'MAX_TOKENS':
            print("Warning: Response was cut off due to MAX_TOKENS")
        
        if 'content' in candidate:
            if 'parts' in candidate['content']:
                content = candidate['content']['parts'][0]['text']
                return content, model
    
    raise ValueError(f"Unexpected response format: {result}")

def main():
    try:
        response, model = call_gemini()
        
        print("="*80)
        print("Gemini Response:")
        print("="*80)
        print(response)
        print("="*80)
        
        # Create prediction file
        prediction = [{
            "instance_id": "sympy__sympy-20590",
            "model_name_or_path": model,
            "model_patch": response
        }]
        
        with open("gemini_predictions.json", 'w') as f:
            json.dump(prediction, f, indent=2)
        
        print("\n✓ Gemini prediction saved to gemini_predictions.json")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

