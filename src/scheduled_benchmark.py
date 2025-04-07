# File: scheduled_benchmark.py
#!/usr/bin/env python3
"""
Scheduled benchmark for task execution and system suspend/resume cycles.
Schedules each task to start at fixed intervals (e.g., every minute) aligned to the clock,
performs the task, waits, suspends the system, and ensures the next task starts precisely on time.
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


def wait_until(target: datetime.datetime) -> None:
    """Sleep until the target datetime."""
    now = datetime.datetime.now()
    delta = (target - now).total_seconds()
    if delta > 0:
        time.sleep(delta)


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
        description="Run scheduled task and suspend/resume benchmark."
    )
    parser.add_argument(
        "--mode", choices=["mem", "disk"], default="mem",
        help="Suspend mode: mem (S3) or disk (S4)."
    )
    parser.add_argument(
        "--period", type=int, default=60,
        help="Interval between task starts in seconds (default: 60)."
    )
    parser.add_argument(
        "--active-delay", type=float, default=5.0,
        help="Delay after task completion before suspending, in seconds."
    )
    parser.add_argument(
        "--pre-wakeup-delay", type=float, default=5.0,
        help="Time before the next scheduled start to wake up, in seconds."
    )
    parser.add_argument(
        "--iterations", type=int, default=5,
        help="Number of benchmark iterations."
    )
    parser.add_argument(
        "--task-cmd", required=True,
        help="Shell command for the task (e.g., './scripts/my_task.sh')."
    )
    parser.add_argument(
        "--log-file", default="scheduled_benchmark.csv",
        help="CSV file to write benchmark results."
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    check_environment()

    # Calculate first start aligned to the next period boundary
    now = datetime.datetime.now()
    next_boundary = (now.replace(second=0, microsecond=0)
                     + datetime.timedelta(seconds=args.period))
    logging.info(f"Waiting until first scheduled start at {next_boundary.isoformat()}")
    wait_until(next_boundary)

    fieldnames = [
        "iter",
        "scheduled_start",
        "actual_task_start",
        "task_duration_s",
        "suspend_start",
        "requested_suspend_s",
        "actual_suspend_s",
        "resume_time",
        "next_scheduled_start",
        "next_actual_start"
    ]

    new_file = not os.path.exists(args.log_file)
    with open(args.log_file, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if new_file:
            writer.writeheader()

        for i in range(1, args.iterations + 1):
            scheduled_start = next_boundary + datetime.timedelta(seconds=(i - 1) * args.period)
            logging.info(f"Iteration {i}/{args.iterations}: waiting until {scheduled_start.isoformat()}")
            wait_until(scheduled_start)

            actual_task_start = datetime.datetime.now()
            task_duration = run_task(args.task_cmd)
            suspend_start = datetime.datetime.now()

            # Delay before suspending
            if args.active_delay > 0:
                logging.info(f"Waiting {args.active_delay:.2f}s before suspend")
                time.sleep(args.active_delay)

            # Compute suspend duration to wake just before next task
            next_scheduled_start = scheduled_start + datetime.timedelta(seconds=args.period)
            secs_until_wakeup = (next_scheduled_start
                                 - datetime.timedelta(seconds=args.pre_wakeup_delay)
                                 - datetime.datetime.now()).total_seconds()
            requested_suspend = max(1, int(secs_until_wakeup))

            logging.info(f"Suspending for {requested_suspend}s (mode={args.mode})")
            actual_suspend = rtc_sleep(args.mode, requested_suspend)
            resume_time = datetime.datetime.now()

            # Wait until next scheduled start if resumed early
            wait_until(next_scheduled_start)
            next_actual_start = datetime.datetime.now()

            row = {
                "iter": i,
                "scheduled_start": scheduled_start.isoformat(),
                "actual_task_start": actual_task_start.isoformat(),
                "task_duration_s": f"{task_duration:.3f}",
                "suspend_start": suspend_start.isoformat(),
                "requested_suspend_s": requested_suspend,
                "actual_suspend_s": f"{actual_suspend:.3f}",
                "resume_time": resume_time.isoformat(),
                "next_scheduled_start": next_scheduled_start.isoformat(),
                "next_actual_start": next_actual_start.isoformat()
            }
            writer.writerow(row)
            f.flush()
            logging.info(f"Logged iteration {i}")

    logging.info("Benchmark completed.")


if __name__ == "__main__":
    main()