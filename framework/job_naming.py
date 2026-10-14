from __future__ import annotations

import re
from datetime import datetime
from pathlib import PurePosixPath
from secrets import token_hex


def client_name_from_spec(spec_path: str) -> str:
	parts = PurePosixPath(spec_path.replace("\\", "/")).parts
	for index, part in enumerate(parts[:-1]):
		if part.lower() == "client":
			return re.sub(r"[^A-Za-z0-9_-]", "-", parts[index + 1])
	return "client"


def build_job_name(base_name: str, spec_path: str) -> str:
	client_name = client_name_from_spec(spec_path)
	timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
	unique_suffix = token_hex(3)
	return f"{base_name}-{client_name}-{timestamp}-{unique_suffix}"