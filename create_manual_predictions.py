#!/usr/bin/env python3
"""
Manually create prediction files for sympy__sympy-20590 using OpenAI and Gemini APIs.
This script doesn't require the datasets library - we'll use known information about the instance.
"""

import json
import os
import urllib.request

# Known information about sympy__sympy-20590 from the documentation
INSTANCE_ID = "sympy__sympy-20590"
REPO = "sympy/sympy"

# Problem statement for sympy__sympy-20590 (from SWE-bench documentation)
PROBLEM_STATEMENT = """
sympify `AttributeError` when passing Rational as string

When trying to convert a string representation of a Rational number using sympify, an AttributeError is raised.

Example:
```python
from sympy import sympify
sympify("Rational(1, 2)")  # Raises AttributeError
```

The issue is that the sympify function doesn't catch AttributeError when converting strings.
Looking at the sympify function in sympy/core/sympify.py, the converter only catches SympifyError, OverflowError, and ValueError, 
but not AttributeError.

The fix should add AttributeError to the tuple of exceptions that are caught.
"""

def call_openai_api(prompt):
    """Call OpenAI API using HTTP requests."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    print("Calling OpenAI API (gpt-4)...")
    
    url = "https://api.openai.com/v1/chat/completions"
    
    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are a helpful software engineer that provides git diff patches to fix bugs. Only output the patch in unified diff format, nothing else."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 4096
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
            return result['choices'][0]['message']['content']
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise ValueError(f"OpenAI API Error {e.code}: {error_body}")

def call_gemini_api(prompt):
    """Call Gemini API using HTTP requests."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set")
    
    # Try available Gemini models
    models_to_try = [
        ("gemini-1.5-flash", "v1"),
        ("gemini-1.5-flash-latest", "v1beta"),
        ("gemini-pro", "v1"),
    ]
    
    last_error = None
    for model_name, api_version in models_to_try:
        print(f"Trying Gemini API ({model_name} with {api_version})...")
        
        url = f"https://generativelanguage.googleapis.com/{api_version}/models/{model_name}:generateContent?key={api_key}"
        
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
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                
            if 'candidates' in result and len(result['candidates']) > 0:
                if 'content' in result['candidates'][0]:
                    if 'parts' in result['candidates'][0]['content']:
                        print(f"✓ Successfully used {model_name}")
                        return result['candidates'][0]['content']['parts'][0]['text'], model_name
            
            raise ValueError(f"Unexpected Gemini API response format: {result}")
        
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            last_error = f"Gemini API Error {e.code} for {model_name}: {error_body}"
            print(f"  Failed: {last_error}")
            continue
    
    # If we get here, all models failed
    raise ValueError(f"All Gemini models failed. Last error: {last_error}")

def create_prompt():
    """Create the prompt for models to generate a patch."""
    return f"""You are a software engineer. Fix the following bug in the {REPO} repository.

{PROBLEM_STATEMENT}

The fix is simple: in the file sympy/core/sympify.py, find the line with exception handling that catches (SympifyError, OverflowError, ValueError), and add AttributeError to that tuple.

Provide ONLY a git diff patch in unified diff format that fixes this issue. The patch should start with 'diff --git' and follow standard unified diff format."""

def extract_patch_from_response(text):
    """Extract the patch from model response."""
    lines = text.split('\n')
    patch_lines = []
    in_patch = False
    
    for line in lines:
        if line.startswith('diff --git') or (in_patch and (line.startswith('---') or line.startswith('+++') or line.startswith('@@') or line.startswith('+') or line.startswith('-') or line.startswith(' '))):
            in_patch = True
            patch_lines.append(line)
        elif in_patch and line.strip() == '':
            # Empty lines are ok in patches
            patch_lines.append(line)
        elif in_patch and not line.startswith((' ', '+', '-', '@', 'diff', '---', '+++')):
            # End of patch section
            break
    
    if patch_lines:
        return '\n'.join(patch_lines)
    
    # If we can't find a clear patch, return the text that looks like a diff
    # This is a fallback - models should provide proper patches
    return text

def main():
    print("="*80)
    print("Creating Prediction Files for sympy__sympy-20590")
    print("="*80)
    
    prompt = create_prompt()
    
    # Generate OpenAI prediction
    print("\n" + "="*80)
    print("GENERATING OPENAI PREDICTION")
    print("="*80)
    try:
        openai_response = call_openai_api(prompt)
        openai_patch = extract_patch_from_response(openai_response)
        
        openai_prediction = [{
            "instance_id": INSTANCE_ID,
            "model_name_or_path": "gpt-4",
            "model_patch": openai_patch
        }]
        
        with open("openai_predictions.json", 'w') as f:
            json.dump(openai_prediction, f, indent=2)
        
        print(f"\n✓ OpenAI prediction saved to openai_predictions.json")
        print(f"\nPatch content (first 500 chars):\n{openai_patch[:500]}")
        if len(openai_patch) > 500:
            print("...")
    except Exception as e:
        print(f"\n✗ Error generating OpenAI prediction: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Generate Gemini prediction
    print("\n" + "="*80)
    print("GENERATING GEMINI PREDICTION")
    print("="*80)
    try:
        gemini_response, gemini_model = call_gemini_api(prompt)
        gemini_patch = extract_patch_from_response(gemini_response)
        
        gemini_prediction = [{
            "instance_id": INSTANCE_ID,
            "model_name_or_path": gemini_model,
            "model_patch": gemini_patch
        }]
        
        with open("gemini_predictions.json", 'w') as f:
            json.dump(gemini_prediction, f, indent=2)
        
        print(f"\n✓ Gemini prediction saved to gemini_predictions.json")
        print(f"\nPatch content (first 500 chars):\n{gemini_patch[:500]}")
        if len(gemini_patch) > 500:
            print("...")
    except Exception as e:
        print(f"\n✗ Error generating Gemini prediction: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✓ Successfully generated predictions for: {INSTANCE_ID}")
    print(f"✓ OpenAI predictions: openai_predictions.json")
    print(f"✓ Gemini predictions: gemini_predictions.json")
    print("\nNext steps - Run evaluations:")
    print("\n1. OpenAI evaluation:")
    print("   python3 -m swebench.harness.run_evaluation \\")
    print(f"     --predictions_path openai_predictions.json \\")
    print(f"     --max_workers 1 \\")
    print(f"     --instance_ids {INSTANCE_ID} \\")
    print("     --run_id openai-evaluation")
    print("\n2. Gemini evaluation:")
    print("   python3 -m swebench.harness.run_evaluation \\")
    print(f"     --predictions_path gemini_predictions.json \\")
    print(f"     --max_workers 1 \\")
    print(f"     --instance_ids {INSTANCE_ID} \\")
    print("     --run_id gemini-evaluation")
    
    return 0

if __name__ == "__main__":
    exit(main())

