#!/bin/bash
# Run full model validation and save output to validation_output.txt

echo "Running validation..."
source ./myenv/bin/activate

python validate_models.py | tee validation_output.txt

echo "Done. Output saved to validation_output.txt"
