#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="$PROJECT_DIR/example/target_c_project"
OUTPUT="$PROJECT_DIR/output/vulnerability_score.txt"

python3 "$PROJECT_DIR/code_risk_evaluator/flawfinder_evaluator.py" "$TARGET" "$OUTPUT"
