#!/usr/bin/env bash

# Confirm the correct virtual environment.

# Get the project root directory (where Claude Code is running)
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
EXPECTED_VENV="$PROJECT_ROOT/.venv"

# Check if virtual environment is active AND it's the correct one
if [ -n "$VIRTUAL_ENV" ] && [ "$VIRTUAL_ENV" = "$EXPECTED_VENV" ]; then
    echo "✅ Virtual environment active: $VIRTUAL_ENV"
    exit 0
fi

# Check if wrong venv is active
if [ -n "$VIRTUAL_ENV" ]; then
    echo "⚠️  WARNING: Wrong virtual environment is active!" >&2
    echo "   Active: $VIRTUAL_ENV" >&2
    echo "   Expected: $EXPECTED_VENV" >&2
    echo "Please deactivate and activate the correct venv:" >&2
    echo "  deactivate" >&2
    echo "  source $EXPECTED_VENV/bin/activate" >&2
    exit 1
fi

# No venv is active
echo "❌ ERROR: Virtual environment not active!" >&2
echo "Please activate the project venv before running Claude Code:" >&2
echo "  source $EXPECTED_VENV/bin/activate" >&2
exit 1
