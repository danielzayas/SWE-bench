#!/usr/bin/env python3
"""
Run evaluation directly by calling the main function.
This bypasses the need for a fully installed package.
"""

import sys
import os

# Add the project directory to path
sys.path.insert(0, '/Users/danielzayas/.cursor/worktrees/SWE-bench/k1161')

# Now try to import and run the evaluation
try:
    # First check if we have the required modules
    missing_modules = []
    try:
        import requests
    except ImportError:
        missing_modules.append("requests")
    
    try:
        import docker
    except ImportError:
        missing_modules.append("docker")
    
    try:
        import datasets
    except ImportError:
        missing_modules.append("datasets")
    
    try:
        import unidiff
    except ImportError:
        missing_modules.append("unidiff")
    
    try:
        import rich
    except ImportError:
        missing_modules.append("rich")
    
    try:
        import tqdm
    except ImportError:
        missing_modules.append("tqdm")
    
    try:
        import git
    except ImportError:
        missing_modules.append("GitPython")
    
    try:
        import dotenv
    except ImportError:
        missing_modules.append("python-dotenv")
    
    try:
        import tenacity
    except ImportError:
        missing_modules.append("tenacity")
    
    if missing_modules:
        print("Missing required modules:")
        for module in missing_modules:
            print(f"  - {module}")
        print("\nPlease install them with:")
        print(f"  pip install {' '.join(missing_modules)}")
        sys.exit(1)
    
    # Try to import the evaluation module
    from swebench.harness.run_evaluation import main
    
    print("Running OpenAI evaluation...")
    main(
        dataset_name="princeton-nlp/SWE-bench",
        split="test",
        instance_ids=["sympy__sympy-20590"],
        predictions_path="openai_predictions.json",
        max_workers=1,
        force_rebuild=False,
        cache_level="env",
        clean=False,
        open_file_limit=4096,
        run_id="openai-evaluation",
        timeout=1800,
        namespace="",
        rewrite_reports=False,
        modal=False,
    )
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

