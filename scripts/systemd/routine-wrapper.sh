#!/bin/bash
set -euo pipefail

# Run your routine task (adjust the path as necessary)
echo "Starting routine task at $(date)"
/home/miguel/multipacha/hibernate-task/scripts/my_task.sh

# Wait for 5 seconds after the task completes
sleep 5

# Calculate the wakeup time:
# Get the current minute's beginning and add 1 minute to it, so the next minute starts exactly at :00.
# Then, subtract 5 seconds to wake up 5 seconds before the next minute.
next_minute=$(date -d "$(date +%Y-%m-%dT%H:%M:00) next minute" +%s)
wakeup_time=$(( next_minute - 5 ))
current_time=$(date +%s)
delay=$(( wakeup_time - current_time ))

echo "Suspending for $delay seconds. Will wake up at $(date -d "@$wakeup_time")"

# Suspend to memory (S3) and schedule wakeup
rtcwake -m mem -s "$delay"