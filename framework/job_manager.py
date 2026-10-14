from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class JobStatus:
	name: str
	status: str
	job_id: str

	@property
	def is_complete(self) -> bool:
		return "complete" in self.status.lower()

	@property
	def is_failed(self) -> bool:
		return "failed" in self.status.lower() or "error" in self.status.lower()


def parse_job_statuses(console_output: str, job_prefix: str) -> list[JobStatus]:
	clean_output = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", console_output)
	row_pattern = re.compile(
		r"\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|"
		r"\s*([^|]+)\s*\|\s*([^|]+)\s*\|",
		re.DOTALL,
	)
	job_id_pattern = re.compile(
		r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
		re.IGNORECASE,
	)
	statuses = []
	for match in row_pattern.finditer(clean_output):
		job_id, name, _created_on, status, _client = (
			field.strip().replace("\r", " ").replace("\n", " ")
			for field in match.groups()
		)
		if job_id_pattern.fullmatch(job_id) and job_prefix.lower() in name.lower():
			statuses.append(JobStatus(name, status, job_id))
	return statuses


def job_failure_reason(statuses: list[JobStatus]) -> str:
	failed = [f"{job.name}: {job.status}" for job in statuses if job.is_failed]
	return "; ".join(failed) or ""
