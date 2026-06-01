# tests/conftest.py
# Shared fixtures, mocks, and test configuration
# See agents.md §MODULE_CONTRACTS → M9 Test Suite Requirements
#
# Provides:
#   - sample_processing_request fixture
#   - sample_document fixture (valid Document object)
#   - sample_layout_document fixture
#   - sample_recognized_document fixture
#   - sample_structured_document fixture
#   - mock_ocr_engine fixture (deterministic — no real inference)
#   - mock_layout_model fixture
#   - fast_draft_profile fixture
#   - high_accuracy_profile fixture
#   - temp_output_dir fixture (writable temp directory)

import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--input", 
        action="store", 
        default=None, 
        help="Path to input file or directory for batch layout testing"
    )
