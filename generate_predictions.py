#!/usr/bin/env python3
"""
Generate predictions for sympy__sympy-20590 using OpenAI and Google Gemini models.
"""

import json
import os
from pathlib import Path
from datasets import load_dataset
import openai
import google.generativeai as genai

def load_instance_data(instance_id="sympy__sympy-20590"):
    """Load the instance data from SWE-bench dataset."""
    print(f"Loading dataset for instance {instance_id}...")
    dataset = load_dataset('princeton-nlp/SWE-bench', split='test')
    
    # Find the specific instance
    instance = None
    for item in dataset:
        if item['instance_id'] == instance_id:
            instance = item
            break
    
    if instance is None:
        raise ValueError(f"Instance {instance_id} not found in dataset")
    
    return instance

def create_prompt(instance):
    """Create a prompt for the model to generate a patch."""
    prompt = f"""You are a software engineer tasked with fixing a bug in a Python repository.

Repository: {instance['repo']}
Problem Statement:
{instance['problem_statement']}

Please provide a git diff patch that fixes this issue. The patch should be in unified diff format and start with 'diff --git'.
Only provide the patch, no additional explanation."""
    
    return prompt

def call_openai(prompt, model="gpt-4"):
    """Call OpenAI API to generate a patch."""
    print(f"Calling OpenAI model {model}...")
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    client = openai.OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful software engineer that provides git diff patches to fix bugs."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=4096
    )
    
    return response.choices[0].message.content

def call_gemini(prompt, model="gemini-1.5-pro"):
    """Call Google Gemini API to generate a patch."""
    print(f"Calling Google Gemini model {model}...")
    
    # Try GEMINI_API_KEY first, fall back to GOOGLE_API_KEY
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set")
    
    genai.configure(api_key=api_key)
    
    model_instance = genai.GenerativeModel(model)
    response = model_instance.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.2,
            max_output_tokens=4096,
        )
    )
    
    return response.text

def extract_patch(text):
    """Extract the patch from the model output."""
    # Look for diff content
    lines = text.split('\n')
    patch_lines = []
    in_patch = False
    
    for line in lines:
        if line.startswith('diff --git'):
            in_patch = True
        if in_patch:
            patch_lines.append(line)
    
    if patch_lines:
        return '\n'.join(patch_lines)
    else:
        # If no clear patch found, return the whole text
        return text

def main():
    # Load the instance data
    instance = load_instance_data("sympy__sympy-20590")
    
    print(f"\nInstance ID: {instance['instance_id']}")
    print(f"Repository: {instance['repo']}")
    print(f"Base commit: {instance['base_commit']}")
    
    # Create prompt
    prompt = create_prompt(instance)
    
    # Generate predictions with OpenAI
    print("\n" + "="*80)
    print("GENERATING OPENAI PREDICTION")
    print("="*80)
    try:
        openai_output = call_openai(prompt)
        openai_patch = extract_patch(openai_output)
        
        openai_prediction = {
            "instance_id": instance['instance_id'],
            "model_name_or_path": "gpt-4",
            "model_patch": openai_patch
        }
        
        # Save to file
        openai_file = Path("openai_predictions.json")
        with open(openai_file, 'w') as f:
            json.dump([openai_prediction], f, indent=2)
        
        print(f"\n✓ OpenAI prediction saved to {openai_file}")
        print(f"Patch preview (first 500 chars):\n{openai_patch[:500]}...")
        
    except Exception as e:
        print(f"✗ Error calling OpenAI: {e}")
        raise
    
    # Generate predictions with Gemini
    print("\n" + "="*80)
    print("GENERATING GEMINI PREDICTION")
    print("="*80)
    try:
        gemini_output = call_gemini(prompt)
        gemini_patch = extract_patch(gemini_output)
        
        gemini_prediction = {
            "instance_id": instance['instance_id'],
            "model_name_or_path": "gemini-1.5-pro",
            "model_patch": gemini_patch
        }
        
        # Save to file
        gemini_file = Path("gemini_predictions.json")
        with open(gemini_file, 'w') as f:
            json.dump([gemini_prediction], f, indent=2)
        
        print(f"\n✓ Gemini prediction saved to {gemini_file}")
        print(f"Patch preview (first 500 chars):\n{gemini_patch[:500]}...")
        
    except Exception as e:
        print(f"✗ Error calling Gemini: {e}")
        raise
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✓ Generated predictions for instance: {instance['instance_id']}")
    print(f"✓ OpenAI predictions saved to: openai_predictions.json")
    print(f"✓ Gemini predictions saved to: gemini_predictions.json")
    print("\nYou can now run evaluations with:")
    print(f"  python -m swebench.harness.run_evaluation \\")
    print(f"    --predictions_path openai_predictions.json \\")
    print(f"    --max_workers 1 \\")
    print(f"    --instance_ids {instance['instance_id']} \\")
    print(f"    --run_id openai-evaluation")
    print(f"\n  python -m swebench.harness.run_evaluation \\")
    print(f"    --predictions_path gemini_predictions.json \\")
    print(f"    --max_workers 1 \\")
    print(f"    --instance_ids {instance['instance_id']} \\")
    print(f"    --run_id gemini-evaluation")

if __name__ == "__main__":
    main()

