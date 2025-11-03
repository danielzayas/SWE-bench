#!/bin/bash
# Script to install dependencies for prediction generation
# This works around pip hash verification issues

echo "Installing dependencies for prediction generation..."
echo "Note: If you encounter hash verification errors, try:"
echo "  pip install --no-deps requests"
echo "  pip install --no-deps openai"  
echo "  pip install --no-deps google-generativeai"
echo "  pip install --no-deps datasets"
echo ""
echo "Or install manually:"
echo "  pip install requests openai google-generativeai datasets"
echo ""

python3 -m pip install requests openai google-generativeai datasets 2>&1 | tail -20

