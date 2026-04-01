#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="$PROJECT_DIR/target/sample_c_project"
OUTPUT="$PROJECT_DIR/risk_report.json"

python3 "$PROJECT_DIR/code_risk_evaluator/example_c_evaluator.py" "$TARGET" "$OUTPUT"
