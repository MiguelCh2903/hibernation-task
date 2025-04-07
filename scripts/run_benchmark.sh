#!/bin/bash
# Script to run scheduled benchmark

set -euo pipefail

# Parameters
MODE="mem"
PERIOD=60
ACTIVE_DELAY=5.0
PRE_WAKEUP_DELAY=6.0
ITERATIONS=3
TASK_CMD="./scripts/my_task.sh"
LOG_FILE="./logs/scheduled_benchmark2.csv"

# Run benchmark script in src/
echo "Starting scheduled benchmark..."
python3 ./src/scheduled_benchmark.py \
    --mode "$MODE" \
    --period "$PERIOD" \
    --active-delay "$ACTIVE_DELAY" \
    --pre-wakeup-delay "$PRE_WAKEUP_DELAY" \
    --iterations "$ITERATIONS" \
    --task-cmd "$TASK_CMD" \
    --log-file "$LOG_FILE"
