# m1_ingest/normalizer.py
# Color space normalization for M1
# See agents.md §MODULE_CONTRACTS → M1 step 9
#
# Responsibilities:
#   - Normalize all loaded page images to consistent BGR color space
#   - Ensure uniform np.ndarray dtype across all pages
