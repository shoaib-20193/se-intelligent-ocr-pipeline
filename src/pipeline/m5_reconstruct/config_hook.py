# m5_reconstruct/config_hook.py
# Reads M5-relevant fields from PostProcessConfig
# See agents.md §DATA_MODEL → PostProcessConfig
#
# Consumed fields:
#   config.confidence_threshold -> float  (discard threshold, default: 0.5)
#   config.grammar_correction   -> bool
#   config.merge_paragraphs     -> bool
