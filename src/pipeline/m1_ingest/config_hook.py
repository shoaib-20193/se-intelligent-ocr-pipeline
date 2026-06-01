# m1_ingest/config_hook.py
# Reads M1-relevant fields from ProcessingRequest.constraints
# See agents.md §MODULE_CONTRACTS → M1
#
# Consumed fields:
#   constraints.max_pages        -> int
#   constraints.max_file_size_mb -> int
