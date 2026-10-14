from __future__ import annotations

from pathlib import Path

from framework.command_runner import CommandRunner


class AgileClient:
	def __init__(self, runner: CommandRunner):
		self.runner = runner

	def submit_matchback(self, spec_path: Path, job_name: str) -> str:
		result = self.runner.run([
			f"submit-matchback {spec_path}",
			job_name,
			"quit",
			"y",
		])
		return result.stdout

	def submit_agile(self, spec_path: str, job_name: str) -> str:
		return self.submit_job("submit-agile", spec_path, job_name)

	def submit_job(self, command: str, spec_path: str, job_name: str) -> str:
		result = self.runner.run([
			f"{command} {spec_path}",
			job_name,
			"quit",
			"y",
		])
		return result.stdout

	def check_status(self) -> str:
		result = self.runner.run(["check-status", "x", "y", "quit", "y"])
		return result.stdout or ""

	def check_status_captured(self) -> str:
		return self.runner.run_captured(["check-status", "x", "y", "quit", "y"])
