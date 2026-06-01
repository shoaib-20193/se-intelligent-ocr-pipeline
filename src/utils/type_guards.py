# src/utils/type_guards.py
# Runtime type assertion helpers — validate data structures at module boundaries
# See agents.md §DATA_MODEL — enforces no implicit fields
#
# Functions:
#   assert_document(obj) -> None          # raises TypeError if not valid Document
#   assert_layout_document(obj) -> None
#   assert_recognized_document(obj) -> None
#   assert_structured_document(obj) -> None
#   assert_profile_config(obj) -> None
