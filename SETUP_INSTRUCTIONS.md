# Setup Instructions for Generating Predictions

## Issue
There appears to be a pip hash verification issue preventing automatic package installation. You'll need to install dependencies manually.

## Manual Dependency Installation

Try one of these methods:

### Method 1: Use a clean Python environment
```bash
# Create a new virtual environment
python3 -m venv venv_clean
source venv_clean/bin/activate

# Upgrade pip first
pip install --upgrade pip

# Install dependencies
pip install requests openai google-generativeai datasets
```

### Method 2: Install SWE-bench package (includes datasets)
```bash
# Make sure you have a newer pip or setuptools
pip install --upgrade setuptools wheel

# Install SWE-bench in development mode
pip install -e .
```

### Method 3: Install packages individually with --no-deps
```bash
pip install --no-deps requests
pip install --no-deps urllib3 idna charset-normalizer certifi  # requests dependencies
pip install --no-deps openai
pip install --no-deps google-generativeai
pip install --no-deps datasets
```

## Environment Variables

Make sure these are set:
```bash
export OPENAI_API_KEY="your-key-here"
export GEMINI_API_KEY="your-key-here"  # or GOOGLE_API_KEY
```

## Running the Script

Once dependencies are installed:
```bash
python3 generate_predictions.py
```

This will create:
- `openai_predictions.json`
- `gemini_predictions.json`

## Running Evaluations

After generating predictions, run evaluations with the commands in `README_PREDICTIONS.md`.

