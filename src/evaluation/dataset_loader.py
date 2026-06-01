# src/evaluation/dataset_loader.py
# Ground-truth dataset loader for M9
# See agents.md §EVALUATION_SYSTEM → Supported Ground-Truth Datasets
#
# Supported datasets:
#   - FUNSD  (Form Understanding in Noisy Scanned Documents)
#   - SROIE  (Scanned Receipts OCR and Information Extraction)
#   - Custom user-provided ground-truth (format: TODO — define schema)
#
# Public function:
#   load_ground_truth(path: str, dataset_type: str) -> GroundTruthDocument
