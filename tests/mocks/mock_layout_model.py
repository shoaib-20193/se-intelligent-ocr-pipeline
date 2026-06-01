# tests/mocks/mock_layout_model.py
# Deterministic mock layout model — replaces LayoutLMv3/Detectron2 in tests
# See agents.md §MODULE_CONTRACTS → M9 Test Suite: "Mocked inference tests"
#
# Behaviour:
#   Returns fixed list of Region objects with confidence = 0.9
#   Region types cycle: header, paragraph, table
#   Bounding boxes are non-overlapping grid positions
