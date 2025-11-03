# Generating Predictions for sympy__sympy-20590

This directory contains scripts to generate predictions using OpenAI and Google Gemini models.

## Prerequisites

You need to install the following Python packages:
- `datasets` (HuggingFace)
- `openai`
- `google-generativeai`

**Note**: If you encounter pip hash verification errors, try:
```bash
pip install --no-deps datasets
pip install --no-deps openai
pip install --no-deps google-generativeai
```

Or install the SWE-bench package in editable mode (which includes datasets):
```bash
pip install -e .
```

## Environment Variables

Set the following environment variables:
- `OPENAI_API_KEY` - Your OpenAI API key
- `GEMINI_API_KEY` or `GOOGLE_API_KEY` - Your Google/Gemini API key

## Usage

Run the prediction generation script:
```bash
python3 generate_predictions.py
```

This will create:
- `openai_predictions.json` - Predictions from GPT-4
- `gemini_predictions.json` - Predictions from Gemini Pro

## Running Evaluations

After generating predictions, run evaluations:

For OpenAI predictions:
```bash
python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Lite \
    --predictions_path openai_predictions.json \
    --instance_ids sympy__sympy-20590 \
    --max_workers 1 \
    --run_id openai-eval \
    --namespace ''
```

For Gemini predictions:
```bash
python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Lite \
    --predictions_path gemini_predictions.json \
    --instance_ids sympy__sympy-20590 \
    --max_workers 1 \
    --run_id gemini-eval \
    --namespace ''
```

