#!/bin/bash
# Wrapper script for question generation cronjob
# Usage: ./run_generator.sh [count] [parallel]
#
# Required environment variables:
#   DATABASE_URL - PostgreSQL connection string
#
# Optional environment variables:
#   API_BASE_URL - API endpoint (default: http://localhost:8000)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Check required environment variable
if [ -z "$DATABASE_URL" ]; then
    echo "[$(date)] ERROR: DATABASE_URL environment variable is required" >&2
    exit 1
fi

# Default values
COUNT=${1:-100}
PARALLEL=${2:-6}

# Log file
LOG_FILE="/var/log/learntogrow/question_generator.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Run the generator
echo "[$(date)] Starting question generation: $COUNT questions with $PARALLEL parallel" >> "$LOG_FILE"

python3 "$SCRIPT_DIR/generate_questions.py" \
    --count "$COUNT" \
    --parallel "$PARALLEL" \
    >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date)] Question generation completed successfully" >> "$LOG_FILE"
else
    echo "[$(date)] Question generation failed with exit code $EXIT_CODE" >> "$LOG_FILE"
fi

exit $EXIT_CODE
