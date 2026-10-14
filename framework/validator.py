from pathlib import Path


def require_result_folder(result_folder: Path) -> Path:
	if not result_folder.is_dir():
		raise AssertionError(f"Expected Agile result folder was not found: {result_folder}")
	return result_folder
