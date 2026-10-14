from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from framework.job_manager import JobStatus


def write_status_report(report_folder: Path, spec_path: str, statuses: list[JobStatus]) -> Path:
	report_folder.mkdir(parents=True, exist_ok=True)
	report_path = report_folder / "agile_status.json"
	report_path.write_text(
		json.dumps(
			{
				"spec_path": spec_path,
				"checked_at": datetime.now(timezone.utc).isoformat(),
				"jobs": [job.__dict__ for job in statuses],
				"result": "failed" if any(job.is_failed for job in statuses) else "passed",
			},
			indent=2,
		),
		encoding="utf-8",
	)
	return report_path
