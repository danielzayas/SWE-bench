#!/usr/bin/env python3
"""
Script to generate predictions for sympy__sympy-20590 using OpenAI and Google Gemini.
Uses HuggingFace API directly to avoid dependency issues.
"""

import os
import json
import sys

# Try to use requests (might be available or easier to install)
try:
    import requests
except ImportError:
    print("requests not found. Trying to install...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        import requests
    except:
        print("ERROR: Could not install requests. Please install manually: pip install requests")
        sys.exit(1)

# Try to import OpenAI
try:
    import openai
except ImportError:
    print("openai not found. Trying to install...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "openai"], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        import openai
    except Exception as e:
        print(f"ERROR: Could not install openai: {e}")
        print("Please install manually: pip install openai")
        sys.exit(1)

# Try to import Google Generative AI
try:
    import google.generativeai as genai
except ImportError:
    print("google-generativeai not found. Trying to install...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "google-generativeai"], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        import google.generativeai as genai
    except Exception as e:
        print(f"ERROR: Could not install google-generativeai: {e}")
        print("Please install manually: pip install google-generativeai")
        sys.exit(1)


def load_instance_via_api(instance_id: str):
    """Load instance data from SWE-bench dataset using HuggingFace API."""
    print(f"Loading instance {instance_id} from SWE-bench_Lite...")
    
    # Try using SWE-bench's own utilities first (if package is installed)
    try:
        from swebench.harness.utils import load_swebench_dataset
        print("Using SWE-bench utilities...")
        dataset = load_swebench_dataset("princeton-nlp/SWE-bench_Lite", "test", [instance_id])
        if dataset:
            return dataset[0]
    except ImportError:
        pass
    except Exception as e:
        print(f"SWE-bench utilities not available: {e}")
    
    # Fallback to datasets library
    try:
        from datasets import load_dataset
        print("Using HuggingFace datasets library...")
        dataset = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
        for instance in dataset:
            if instance["instance_id"] == instance_id:
                return instance
        raise ValueError(f"Instance {instance_id} not found")
    except ImportError:
        raise ImportError(
            "Please install datasets: pip install datasets\n"
            "Or install SWE-bench package: pip install -e ."
        )


def create_prompt(instance):
    """Create a prompt for the model to generate a patch."""
    problem_statement = instance.get("problem_statement", "")
    hints_text = instance.get("hints_text", "")
    
    # Include relevant code context if available
    repo = instance.get("repo", "sympy/sympy")
    
    prompt = f"""You are tasked with fixing a bug in the {repo} repository.

Issue Description:
{problem_statement}

{hints_text if hints_text else ''}

Please generate a git diff patch that fixes this issue. The patch should:
1. Fix the bug described in the issue
2. Be properly formatted as a git diff (starting with "diff --git")
3. Only modify the necessary files
4. Follow the exact git diff format

Generate the patch now. Only output the git diff, no explanations before or after:"""
    
    return prompt


def generate_openai_patch(instance, api_key: str):
    """Generate patch using OpenAI API."""
    print("Generating patch using OpenAI GPT-4...")
    client = openai.OpenAI(api_key=api_key)
    
    prompt = create_prompt(instance)
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an expert Python developer specializing in fixing bugs. Generate git diff patches that solve software engineering problems. Always output patches in proper git diff format."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
    )
    
    patch = response.choices[0].message.content.strip()
    
    # Extract patch if it's wrapped in markdown code blocks
    if "```" in patch:
        lines = patch.split("\n")
        in_code_block = False
        patch_lines = []
        for line in lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                patch_lines.append(line)
        patch = "\n".join(patch_lines)
    
    # Ensure patch starts with diff --git
    if not patch.startswith("diff --git"):
        # Try to find the diff in the text
        if "diff --git" in patch:
            idx = patch.find("diff --git")
            patch = patch[idx:]
    
    return patch


def generate_gemini_patch(instance, api_key: str):
    """Generate patch using Google Gemini API."""
    print("Generating patch using Google Gemini...")
    genai.configure(api_key=api_key)
    
    # Try available model names - use stable versions
    model_names = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-pro-latest', 'gemini-flash-latest']
    model = None
    for model_name in model_names:
        try:
            model = genai.GenerativeModel(model_name)
            print(f"Using model: {model_name}")
            break
        except Exception as e:
            continue
    
    if model is None:
        raise ValueError("Could not find a valid Gemini model")
    
    prompt = create_prompt(instance)
    
    response = model.generate_content(prompt)
    
    patch = response.text.strip()
    
    # Extract patch if it's wrapped in markdown code blocks
    if "```" in patch:
        lines = patch.split("\n")
        in_code_block = False
        patch_lines = []
        for line in lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                patch_lines.append(line)
        patch = "\n".join(patch_lines)
    
    # Ensure patch starts with diff --git
    if not patch.startswith("diff --git"):
        # Try to find the diff in the text
        if "diff --git" in patch:
            idx = patch.find("diff --git")
            patch = patch[idx:]
    
    return patch


def save_predictions(predictions, filename: str):
    """Save predictions to JSON file."""
    with open(filename, "w") as f:
        json.dump(predictions, f, indent=2)
    print(f"✓ Saved predictions to {filename}")


def main():
    instance_id = "sympy__sympy-20590"
    
    # Get API keys from environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set")
    
    # Load instance data
    print("="*60)
    print("Loading instance data...")
    print("="*60)
    try:
        instance = load_instance_via_api(instance_id)
        print(f"✓ Loaded instance: {instance_id}")
        print(f"  Problem: {instance.get('problem_statement', '')[:150]}...")
    except Exception as e:
        print(f"✗ Error loading instance: {e}")
        print("\nTrying alternative method...")
        # If datasets library fails, we might need to install it properly
        print("Please ensure 'datasets' is installed: pip install datasets")
        sys.exit(1)
    
    # Generate OpenAI prediction
    print("\n" + "="*60)
    print("Generating OpenAI prediction...")
    print("="*60)
    try:
        openai_patch = generate_openai_patch(instance, openai_api_key)
        print(f"Generated patch length: {len(openai_patch)} characters")
        print(f"Patch preview: {openai_patch[:200]}...")
        
        openai_prediction = {
            "instance_id": instance_id,
            "model_name_or_path": "gpt-4",
            "model_patch": openai_patch
        }
        save_predictions([openai_prediction], "openai_predictions.json")
        print("✓ OpenAI prediction generated successfully")
    except Exception as e:
        print(f"✗ Error generating OpenAI prediction: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Generate Gemini prediction
    print("\n" + "="*60)
    print("Generating Gemini prediction...")
    print("="*60)
    try:
        gemini_patch = generate_gemini_patch(instance, gemini_api_key)
        print(f"Generated patch length: {len(gemini_patch)} characters")
        print(f"Patch preview: {gemini_patch[:200]}...")
        
        gemini_prediction = {
            "instance_id": instance_id,
            "model_name_or_path": "gemini-2.5-flash",
            "model_patch": gemini_patch
        }
        save_predictions([gemini_prediction], "gemini_predictions.json")
        print("✓ Gemini prediction generated successfully")
    except Exception as e:
        print(f"✗ Error generating Gemini prediction: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "="*60)
    print("All predictions generated successfully!")
    print("="*60)
    print("\nFiles created:")
    print("  - openai_predictions.json")
    print("  - gemini_predictions.json")
    print("\nYou can now run evaluations with:")
    print("  python -m swebench.harness.run_evaluation \\")
    print("    --predictions_path openai_predictions.json \\")
    print("    --instance_ids sympy__sympy-20590 \\")
    print("    --run_id openai-eval")


if __name__ == "__main__":
    main()
