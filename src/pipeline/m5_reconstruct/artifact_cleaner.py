# m5_reconstruct/artifact_cleaner.py
# Text artifact cleanup for M5 — implements §ALGO-ARTIFACT
# See agents.md §CORE_ALGORITHMS → §ALGO-ARTIFACT
#
# Rules (applied in order):
#   1. Remove regions where text.strip() == ""
#   2. Remove regions where len(text.strip()) < MIN_TEXT_LENGTH (=2)
#   3. Replace r"\s{2,}" with " " (multiple spaces -> single)
#   4. Strip leading/trailing whitespace from text
#   5. Remove chars where ord(char) < 32 EXCEPT \n (0x0A) and \t (0x09)
