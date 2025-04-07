# File: calibrate_params.py
#!/usr/bin/env python3
"""
Calibration script to measure task execution time and suspend/resume durations.
Generates a CSV log and prints average metrics to help configure the main benchmark.
"""
import argparse
import csv
import datetime
import logging
import os
import shutil
import subprocess
import sys
import time


def check_environment():
    """Ensure rtcwake is available and script is run as root."""
    if os.geteuid() != 0:
        logging.error("Root privileges required: please run with sudo or as root.")
        sys.exit(1)
    if not shutil.which("rtcwake"):
        logging.error("rtcwake command not found: please install util-linux package.")
        sys.exit(1)


def run_task(cmd: str) -> float:
    """Run the given shell command and return its execution duration in seconds."""
    start = datetime.datetime.now()
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Task command failed (exit {e.returncode}): {e}")
        sys.exit(1)
    end = datetime.datetime.now()
    return (end - start).total_seconds()


def rtc_sleep(mode: str, secs: int) -> float:
    """Suspend the system using rtcwake and return the actual suspend duration."""
    start = datetime.datetime.now()
    try:
        subprocess.run(["rtcwake", "-m", mode, "-s", str(secs)], check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"rtcwake failed (exit {e.returncode}): {e}. Ensure proper privileges and hardware support.")
        sys.exit(1)
    end = datetime.datetime.now()
    return (end - start).total_seconds()


def main():
    parser = argparse.ArgumentParser(
        description="Measure task and suspend/resume durations for calibration."
    )
    parser.add_argument(
        "--mode", choices=["mem", "disk"], default="mem",
        help="Suspend mode: mem (S3) or disk (S4)."
    )
    parser.add_argument(
        "--suspend-secs", type=int, default=5,
        help="Requested suspend duration in seconds."
    )
    parser.add_argument(
        "--iterations", type=int, default=5,
        help="Number of calibration iterations."
    )
    parser.add_argument(
        "--task-cmd", required=True,
        help="Shell command for the task to measure (e.g., './scripts/my_task.sh')."
    )
    parser.add_argument(
        "--log-file", default="calibration_log.csv",
        help="CSV file to write calibration results."
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    check_environment()

    new_file = not os.path.exists(args.log_file)
    with open(args.log_file, "a", newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["iter", "task_duration_s", "requested_suspend_s", "actual_suspend_s"])

        task_durations = []
        suspend_overheads = []

        for i in range(1, args.iterations + 1):
            logging.info(f"Calibration iteration {i}/{args.iterations}")

            # Measure task duration
            td = run_task(args.task_cmd)
            task_durations.append(td)
            logging.info(f"Task duration: {td:.3f}s")

            # Measure suspend/resume duration
            actual = rtc_sleep(args.mode, args.suspend_secs)
            overhead = actual - args.suspend_secs
            suspend_overheads.append(overhead)
            logging.info(f"Requested suspend: {args.suspend_secs}s, actual: {actual:.3f}s, overhead: {overhead:.3f}s")

            writer.writerow([i, f"{td:.3f}", args.suspend_secs, f"{actual:.3f}"])
            f.flush()

    avg_task = sum(task_durations) / len(task_durations)
    avg_overhead = sum(suspend_overheads) / len(suspend_overheads)

    print("\nCalibration Summary:")
    print(f"Average task duration: {avg_task:.3f}s")
    print(f"Average suspend overhead: {avg_overhead:.3f}s")


if __name__ == "__main__":
    main()