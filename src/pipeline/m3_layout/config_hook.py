# m3_layout/config_hook.py
# Reads M3-relevant fields from ProfileConfig
# See agents.md §CONFIGURATION_SCHEMA
#
# Consumed fields:
#   profile.confidence_threshold -> float  (layout hard-discard threshold)
#   layout.model                 -> str    ("LayoutLMv3" | "Detectron2")
