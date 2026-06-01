# m6_export/config_hook.py
# Reads M6-relevant fields from ExportConfig
# See agents.md §DATA_MODEL → ExportConfig
#
# Consumed fields:
#   config.formats          -> list[str]  (subset of SUPPORTED_FORMATS)
#   config.output_directory -> str        (must be writable before export)
