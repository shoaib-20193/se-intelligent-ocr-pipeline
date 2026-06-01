# gui/tabs/benchmarking_tab.py
# Tab 3 — Benchmarking / Evaluation
# See agents.md §MODULE_CONTRACTS → M8 Tab 3, §UI_TO_SYSTEM_MAPPING
#
# Elements:
#   - Dataset selector: FUNSD | SROIE | custom path
#   - Metrics display: Precision, Recall, F1, WER, latency/page, RAM
#   - Confusion matrix heatmap (TODO: implement)
#   - Error Examples panel (False Positives from evaluation)
#   - Evaluation log console (per-region IoU, Levenshtein distances)
#
# Maps to: M9 exclusively
# Constraint: zero processing logic — delegates to evaluation interface
