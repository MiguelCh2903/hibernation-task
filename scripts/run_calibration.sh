#!/bin/bash
# Script to run calibration for task and suspend timing

set -euo pipefail

# Configurable parameters
MODE="mem"                        # "mem" for suspend-to-RAM, "disk" for hibernation
TASK_CMD="./scripts/my_task.sh"
LOG_FILE="./logs/calibration_log.csv"

# Run calibration
echo "Running calibration..."
python3 ./src/calibrate_params.py \
    --mode "$MODE" \
    --task-cmd "$TASK_CMD" \
    --log-file "$LOG_FILE"
