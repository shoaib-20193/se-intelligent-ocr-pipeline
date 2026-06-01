# src/utils/file_utils.py
# File system helpers — shared across M1, M6
# See agents.md §MODULE_CONTRACTS → M1, M6, §ERROR_HANDLING_RULES
#
# Functions:
#   validate_path_readable(path: str) -> bool
#   validate_path_writable(path: str) -> bool
#   get_file_size_mb(path: str) -> float
#   atomic_rename(src: str, dst: str) -> None  # temp -> target rename
#   list_files_recursive(directory: str, extensions: set[str]) -> list[str]
