from __future__ import annotations

import subprocess
from pathlib import Path


class CommandRunner:
	def __init__(self, executable: Path, working_directory: Path, timeout_seconds: int):
		self.executable = executable
		self.working_directory = working_directory
		self.timeout_seconds = timeout_seconds

	def run(self, commands: list[str]) -> subprocess.CompletedProcess[str]:
		if not self.executable.is_file():
			raise FileNotFoundError(f"Agile executable was not found: {self.executable}")

		input_text = "\n".join(commands) + "\n"
		result = subprocess.run(
			[str(self.executable)],
			input=input_text,
			text=True,
			cwd=self.working_directory,
			timeout=self.timeout_seconds,
		)

		if result.returncode != 0:
			raise RuntimeError(f"Agile console failed with exit code {result.returncode}")

		return result

	def run_captured(self, commands: list[str]) -> str:
		"""Run the console in a Windows pseudo-terminal and capture its display output."""
		try:
			from winpty import PtyProcess
		except ImportError as exc:
			raise RuntimeError(
				"Install pywinpty with '.venv\\Scripts\\python -m pip install pywinpty'"
			) from exc

		command = f'cmd.exe /c ""{self.executable}""'
		process = PtyProcess.spawn(command, cwd=str(self.working_directory))
		process.write("\n".join(commands) + "\n")
		output = []
		while process.isalive():
			try:
				output.append(process.read())
			except EOFError:
				break
		return "".join(output)
