from pathlib import Path
import os
import sys
import time

import yaml

from framework.agile_client import AgileClient
from framework.command_runner import CommandRunner
from framework.downloader import write_status_report
from framework.job_manager import job_failure_reason, parse_job_statuses
from framework.job_naming import build_job_name


PROJECT_ROOT = Path(__file__).resolve().parent
config = yaml.safe_load((PROJECT_ROOT / "config" / "config.yaml").read_text())
agile_config = config["agile"]
job_command = os.getenv("AGILE_JOB_COMMAND", agile_config["command"])


def stop_requested() -> bool:
    if os.name != "nt" or not sys.stdin.isatty():
        return False
    import msvcrt
    while msvcrt.kbhit():
        if msvcrt.getwch().lower() == "x":
            return True
    return False
if os.getenv("AGILE_SKIP_SUBMIT") == "1":
    job_name = os.getenv("AGILE_JOB_NAME", agile_config["job_name"])
else:
    job_name = build_job_name(agile_config["job_name"], agile_config["spec_path"])

client = AgileClient(
    CommandRunner(
        executable=Path(agile_config["executable"]),
        working_directory=Path(agile_config["working_directory"]),
        timeout_seconds=agile_config["command_timeout_seconds"],
    )
)

if os.getenv("AGILE_SKIP_SUBMIT") != "1":
    client.submit_job(job_command, agile_config["spec_path"], job_name)
    print(f"Submitted {job_command} job: {job_name}")
else:
    print(f"Polling existing Agile job: {job_name}")

deadline = time.monotonic() + agile_config["command_timeout_seconds"]
statuses = []
last_status_output = ""
poll_number = 0
while time.monotonic() < deadline:
    if stop_requested():
        print("Stop requested. Exiting status polling.", flush=True)
        raise SystemExit(0)
    poll_number += 1
    elapsed_seconds = agile_config["command_timeout_seconds"] - max(
        0, int(deadline - time.monotonic())
    )
    print(
        f"[Poll {poll_number}] Checking Agile status for '{job_name}' "
        f"after {elapsed_seconds}s...",
        flush=True,
    )
    status_output = client.check_status_captured()
    last_status_output = status_output
    statuses = parse_job_statuses(status_output, job_name)
    if statuses:
        print(
            " | ".join(f"{job.name}: {job.status}" for job in statuses),
            flush=True,
        )
    else:
        print(
            f"[Poll {poll_number}] No matching jobs found yet; continuing to poll.",
            flush=True,
        )
    if statuses and all(job.is_complete or job.is_failed for job in statuses):
        print(f"[Poll {poll_number}] All jobs reached a terminal state.", flush=True)
        break
    print(
        f"[Poll {poll_number}] Waiting {agile_config['status_poll_seconds']}s "
        "before the next status check. Press x then Enter to stop polling.",
        flush=True,
    )
    for _ in range(agile_config["status_poll_seconds"]):
        if stop_requested():
            print("Stop requested. Exiting status polling.", flush=True)
            raise SystemExit(0)
        time.sleep(1)
    else:
        continue
    break
else:
    report_path = write_status_report(
        PROJECT_ROOT / config["results"]["root"],
        agile_config["spec_path"],
        statuses,
    )
    raise TimeoutError(
        f"Agile jobs did not finish before timeout: {job_name}. "
        f"Last status rows: {len(statuses)}. Report: {report_path}"
    )

report_path = write_status_report(
    PROJECT_ROOT / config["results"]["root"],
    agile_config["spec_path"],
    statuses,
)
failure_reason = job_failure_reason(statuses)
if failure_reason:
    raise RuntimeError(f"Agile model failed: {failure_reason}. Report: {report_path}")

print(f"All Agile jobs completed. Report: {report_path}")
print(f"Expected output location: {config['results']['s3_prefix']}")
