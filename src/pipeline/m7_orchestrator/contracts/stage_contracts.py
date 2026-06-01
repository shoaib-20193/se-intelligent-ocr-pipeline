"""
src/pipeline/m7_orchestrator/contracts/stage_contracts.py
Validates input/output DTO type correctness for each stage.
Rejects invalid outputs immediately to prevent silent pipeline corruption.
"""
import logging
from typing import Any
from src.pipeline.m7_orchestrator.errors.pipeline_exceptions import ContractViolationError
from src.data_model.document import Document
from src.data_model.preprocessed import PreprocessedDocument
from src.data_model.layout import LayoutDocument
from src.data_model.ocr import RecognizedDocument
from src.pipeline.m5_semantic.contracts import StructuredDocument

logger = logging.getLogger(__name__)


class StageIOValidator:
    """
    Enforces strict DTO type contracts at every stage boundary.
    Prevents malformed or None outputs from propagating downstream.
    """

    @staticmethod
    def validate_m1_output(dto: Any) -> Document:
        if dto is None:
            raise ContractViolationError("M1 Output Contract Violation: output is None")
        if not isinstance(dto, Document):
            raise ContractViolationError(
                f"M1 Output Contract Violation: Expected Document, got {type(dto).__name__}"
            )
        logger.debug("[M7_CONTRACT] M1 output validated: Document OK")
        return dto

    @staticmethod
    def validate_m2_output(dto: Any) -> PreprocessedDocument:
        if dto is None:
            raise ContractViolationError("M2 Output Contract Violation: output is None")
        if not isinstance(dto, PreprocessedDocument):
            raise ContractViolationError(
                f"M2 Output Contract Violation: Expected PreprocessedDocument, got {type(dto).__name__}"
            )
        logger.debug("[M7_CONTRACT] M2 output validated: PreprocessedDocument OK")
        return dto

    @staticmethod
    def validate_m3_output(dto: Any) -> LayoutDocument:
        if dto is None:
            raise ContractViolationError("M3 Output Contract Violation: output is None")
        if not isinstance(dto, LayoutDocument):
            raise ContractViolationError(
                f"M3 Output Contract Violation: Expected LayoutDocument, got {type(dto).__name__}"
            )
        logger.debug("[M7_CONTRACT] M3 output validated: LayoutDocument OK")
        return dto

    @staticmethod
    def validate_m4_output(dto: Any) -> RecognizedDocument:
        if dto is None:
            raise ContractViolationError("M4 Output Contract Violation: output is None")
        if not isinstance(dto, RecognizedDocument):
            raise ContractViolationError(
                f"M4 Output Contract Violation: Expected RecognizedDocument, got {type(dto).__name__}"
            )
        logger.debug("[M7_CONTRACT] M4 output validated: RecognizedDocument OK")
        return dto

    @staticmethod
    def validate_m5_output(dto: Any) -> StructuredDocument:
        if dto is None:
            raise ContractViolationError("M5 Output Contract Violation: output is None")
        if not isinstance(dto, StructuredDocument):
            raise ContractViolationError(
                f"M5 Output Contract Violation: Expected StructuredDocument, got {type(dto).__name__}"
            )
        # Check basic integrity according to the prompt
        if not hasattr(dto, "pages"):
             raise ContractViolationError("M5 Output Contract Violation: StructuredDocument missing 'pages'")
        logger.debug("[M7_CONTRACT] M5 output validated: StructuredDocument OK")
        return dto
