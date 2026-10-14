from __future__ import annotations

import os
import time
from pathlib import Path

import pytest
import yaml

from framework.agile_client import AgileClient
from framework.command_runner import CommandRunner
from framework.validator import require_result_folder
from framework.job_naming import build_job_name


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG = yaml.safe_load((PROJECT_ROOT / "config" / "config.yaml").read_text())


@pytest.mark.skipif(
	not all(
		os.getenv(variable)
		for variable in ("AGILE_SPEC_PATH", "AGILE_RESULT_FOLDER")
	),
	reason=(
		"Set AGILE_SPEC_PATH and AGILE_RESULT_FOLDER "
		"to run the live Agile test"
	),
)
def test_submit_matchback_and_validate_result():
	agile_config = CONFIG["agile"]
	client = AgileClient(
		CommandRunner(
			executable=Path(agile_config["executable"]),
			working_directory=Path(agile_config["working_directory"]),
			timeout_seconds=agile_config["command_timeout_seconds"],
		)
	)

	spec_path = Path(os.environ["AGILE_SPEC_PATH"])
	job_name = build_job_name(agile_config["job_name"], str(spec_path))
	client.submit_matchback(spec_path, job_name)

	deadline = time.monotonic() + agile_config["command_timeout_seconds"]
	while time.monotonic() < deadline:
		status_output = client.check_status().lower()
		if job_name.lower() in status_output and any(
			complete in status_output for complete in ("complete", "completed")
		):
			break
		if job_name.lower() in status_output and any(
			failure in status_output for failure in ("failed", "error")
		):
			pytest.fail(f"Agile job failed:\n{status_output}")
		time.sleep(agile_config["status_poll_seconds"])
	else:
		pytest.fail(f"Agile job did not complete before timeout: {job_name}")

	result_folder = Path(os.environ["AGILE_RESULT_FOLDER"])
	require_result_folder(result_folder)
