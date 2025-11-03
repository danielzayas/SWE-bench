# Summary: Generating Predictions for sympy__sympy-20590

## Status

I've created scripts to generate predictions using OpenAI and Google Gemini models for the `sympy__sympy-20590` instance. However, there's a pip hash verification issue preventing automatic dependency installation.

## Files Created

1. **`generate_predictions.py`** - Main script to generate predictions
   - Loads instance data from SWE-bench_Lite
   - Generates patches using OpenAI GPT-4
   - Generates patches using Google Gemini Pro
   - Saves predictions to JSON files

2. **`openai_predictions.json`** - Will be created after running the script
3. **`gemini_predictions.json`** - Will be created after running the script

4. **`README_PREDICTIONS.md`** - Instructions for running predictions and evaluations
5. **`SETUP_INSTRUCTIONS.md`** - Instructions for installing dependencies
6. **`install_deps.sh`** - Helper script for dependency installation

## Next Steps

### 1. Install Dependencies Manually

Due to pip hash verification issues, you'll need to install dependencies manually. Try:

```bash
# Option A: Use a clean virtual environment
python3 -m venv venv_clean
source venv_clean/bin/activate
pip install --upgrade pip
pip install requests openai google-generativeai datasets

# Option B: Install SWE-bench package (includes datasets)
pip install -e .

# Option C: Install without hash checking (if your pip supports it)
pip install --no-deps requests openai google-generativeai datasets
```

### 2. Set Environment Variables

```bash
export OPENAI_API_KEY="your-openai-key"
export GEMINI_API_KEY="your-gemini-key"  # or GOOGLE_API_KEY
```

### 3. Run Prediction Generation

```bash
python3 generate_predictions.py
```

This will create:
- `openai_predictions.json`
- `gemini_predictions.json`

### 4. Run Evaluations

**For OpenAI predictions:**
```bash
python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Lite \
    --predictions_path openai_predictions.json \
    --instance_ids sympy__sympy-20590 \
    --max_workers 1 \
    --run_id openai-eval \
    --namespace ''
```

**For Gemini predictions:**
```bash
python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Lite \
    --predictions_path gemini_predictions.json \
    --instance_ids sympy__sympy-20590 \
    --max_workers 1 \
    --run_id gemini-eval \
    --namespace ''
```

## Known Issues

- **Pip hash verification**: There appears to be a requirements file or configuration enforcing hash checking, preventing automatic package installation. This needs to be resolved manually.

## Script Functionality

The `generate_predictions.py` script:
1. Loads the `sympy__sympy-20590` instance from SWE-bench_Lite
2. Creates prompts with the problem statement and hints
3. Calls OpenAI GPT-4 API to generate a patch
4. Calls Google Gemini Pro API to generate a patch
5. Saves both predictions in the correct JSON format for SWE-bench evaluation

The prediction format matches SWE-bench requirements:
```json
{
  "instance_id": "sympy__sympy-20590",
  "model_name_or_path": "gpt-4",
  "model_patch": "diff --git ..."
}
```

