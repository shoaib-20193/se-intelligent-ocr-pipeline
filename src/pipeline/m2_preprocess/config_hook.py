# m2_preprocess/config_hook.py
# Reads M2-relevant fields from ProfileConfig
# See agents.md §MODULE_CONTRACTS → M2, §CONFIGURATION_SCHEMA
#
# Consumed fields:
#   profile.denoise                -> bool
#   profile.deskew                 -> bool
#   profile.thresholding           -> bool
#   profile.resize_scale           -> float
#   profile.perspective_correction -> bool
