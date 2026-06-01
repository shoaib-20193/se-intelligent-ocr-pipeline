# src/evaluation/wer_calculator.py
# Word Error Rate computation for M9 — implements §ALGO-WER
# See agents.md §CORE_ALGORITHMS → §ALGO-WER
#
# Formula:
#   WER = (S + D + I) / N
#   S = substitutions, D = deletions, I = insertions, N = ground-truth word count
#
# Method: Levenshtein distance at word level (space-tokenized)
# WER range: [0.0, inf); lower is better
# Target: WER <= 0.15 (TODO: confirm after baseline testing)
