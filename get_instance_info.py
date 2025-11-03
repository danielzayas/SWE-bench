#!/usr/bin/env python3
"""Get basic info about sympy__sympy-20590 instance."""

# Use the local swebench module
import sys
sys.path.insert(0, '/Users/danielzayas/.cursor/worktrees/SWE-bench/k1161')

# Now we can try importing what we need
try:
    # Try to import datasets
    from datasets import load_dataset
    dataset = load_dataset('princeton-nlp/SWE-bench', split='test')
    
    # Find the instance
    for item in dataset:
        if item['instance_id'] == 'sympy__sympy-20590':
            print("Instance found!")
            print(f"Instance ID: {item['instance_id']}")
            print(f"Repository: {item['repo']}")
            print(f"Base Commit: {item['base_commit']}")
            print(f"\nProblem Statement:")
            print(item['problem_statement'][:500] + "...")
            break
except Exception as e:
    print(f"Error: {e}")
    print("\nTrying alternative approach...")
    print("Please ensure datasets library is installed:")
    print("  pip install datasets")

